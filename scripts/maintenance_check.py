#!/usr/bin/env python3
"""Determine whether a skill maintenance review is due and prepare the next state."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"date ISO 8601 invalide: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"état JSON invalide à la ligne {exc.lineno}: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ValueError("l'état doit être un objet JSON")
    return value


def check(state: dict[str, Any], interval_days: int, now: datetime) -> dict[str, Any]:
    if interval_days < 1:
        raise ValueError("interval-days doit être supérieur à zéro")
    last_raw = state.get("last_reviewed_at")
    if not isinstance(last_raw, str) or not last_raw:
        return {
            "due": True,
            "reason": "never-reviewed",
            "last_reviewed_at": None,
            "next_due_at": iso_time(now),
            "days_overdue": 0,
        }
    last = parse_time(last_raw)
    next_due = last + timedelta(days=interval_days)
    due = now >= next_due
    overdue = max(0, (now - next_due).days) if due else 0
    return {
        "due": due,
        "reason": "interval-elapsed" if due else "up-to-date",
        "last_reviewed_at": iso_time(last),
        "next_due_at": iso_time(next_due),
        "days_overdue": overdue,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Contrôler l'échéance de maintenance d'un skill")
    parser.add_argument("state", type=Path)
    parser.add_argument("--interval-days", type=int, default=30)
    parser.add_argument("--now")
    parser.add_argument("--record-state", type=Path)
    parser.add_argument("--skill-name")
    parser.add_argument("--version")
    parser.add_argument("--score", type=float)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        state = load_state(args.state)
        now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
        report = check(state, args.interval_days, now)
        report["skill_name"] = state.get("skill_name") or args.skill_name
        report["version"] = state.get("version") or args.version
        report["last_score"] = state.get("last_score")
        if args.score is not None and not 0 <= args.score <= 100:
            raise ValueError("score doit rester entre 0 et 100")
        if args.record_state:
            next_state = {
                "skill_name": args.skill_name or state.get("skill_name"),
                "version": args.version or state.get("version"),
                "last_reviewed_at": iso_time(now),
                "last_score": args.score if args.score is not None else state.get("last_score"),
            }
            args.record_state.parent.mkdir(parents=True, exist_ok=True)
            args.record_state.write_text(json.dumps(next_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            report["recorded_state"] = str(args.record_state)
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
