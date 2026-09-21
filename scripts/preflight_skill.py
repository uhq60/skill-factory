#!/usr/bin/env python3
"""Run complementary static checks on a skill directory.

This script supplements the platform's official validator; it does not replace it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
FORBIDDEN_FILES = {
    "README.md",
    "INSTALLATION_GUIDE.md",
    "QUICK_REFERENCE.md",
    "CHANGELOG.md",
}


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md doit commencer par un frontmatter YAML")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration as exc:
        raise ValueError("frontmatter YAML non fermé") from exc

    data: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.startswith((" ", "\t")):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if not match:
            raise ValueError(f"ligne de frontmatter non reconnue: {line}")
        data[match.group(1)] = match.group(2).strip().strip("'\"")
    return data, "\n".join(lines[end + 1 :])


def inspect_skill(root: Path) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    skill_md = root / "SKILL.md"

    if not root.is_dir():
        return {"path": str(root), "errors": ["répertoire du skill introuvable"], "warnings": []}
    if not skill_md.is_file():
        return {"path": str(root), "errors": ["SKILL.md introuvable"], "warnings": []}

    text = skill_md.read_text(encoding="utf-8")
    try:
        metadata, body = parse_frontmatter(text)
    except ValueError as exc:
        return {"path": str(root), "errors": [str(exc)], "warnings": []}

    extra_keys = sorted(set(metadata) - {"name", "description"})
    missing_keys = sorted({"name", "description"} - set(metadata))
    if missing_keys:
        errors.append("clés de frontmatter manquantes: " + ", ".join(missing_keys))
    if extra_keys:
        errors.append("clés de frontmatter interdites: " + ", ".join(extra_keys))

    name = metadata.get("name", "")
    description = metadata.get("description", "")
    if name and (len(name) > 63 or not NAME_RE.fullmatch(name)):
        errors.append("name doit contenir moins de 64 caractères en minuscules, chiffres et tirets")
    if description and len(description) < 50:
        warnings.append("description courte: préciser la fonction et les contextes de déclenchement")
    if description and not re.search(r"\b(use when|use for|utiliser|lorsque|déclench)\b", description, re.I):
        warnings.append("description sans formulation explicite des contextes de déclenchement")

    if re.search(r"\b(TODO|TBD|FIXME)\b", text, re.I):
        errors.append("marqueur TODO/TBD/FIXME restant")
    body_lines = body.splitlines()
    if len(body_lines) > 500:
        errors.append(f"corps de SKILL.md trop long: {len(body_lines)} lignes")
    if len([line for line in body_lines if line.strip()]) < 8:
        warnings.append("corps de SKILL.md très court")

    for path in root.rglob("*"):
        if path.is_file() and path.name in FORBIDDEN_FILES:
            errors.append(f"fichier auxiliaire interdit: {path.relative_to(root)}")

    for raw_target in LINK_RE.findall(text):
        target = raw_target.strip().split()[0].strip("<>")
        if target.startswith(("http://", "https://", "mailto:", "#", "skill://", "sandbox:")):
            continue
        target = target.split("#", 1)[0]
        if target and not (root / target).exists():
            errors.append(f"lien local introuvable depuis SKILL.md: {target}")

    agent_yaml = root / "agents" / "openai.yaml"
    if not agent_yaml.is_file():
        warnings.append("agents/openai.yaml absent")
    else:
        agent_text = agent_yaml.read_text(encoding="utf-8")
        if name and f"${name}" not in agent_text:
            warnings.append("default_prompt ne mentionne pas explicitement le skill")

    for dirname in ("scripts", "references", "assets"):
        directory = root / dirname
        if directory.is_dir() and not any(p.is_file() for p in directory.rglob("*")):
            warnings.append(f"répertoire de ressources vide: {dirname}/")

    return {
        "path": str(root),
        "name": name,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "status": "pass" if not errors else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Contrôles complémentaires d'un skill")
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    result = inspect_skill(args.skill_dir.resolve())
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Skill: {result.get('name') or '(inconnu)'}")
        print(f"Statut: {result.get('status', 'fail')}")
        for error in result["errors"]:
            print(f"ERREUR: {error}")
        for warning in result["warnings"]:
            print(f"AVERTISSEMENT: {warning}")
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
