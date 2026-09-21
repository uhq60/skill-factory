#!/usr/bin/env python3
"""Aggregate multi-task skill performance into reproducible metrics."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_payload(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"fichier introuvable: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON invalide à la ligne {exc.lineno}: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ValueError("la racine JSON doit être un objet")
    return value


def number(run: dict[str, Any], key: str, minimum: float = 0) -> float:
    value = run.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < minimum:
        raise ValueError(f"{run.get('task_id', 'run')}: {key} doit être un nombre >= {minimum}")
    return float(value)


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, math.ceil(ratio * len(ordered)) - 1)
    return ordered[index]


def summarize(runs: list[dict[str, Any]]) -> dict[str, Any]:
    if not runs:
        return {"runs": 0, "passed": 0, "pass_rate": 0.0}
    passed = sum(1 for run in runs if run["passed"])
    critical = [run for run in runs if run.get("critical", False)]
    critical_passed = sum(1 for run in critical if run["passed"])
    latencies = [number(run, "latency_ms") for run in runs]
    tokens = [number(run, "tokens") for run in runs]
    attempts = [number(run, "attempts", 1) for run in runs]
    quality = [number(run, "quality_score") for run in runs]
    if any(value > 100 for value in quality):
        raise ValueError("quality_score doit rester entre 0 et 100")
    pass_rate = 100 * passed / len(runs)
    critical_rate = 100 * critical_passed / len(critical) if critical else 100.0
    quality_average = statistics.fmean(quality)
    first_try_rate = 100 * sum(1 for value in attempts if value == 1) / len(attempts)
    performance_score = round(
        0.45 * pass_rate
        + 0.25 * critical_rate
        + 0.20 * quality_average
        + 0.10 * first_try_rate
    )
    return {
        "runs": len(runs),
        "passed": passed,
        "pass_rate": round(pass_rate, 2),
        "critical_runs": len(critical),
        "critical_pass_rate": round(critical_rate, 2),
        "average_quality": round(quality_average, 2),
        "average_latency_ms": round(statistics.fmean(latencies), 2),
        "p95_latency_ms": round(percentile(latencies, 0.95), 2),
        "average_tokens": round(statistics.fmean(tokens), 2),
        "average_attempts": round(statistics.fmean(attempts), 2),
        "first_try_rate": round(first_try_rate, 2),
        "performance_score": performance_score,
    }


def benchmark(payload: dict[str, Any]) -> dict[str, Any]:
    skill_name = payload.get("skill_name")
    runs = payload.get("runs")
    if not isinstance(skill_name, str) or not skill_name.strip():
        raise ValueError("skill_name est requis")
    if not isinstance(runs, list) or len(runs) < 3:
        raise ValueError("au moins trois runs sont requis")
    normalized: list[dict[str, Any]] = []
    ids: set[str] = set()
    for index, run in enumerate(runs, start=1):
        if not isinstance(run, dict):
            raise ValueError(f"run {index} invalide")
        task_id = run.get("task_id")
        category = run.get("category")
        if not isinstance(task_id, str) or not task_id or task_id in ids:
            raise ValueError(f"run {index}: task_id absent ou dupliqué")
        if not isinstance(category, str) or not category:
            raise ValueError(f"{task_id}: category est requise")
        if not isinstance(run.get("passed"), bool):
            raise ValueError(f"{task_id}: passed doit être un booléen")
        if "critical" in run and not isinstance(run["critical"], bool):
            raise ValueError(f"{task_id}: critical doit être un booléen")
        number(run, "latency_ms")
        number(run, "tokens")
        number(run, "attempts", 1)
        number(run, "quality_score")
        ids.add(task_id)
        normalized.append(run)

    categories: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in normalized:
        categories[run["category"]].append(run)
    overall = summarize(normalized)
    representative = len(categories) >= 2
    if overall["critical_pass_rate"] < 100:
        status = "blocked"
    elif overall["pass_rate"] >= 90 and overall["average_quality"] >= 80 and representative:
        status = "ready"
    else:
        status = "needs-improvement"
    return {
        "schema_version": 1,
        "skill_name": skill_name,
        "status": status,
        "representative": representative,
        "overall": overall,
        "by_category": {name: summarize(items) for name, items in sorted(categories.items())},
        "failed_task_ids": [run["task_id"] for run in normalized if not run["passed"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Mesurer les performances multi-tâches d'un skill")
    parser.add_argument("results", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = benchmark(load_payload(args.results))
    except (OSError, ValueError) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 1
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["status"] != "blocked" else 1


if __name__ == "__main__":
    sys.exit(main())
