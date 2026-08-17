from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

DATASET_PATH = Path(__file__).resolve().parents[2] / "resource" / "research_data.sqlite"
DOCS_PATH = Path(__file__).resolve().parents[2] / "resource" / "knowledge"


def route_user_question(question: str) -> str:
    """Choose the most appropriate tool for a user question."""
    q = (question or "").lower()

    if any(keyword in q for keyword in [
        "architecture", "deployment", "playbook", "documentation", "doc", "what does the", "describe the",
        "where is", "how is", "what are the system responsibilities", "retrieval",
    ]):
        return "retrieval"

    if any(keyword in q for keyword in [
        "calculate", "percentage", "percent", "average", "median", "sum", "difference", "growth", "delta",
    ]):
        return "calculator"

    if any(keyword in q for keyword in [
        "revenue", "profit", "customers", "compare", "dataset", "year", "region", "quarter", "conversion",
        "metric", "sql", "analytics",
    ]):
        return "sql"

    return "retrieval"


def buggy_route_user_question(question: str) -> str:
    """Old bug: retrieval was chosen too early for revenue and average questions."""
    q = (question or "").lower()
    if any(keyword in q for keyword in ["average", "revenue", "profit", "metric"]):
        return "retrieval"
    if any(keyword in q for keyword in ["architecture", "deployment"]):
        return "retrieval"
    if any(keyword in q for keyword in ["calculate", "percentage", "percent"]):
        return "calculator"
    return "retrieval"


def ensure_business_dataset() -> Path:
    DOCS_PATH.mkdir(parents=True, exist_ok=True)
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DATASET_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS revenue_metrics (
                year INTEGER,
                quarter INTEGER,
                region TEXT,
                product TEXT,
                revenue REAL,
                cost REAL,
                profit REAL,
                customers INTEGER,
                conversion_rate REAL,
                channel TEXT
            )
            """
        )
        existing = conn.execute("SELECT COUNT(*) FROM revenue_metrics").fetchone()[0]
        if existing == 0:
            rows = [
                (2023, 1, "North", "Core Platform", 120000.0, 76000.0, 44000.0, 1800, 0.12, "Enterprise"),
                (2023, 2, "North", "Core Platform", 135000.0, 82000.0, 53000.0, 1950, 0.13, "Enterprise"),
                (2023, 3, "South", "Analytics Suite", 98000.0, 61000.0, 37000.0, 1600, 0.11, "Self-serve"),
                (2023, 4, "South", "Analytics Suite", 110000.0, 67000.0, 43000.0, 1700, 0.12, "Self-serve"),
                (2024, 1, "North", "Core Platform", 148000.0, 90000.0, 58000.0, 2100, 0.14, "Enterprise"),
                (2024, 2, "North", "Core Platform", 162000.0, 96000.0, 66000.0, 2250, 0.15, "Enterprise"),
                (2024, 3, "South", "Analytics Suite", 127000.0, 76000.0, 51000.0, 2050, 0.17, "Self-serve"),
                (2024, 4, "South", "Analytics Suite", 142000.0, 83000.0, 59000.0, 2200, 0.18, "Self-serve"),
                (2025, 1, "North", "Core Platform", 181000.0, 103000.0, 78000.0, 2550, 0.18, "Enterprise"),
                (2025, 2, "North", "Core Platform", 195000.0, 110000.0, 85000.0, 2680, 0.19, "Enterprise"),
                (2025, 3, "South", "Analytics Suite", 154000.0, 89000.0, 65000.0, 2380, 0.2, "Self-serve"),
                (2025, 4, "South", "Analytics Suite", 171000.0, 96000.0, 75000.0, 2500, 0.21, "Self-serve"),
            ]
            conn.executemany(
                "INSERT INTO revenue_metrics (year, quarter, region, product, revenue, cost, profit, customers, conversion_rate, channel) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
    finally:
        conn.close()
    return DATASET_PATH


def generate_safe_sql(question: str) -> str:
    q = question.lower()
    blocked = ["drop ", "delete ", "update ", "insert ", "alter ", "truncate ", "attach ", "vacuum", "pragma", ";--"]
    if any(token in q for token in blocked):
        raise ValueError("Destructive SQL is blocked.")

    if "average revenue" in q or "avg revenue" in q:
        return "SELECT year, ROUND(AVG(revenue), 2) AS avg_revenue FROM revenue_metrics GROUP BY year ORDER BY year;"
    if "total revenue" in q or "revenue total" in q or "compare" in q:
        return "SELECT year, ROUND(SUM(revenue), 2) AS total_revenue FROM revenue_metrics GROUP BY year ORDER BY year;"
    if "profit" in q:
        return "SELECT year, ROUND(AVG(profit), 2) AS avg_profit FROM revenue_metrics GROUP BY year ORDER BY year;"
    if "customers" in q:
        return "SELECT year, ROUND(AVG(customers), 2) AS avg_customers FROM revenue_metrics GROUP BY year ORDER BY year;"
    if "conversion" in q:
        return "SELECT region, ROUND(AVG(conversion_rate), 4) AS avg_conversion_rate FROM revenue_metrics GROUP BY region ORDER BY avg_conversion_rate DESC;"
    return "SELECT year, ROUND(AVG(revenue), 2) AS avg_revenue FROM revenue_metrics GROUP BY year ORDER BY year LIMIT 5;"


def execute_sql_query(question: str) -> dict[str, Any]:
    db_path = ensure_business_dataset()
    sql = generate_safe_sql(question)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql).fetchall()
    return {
        "query": sql,
        "rows": [dict(row) for row in rows],
        "row_count": len(rows),
    }


def retrieve_docs(query: str) -> dict[str, Any]:
    docs = []
    for path in sorted(DOCS_PATH.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        if any(term in content.lower() for term in [term for term in query.lower().split() if len(term) > 3]):
            docs.append({
                "source": path.name,
                "snippet": content[:300].replace("\n", " ").strip(),
            })
    if not docs:
        return {"error": "No matching documentation found.", "query": query, "documents": []}
    return {"query": query, "documents": docs}


def compute_percentage_change(start: float, end: float) -> float:
    if start == 0:
        raise ValueError("Percentage change cannot be computed from zero.")
    return round(((end - start) / abs(start)) * 100.0, 2)


def compute_average(values: list[float]) -> float:
    return round(sum(values) / max(len(values), 1), 2)


def summarize_question(question: str) -> dict[str, Any]:
    route = route_user_question(question)
    if route == "sql":
        result = execute_sql_query(question)
        return {"tool": "sql", "result": result}
    if route == "calculator":
        try:
            numbers = [float(token) for token in re.findall(r"-?\d+(?:\.\d+)?", question)]
            if len(numbers) >= 2:
                result = {"operation": "percent_change", "result": compute_percentage_change(numbers[-2], numbers[-1])}
            else:
                result = {"operation": "average", "result": compute_average(numbers or [0.0])}
        except Exception as exc:
            result = {"error": str(exc)}
        return {"tool": "calculator", "result": result}
    return {"tool": "retrieval", "result": retrieve_docs(question)}
