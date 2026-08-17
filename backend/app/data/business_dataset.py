from __future__ import annotations

import sqlite3
from pathlib import Path

DATASET_PATH = Path(__file__).resolve().parents[2] / "resource" / "research_data.sqlite"


def ensure_business_dataset(db_path: str | Path | None = None) -> Path:
    """Create a small safe SQLite dataset for analytical research queries."""
    target = Path(db_path) if db_path is not None else DATASET_PATH
    target.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(target)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS revenue_metrics (
                year INTEGER NOT NULL,
                quarter INTEGER NOT NULL,
                region TEXT NOT NULL,
                product TEXT NOT NULL,
                revenue REAL NOT NULL,
                cost REAL NOT NULL,
                profit REAL NOT NULL,
                customers INTEGER NOT NULL,
                conversion_rate REAL NOT NULL,
                channel TEXT NOT NULL
            )
            """
        )

        existing_count = conn.execute("SELECT COUNT(*) FROM revenue_metrics").fetchone()[0]
        if existing_count == 0:
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
                """
                INSERT INTO revenue_metrics (
                    year, quarter, region, product, revenue, cost, profit, customers, conversion_rate, channel
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            conn.commit()
    finally:
        conn.close()

    return target
