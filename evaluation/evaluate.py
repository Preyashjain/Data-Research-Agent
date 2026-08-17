from __future__ import annotations

import json
import time
from pathlib import Path
from statistics import mean

from backend.app.agent_logic import (
    compute_average,
    compute_percentage_change,
    ensure_business_dataset,
    execute_sql_query,
    retrieve_docs,
    route_user_question,
    summarize_question,
)


ROOT = Path(__file__).resolve().parents[1]
TEST_CASES_PATH = ROOT / "evaluation" / "test_cases.json"


def load_cases() -> list[dict]:
    with TEST_CASES_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def run_evaluation() -> dict:
    cases = load_cases()
    started = time.perf_counter()
    results = []
    for case in cases:
        t0 = time.perf_counter()
        route = route_user_question(case["question"])
        tool_ok = route == case["expected_tool"]
        try:
            response = summarize_question(case["question"])
            task_ok = bool(response.get("result") or response.get("tool"))
        except Exception:
            task_ok = False
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        results.append({
            "id": case["id"],
            "question": case["question"],
            "expected_tool": case["expected_tool"],
            "actual_tool": route,
            "tool_ok": tool_ok,
            "task_ok": task_ok,
            "latency_ms": latency_ms,
        })

    tool_selection_accuracy = round(sum(item["tool_ok"] for item in results) / len(results) * 100, 2)
    task_success_rate = round(sum(item["task_ok"] for item in results) / len(results) * 100, 2)
    avg_latency = round(mean(item["latency_ms"] for item in results), 2)
    sql_success = 0
    retrieval_success = 0
    for item in results:
        if item["actual_tool"] == "sql":
            try:
                execute_sql_query(item["question"])
                sql_success += 1
            except Exception:
                pass
        if item["actual_tool"] == "retrieval":
            try:
                retrieve_docs(item["question"])
                retrieval_success += 1
            except Exception:
                pass

    sql_success_rate = round(sql_success / max(sum(1 for item in results if item["actual_tool"] == "sql"), 1) * 100, 2)
    retrieval_success_rate = round(retrieval_success / max(sum(1 for item in results if item["actual_tool"] == "retrieval"), 1) * 100, 2)

    summary = {
        "total_cases": len(results),
        "tool_selection_accuracy": tool_selection_accuracy,
        "task_success_rate": task_success_rate,
        "sql_execution_success_rate": sql_success_rate,
        "retrieval_success_rate": retrieval_success_rate,
        "average_latency_ms": avg_latency,
        "elapsed_time_s": round(time.perf_counter() - started, 2),
        "results": results,
    }
    return summary


if __name__ == "__main__":
    ensure_business_dataset()
    output = run_evaluation()
    print(json.dumps(output, indent=2))
