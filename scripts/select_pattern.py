#!/usr/bin/env python3
"""Rank reusable skill architecture patterns against a structured brief."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any


DEFAULT_CATALOG = Path(__file__).resolve().parent.parent / "references" / "pattern-catalog.json"


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


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.lower())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value).strip()


def text_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def select_patterns(brief: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    summary = brief.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("summary est requis")
    corpus_parts = [summary]
    for key in ("desired_outputs", "tools", "constraints"):
        corpus_parts.extend(text_values(brief.get(key, [])))
    corpus = normalize(" ".join(corpus_parts))

    patterns = catalog.get("patterns")
    if not isinstance(patterns, list) or not patterns:
        raise ValueError("le catalogue ne contient aucun pattern")

    ranked: list[dict[str, Any]] = []
    fallback: dict[str, Any] | None = None
    for pattern in patterns:
        if not isinstance(pattern, dict) or not isinstance(pattern.get("id"), str):
            raise ValueError("pattern invalide dans le catalogue")
        signals = text_values(pattern.get("signals", []))
        matched = [signal for signal in signals if normalize(signal) in corpus]
        score = sum(2 if " " in signal else 1 for signal in matched)
        entry = {
            "id": pattern["id"],
            "title": pattern.get("title", pattern["id"]),
            "score": score,
            "matched_signals": matched,
            "resources": pattern.get("resources", []),
            "required_tests": pattern.get("required_tests", []),
            "risks": pattern.get("risks", []),
        }
        if pattern["id"] == "general-workflow":
            fallback = entry
        else:
            ranked.append(entry)

    ranked.sort(key=lambda item: (-item["score"], item["id"]))
    recommended = ranked[0] if ranked and ranked[0]["score"] > 0 else fallback
    if recommended is None:
        raise ValueError("le catalogue doit contenir general-workflow")
    return {
        "schema_version": 1,
        "recommended": recommended,
        "alternatives": [item for item in ranked if item["id"] != recommended["id"]][:2],
        "evidence": {
            "matched_signals": recommended["matched_signals"],
            "input_text_retained": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sélectionner un patron de skill")
    parser.add_argument("brief", type=Path)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        report = select_patterns(load_object(args.brief), load_object(args.catalog))
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
