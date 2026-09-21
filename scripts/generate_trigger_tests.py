#!/usr/bin/env python3
"""Generate a normalized skill test matrix from a specification JSON file."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CATEGORIES = (
    ("positive_prompts", "P", "trigger", "invoke", True),
    ("negative_prompts", "N", "non-trigger", "do_not_invoke", True),
    ("ambiguous_prompts", "A", "ambiguous", "ask_or_infer", False),
    ("missing_resource_prompts", "M", "missing-resource", "stop_and_request_resource", True),
    ("sensitive_prompts", "S", "safety", "request_confirmation", True),
)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"fichier introuvable: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON invalide à la ligne {exc.lineno}: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ValueError("la racine du fichier doit être un objet JSON")
    return value


def clean_prompts(spec: dict[str, Any], key: str) -> list[str]:
    raw = spec.get(key, [])
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ValueError(f"{key} doit être une liste de chaînes")
    prompts = [item.strip() for item in raw if item.strip()]
    if len(prompts) != len(set(prompts)):
        raise ValueError(f"{key} contient des doublons")
    return prompts


def generate_suite(spec: dict[str, Any]) -> dict[str, Any]:
    skill_name = spec.get("skill_name")
    if not isinstance(skill_name, str) or not NAME_RE.fullmatch(skill_name):
        raise ValueError("skill_name doit être un nom valide en minuscules et tirets")

    positive = clean_prompts(spec, "positive_prompts")
    negative = clean_prompts(spec, "negative_prompts")
    if len(positive) < 3:
        raise ValueError("au moins trois positive_prompts sont requis")
    if len(negative) < 3:
        raise ValueError("au moins trois negative_prompts sont requis")

    cases: list[dict[str, Any]] = []
    for source_key, prefix, category, expected_action, critical in CATEGORIES:
        for index, prompt in enumerate(clean_prompts(spec, source_key), start=1):
            cases.append(
                {
                    "id": f"{prefix}{index}",
                    "category": category,
                    "prompt": prompt,
                    "expected_action": expected_action,
                    "critical": critical,
                }
            )

    cases.append(
        {
            "id": "R1",
            "category": "regression",
            "prompt": positive[0],
            "expected_action": "preserve_previous_behavior",
            "critical": True,
            "source_case": "P1",
        }
    )
    return {
        "schema_version": 1,
        "skill_name": skill_name,
        "case_count": len(cases),
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Générer une matrice de tests de skill")
    parser.add_argument("specification", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        suite = generate_suite(load_json(args.specification))
    except ValueError as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(suite, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
