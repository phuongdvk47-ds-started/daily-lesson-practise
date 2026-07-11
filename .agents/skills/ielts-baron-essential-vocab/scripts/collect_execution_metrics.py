#!/usr/bin/env python3
"""Collect execution metrics — aggregate per-task metadata into cost report."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def collect_metrics(metrics_dir: Path) -> dict:
    """Aggregate all execution-metadata.json files into a cost report.

    Scans metrics_dir recursively for execution-metadata.json files.
    """
    report = {
        "local_tasks": 0,
        "local_model_tasks": 0,
        "low_cost_llm_tasks": 0,
        "premium_llm_tasks": 0,
        "human_review_tasks": 0,
        "cache_hits": 0,
        "avoided_model_calls": 0,
        "estimated_total_cost": 0.0,
        "premium_escalations": [],
        "tasks": [],
    }

    for meta_path in metrics_dir.rglob("execution-metadata.json"):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

        exec_class = meta.get("execution_class", "")
        if exec_class == "DETERMINISTIC":
            report["local_tasks"] += 1
        elif exec_class == "LOCAL_MODEL":
            report["local_model_tasks"] += 1
        elif exec_class == "LOW_COST_LLM":
            report["low_cost_llm_tasks"] += 1
        elif exec_class == "PREMIUM_LLM":
            report["premium_llm_tasks"] += 1
        elif exec_class == "HUMAN_REQUIRED":
            report["human_review_tasks"] += 1

        if meta.get("cache_hit", False):
            report["cache_hits"] += 1
            report["avoided_model_calls"] += 1

        report["estimated_total_cost"] += meta.get("estimated_cost", 0)

        if meta.get("escalated_from"):
            report["premium_escalations"].append({
                "task_id": meta.get("task_id"),
                "stage": meta.get("stage"),
                "escalated_from": meta.get("escalated_from"),
                "reason": meta.get("escalation_reason", ""),
            })

        report["tasks"].append({
            "task_id": meta.get("task_id"),
            "stage": meta.get("stage"),
            "execution_class": exec_class,
            "engine": meta.get("engine"),
            "cache_hit": meta.get("cache_hit", False),
            "estimated_cost": meta.get("estimated_cost", 0),
        })

    report["estimated_total_cost"] = round(report["estimated_total_cost"], 6)
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Collect execution metrics")
    parser.add_argument("--dir", required=True, help="Directory to scan for execution metadata")
    parser.add_argument("--output", required=True, help="Output cost report path")
    args = parser.parse_args()

    report = collect_metrics(Path(args.dir))
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2))
