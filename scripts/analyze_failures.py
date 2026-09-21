#!/usr/bin/env python3
"""Aggregate recurring skill failures without retaining raw prompts or messages."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"fichier introuvable: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON invalide à la ligne {exc.lineno}: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ValueError("la racine JSON doit être un objet")
    return value


def safe_code(run: dict[str, Any]) -> str:
    raw = run.get("error_code")
    if isinstance(raw, str) and raw.strip():
        code = re.sub(r"[^a-z0-9-]+", "-", raw.lower()).strip("-")
        return code[:80] or "unknown"
    message = run.get("error_message")
    if isinstance(message, str) and message:
        digest = hashlib.sha256(message.encode("utf-8")).hexdigest()[:12]
        return f"unclassified-{digest}"
    return "unclassified"


def analyze(payload: dict[str, Any], history: dict[str, Any] | None = None, now: str | None = None) -> dict[str, Any]:
    skill_name = payload.get("skill_name")
    runs = payload.get("runs")
    if not isinstance(skill_name, str) or not skill_name:
        raise ValueError("skill_name est requis")
    if not isinstance(runs, list):
        raise ValueError("runs doit être une liste")
    timestamp = now or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    totals: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "critical_count": 0, "categories": set(), "sample_task_ids": []}
    )
    if history:
        if history.get("skill_name") not in (None, skill_name):
            raise ValueError("l'historique appartient à un autre skill")
        for cluster in history.get("clusters", []):
            if not isinstance(cluster, dict) or not isinstance(cluster.get("code"), str):
                continue
            item = totals[cluster["code"]]
            item["count"] += int(cluster.get("count", 0))
            item["critical_count"] += int(cluster.get("critical_count", 0))
            item["categories"].update(str(value) for value in cluster.get("categories", []))
            item["sample_task_ids"].extend(str(value) for value in cluster.get("sample_task_ids", [])[:3])

    new_failures = 0
    for index, run in enumerate(runs, start=1):
        if not isinstance(run, dict):
            raise ValueError(f"run {index} invalide")
        if run.get("passed") is not False:
            continue
        new_failures += 1
        code = safe_code(run)
        item = totals[code]
        item["count"] += 1
        item["critical_count"] += int(run.get("critical") is True)
        item["categories"].add(str(run.get("category", "unknown")))
        task_id = run.get("task_id")
        if isinstance(task_id, str) and task_id and task_id not in item["sample_task_ids"]:
            item["sample_task_ids"].append(task_id)

    clusters: list[dict[str, Any]] = []
    for code, item in totals.items():
        if item["critical_count"]:
            priority = "P0"
        elif item["count"] >= 3:
            priority = "P1"
        else:
            priority = "P2"
        clusters.append(
            {
                "code": code,
                "count": item["count"],
                "critical_count": item["critical_count"],
                "recurring": item["count"] >= 2,
                "priority": priority,
                "categories": sorted(item["categories"]),
                "sample_task_ids": item["sample_task_ids"][:3],
            }
        )
    clusters.sort(key=lambda item: (item["priority"], -item["count"], item["code"]))
    return {
        "schema_version": 1,
        "skill_name": skill_name,
        "generated_at": timestamp,
        "new_failures": new_failures,
        "clusters": clusters,
        "recurring_codes": [item["code"] for item in clusters if item["recurring"]],
        "privacy": "Raw prompts and error messages are not retained.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Capitaliser les erreurs récurrentes d'un skill")
    parser.add_argument("results", type=Path)
    parser.add_argument("--history", type=Path)
    parser.add_argument("--now")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        history = load_object(args.history) if args.history else None
        report = analyze(load_object(args.results), history, args.now)
    except (OSError, ValueError) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 1
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
