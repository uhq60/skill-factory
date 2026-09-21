#!/usr/bin/env python3
"""Compare two skill versions by file inventory and audit score."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from audit_skill import audit_skill, load_test_results


def inventory(root: Path) -> dict[str, str]:
    if not root.is_dir():
        raise ValueError(f"répertoire introuvable: {root}")
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        result[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def compare(
    old_dir: Path,
    new_dir: Path,
    old_cases: list[dict[str, Any]] | None = None,
    new_cases: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    old_files = inventory(old_dir)
    new_files = inventory(new_dir)
    old_names = set(old_files)
    new_names = set(new_files)
    added = sorted(new_names - old_names)
    removed = sorted(old_names - new_names)
    modified = sorted(name for name in old_names & new_names if old_files[name] != new_files[name])
    unchanged = sorted(name for name in old_names & new_names if old_files[name] == new_files[name])

    old_audit = audit_skill(old_dir, old_cases or [], "not-run")
    new_audit = audit_skill(new_dir, new_cases or [], "not-run")
    return {
        "schema_version": 1,
        "old_skill": old_audit["skill"],
        "new_skill": new_audit["skill"],
        "added": added,
        "removed": removed,
        "modified": modified,
        "unchanged_count": len(unchanged),
        "old_score": old_audit["score"],
        "new_score": new_audit["score"],
        "score_delta": new_audit["score"] - old_audit["score"],
        "old_critical_failures": old_audit["critical_failures"],
        "new_critical_failures": new_audit["critical_failures"],
    }


def render_markdown(report: dict[str, Any]) -> str:
    def list_or_none(items: list[str]) -> str:
        return ", ".join(f"`{item}`" for item in items) if items else "Aucun"

    return "\n".join(
        [
            f"# Comparaison — {report['old_skill']} → {report['new_skill']}",
            "",
            f"- Score : **{report['old_score']} → {report['new_score']}** ({report['score_delta']:+d})",
            f"- Fichiers ajoutés : {list_or_none(report['added'])}",
            f"- Fichiers supprimés : {list_or_none(report['removed'])}",
            f"- Fichiers modifiés : {list_or_none(report['modified'])}",
            f"- Fichiers inchangés : {report['unchanged_count']}",
            "",
            "## Défaillances critiques de la candidate",
            "",
            list_or_none(report["new_critical_failures"]),
            "",
            "Le delta de score ne prouve pas l'absence de régression fonctionnelle; exécuter les cas de non-régression.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Comparer deux versions d'un skill")
    parser.add_argument("old_skill", type=Path)
    parser.add_argument("new_skill", type=Path)
    parser.add_argument("--old-tests", type=Path)
    parser.add_argument("--new-tests", type=Path)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        report = compare(
            args.old_skill.resolve(),
            args.new_skill.resolve(),
            load_test_results(args.old_tests),
            load_test_results(args.new_tests),
        )
    except (OSError, ValueError) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 1

    rendered = render_markdown(report) if args.format == "markdown" else json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
