from __future__ import annotations

import json
import math
import re
import sqlite3
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from ai.tools.oa_tools import search_handbook
from data.business_dataset import ensure_business_dataset

DOCS_DIR = Path(__file__).resolve().parents[2] / "resource" / "knowledge"


def _safe_sql(question: str) -> str:
    q = question.lower().strip()
    if not q:
        raise ValueError("Question is empty.")

    forbidden = [
        "drop ", "delete ", "update ", "insert ", "alter ", "truncate ", "attach ",
        "pragma", "vacuum", "grant ", "revoke ", "execute ", "replace ", "create ",
        "union select", "--", ";--",
    ]
    if any(token in q for token in forbidden):
        raise ValueError("Destructive or unsupported SQL is not allowed.")

    years = re.findall(r"(20\d{2})", question)
    years = sorted(set(years))
    year_filter = f"WHERE year IN ({', '.join(years)})" if years else ""

    if "average revenue" in q or "avg revenue" in q or "average sales" in q:
        if "region" in q or "by region" in q:
            return (
                f"SELECT region, ROUND(AVG(revenue), 2) AS avg_revenue "
                f"FROM revenue_metrics {year_filter} GROUP BY region ORDER BY avg_revenue DESC LIMIT 5"
            )
        if years:
            return (
                f"SELECT year, ROUND(AVG(revenue), 2) AS avg_revenue "
                f"FROM revenue_metrics {year_filter} GROUP BY year ORDER BY year"
            )
        return "SELECT year, ROUND(AVG(revenue), 2) AS avg_revenue FROM revenue_metrics GROUP BY year ORDER BY year"

    if "revenue" in q and ("compare" in q or "total revenue" in q or "summarize" in q):
        if years:
            return (
                f"SELECT year, ROUND(SUM(revenue), 2) AS total_revenue "
                f"FROM revenue_metrics {year_filter} GROUP BY year ORDER BY year"
            )
        return "SELECT year, ROUND(SUM(revenue), 2) AS total_revenue FROM revenue_metrics GROUP BY year ORDER BY year"

    if "region" in q and "conversion" in q:
        return "SELECT region, ROUND(AVG(conversion_rate), 4) AS avg_conversion_rate FROM revenue_metrics GROUP BY region ORDER BY avg_conversion_rate DESC LIMIT 5"

    if "top" in q and "region" in q:
        return "SELECT region, ROUND(SUM(revenue), 2) AS total_revenue FROM revenue_metrics GROUP BY region ORDER BY total_revenue DESC LIMIT 5"

    if "profit" in q:
        return "SELECT year, ROUND(AVG(profit), 2) AS avg_profit FROM revenue_metrics GROUP BY year ORDER BY year"

    if "customers" in q:
        return "SELECT year, ROUND(AVG(customers), 2) AS avg_customers FROM revenue_metrics GROUP BY year ORDER BY year"

    return "SELECT year, ROUND(AVG(revenue), 2) AS avg_revenue FROM revenue_metrics GROUP BY year ORDER BY year LIMIT 5"


@tool
async def retrieval_tool(query: str) -> dict[str, Any]:
    """Search the curated documentation for architecture, deployment, and research context."""
    results: list[dict[str, Any]] = []
    search_terms = [part.strip() for part in query.lower().split() if len(part.strip()) > 3]
    if not search_terms:
        search_terms = ["architecture", "deployment"]

    for path in sorted(DOCS_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        lower = content.lower()
        score = sum(1 for term in search_terms if term in lower)
        if score == 0:
            continue
        snippet = ""
        for term in search_terms:
            idx = lower.find(term)
            if idx != -1:
                start = max(0, idx - 120)
                end = min(len(content), idx + 220)
                snippet = content[start:end].replace("\n", " ").strip()
                break
        results.append({
            "source": path.name,
            "relevance": score,
            "snippet": snippet or content[:300].replace("\n", " ").strip(),
        })

    if not results:
        return {"error": "No matching documentation found.", "query": query, "documents": []}

    return {
        "query": query,
        "documents": sorted(results, key=lambda item: item["relevance"], reverse=True)[:5],
    }


@tool
async def sql_data_tool(question: str) -> dict[str, Any]:
    """Run a safe read-only SQL query against the business dataset."""
    try:
        sql = _safe_sql(question)
        db_path = ensure_business_dataset()
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql).fetchall()
        return {
            "query": sql,
            "rows": [dict(row) for row in rows],
            "row_count": len(rows),
        }
    except Exception as exc:  # pragma: no cover - defensive guard
        return {"error": str(exc), "query": question}


@tool
def calculator_tool(values: list[float] | None = None, operation: str = "average") -> dict[str, Any]:
    """Compute standard numeric analytics for clean data outputs."""
    if not values:
        return {"error": "No values were provided for analysis."}

    numbers = [float(value) for value in values]
    if operation == "average":
        return {"operation": operation, "result": round(sum(numbers) / len(numbers), 2)}
    if operation == "sum":
        return {"operation": operation, "result": round(sum(numbers), 2)}
    if operation == "percent_change":
        if len(numbers) != 2:
            return {"error": "percent_change requires exactly two values."}
        start, end = numbers
        if start == 0:
            return {"error": "Cannot compute percentage change from zero."}
        result = ((end - start) / abs(start)) * 100.0
        return {"operation": operation, "result": round(result, 2)}
    if operation == "difference":
        return {"operation": operation, "result": round(numbers[-1] - numbers[0], 2)}
    if operation == "median":
        sorted_values = sorted(numbers)
        mid = len(sorted_values) // 2
        if len(sorted_values) % 2 == 0:
            result = (sorted_values[mid - 1] + sorted_values[mid]) / 2
        else:
            result = sorted_values[mid]
        return {"operation": operation, "result": round(result, 2)}
    return {"error": f"Unsupported operation: {operation}"}


@tool
async def docs_rag_tool(query: str) -> dict[str, Any]:
    """Compatibility wrapper for older retrieval usage."""
    return await retrieval_tool(query)


__all__ = [
    "retrieval_tool",
    "sql_data_tool",
    "calculator_tool",
    "docs_rag_tool",
    "search_handbook",
]
