#!/usr/bin/env python3
"""Audit a skill, calculate a traceable score, and render a final report."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

from preflight_skill import LINK_RE, inspect_skill, parse_frontmatter


DIMENSION_MAX = {
    "trigger_precision": 15,
    "instruction_clarity": 15,
    "architecture": 15,
    "context_efficiency": 10,
    "script_reliability": 15,
    "error_handling": 10,
    "safety_confirmations": 10,
    "real_tests": 10,
}


def load_test_results(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"résultats de tests introuvables: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"résultats JSON invalides à la ligne {exc.lineno}: {exc.msg}") from exc
    cases = payload.get("cases") if isinstance(payload, dict) else None
    if not isinstance(cases, list):
        raise ValueError("test-results.json doit contenir une liste cases")
    normalized: list[dict[str, Any]] = []
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict) or not isinstance(case.get("passed"), bool):
            raise ValueError(f"cas {index}: passed doit être un booléen")
        normalized.append(case)
    return normalized


def keyword_hit(text: str, words: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, re.I | re.M) for pattern in words)


def category_passed(cases: list[dict[str, Any]], category: str) -> bool:
    selected = [case for case in cases if case.get("category") == category]
    return bool(selected) and all(case["passed"] for case in selected)


def python_syntax(skill_dir: Path) -> tuple[bool, list[str]]:
    failures: list[str] = []
    for script in sorted((skill_dir / "scripts").glob("*.py")) if (skill_dir / "scripts").is_dir() else []:
        try:
            ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
        except (SyntaxError, UnicodeDecodeError) as exc:
            failures.append(f"{script.name}: {exc}")
    return not failures, failures


def audit_skill(
    skill_dir: Path,
    cases: list[dict[str, Any]] | None = None,
    official_validation: str = "not-run",
) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    cases = cases or []
    preflight = inspect_skill(skill_dir)
    critical_failures: list[str] = []
    if preflight["errors"]:
        critical_failures.extend(f"Précontrôle: {item}" for item in preflight["errors"])
    if official_validation == "failed":
        critical_failures.append("Validation officielle en échec")

    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8") if skill_md.is_file() else ""
    try:
        metadata, body = parse_frontmatter(text)
    except ValueError:
        metadata, body = {}, ""
    description = metadata.get("description", "")
    body_lines = body.splitlines()
    files = [path for path in skill_dir.rglob("*") if path.is_file()]
    relative_files = {str(path.relative_to(skill_dir)) for path in files}

    local_links: set[str] = set()
    for raw_target in LINK_RE.findall(text):
        target = raw_target.strip().split()[0].strip("<>").split("#", 1)[0]
        if target and not target.startswith(("http://", "https://", "mailto:", "#", "skill://", "sandbox:")):
            local_links.add(target)
    reference_files = {item for item in relative_files if item.startswith("references/")}
    unlinked_references = sorted(reference_files - local_links)

    dimensions: dict[str, dict[str, Any]] = {}

    trigger_score = 0
    trigger_evidence: list[str] = []
    if metadata.get("name") and description:
        trigger_score += 4
        trigger_evidence.append("Métadonnées présentes")
    if keyword_hit(description, (r"\butiliser\b", r"\blorsque\b", r"\buse when\b", r"\buse for\b")):
        trigger_score += 4
        trigger_evidence.append("Contexte positif explicite")
    if keyword_hit(description, (r"\bne pas\b", r"\bexcept\b", r"\bdo not\b", r"\bexclude")):
        trigger_score += 3
        trigger_evidence.append("Exclusion explicite")
    if len(description) >= 100:
        trigger_score += 2
        trigger_evidence.append("Description suffisamment détaillée")
    if category_passed(cases, "trigger") and category_passed(cases, "non-trigger"):
        trigger_score += 2
        trigger_evidence.append("Tests positifs et négatifs réussis")
    dimensions["trigger_precision"] = {"score": trigger_score, "max": 15, "evidence": trigger_evidence}

    headings = len(re.findall(r"^#{2,4}\s+", body, re.M))
    numbered = len(re.findall(r"^\s*\d+\.\s+", body, re.M))
    clarity_score = min(4, headings) + min(4, numbered)
    clarity_evidence = [f"{headings} sections", f"{numbered} étapes numérotées"]
    if keyword_hit(body, (r"valid", r"test", r"contrôl", r"vérif")):
        clarity_score += 4
        clarity_evidence.append("Validation et tests explicités")
    if keyword_hit(body, (r"contrat de sortie", r"livrable", r"rapport final", r"output")):
        clarity_score += 3
        clarity_evidence.append("Sortie attendue explicitée")
    dimensions["instruction_clarity"] = {"score": min(15, clarity_score), "max": 15, "evidence": clarity_evidence}

    architecture_score = 0
    architecture_evidence: list[str] = []
    if not preflight["errors"]:
        architecture_score += 5
        architecture_evidence.append("Précontrôle sans erreur")
    if not any("lien local introuvable" in item for item in preflight["errors"]):
        architecture_score += 4
        architecture_evidence.append("Liens locaux résolus")
    top_entries = {path.relative_to(skill_dir).parts[0] for path in files}
    if top_entries <= {"SKILL.md", "agents", "scripts", "references", "assets"}:
        architecture_score += 3
        architecture_evidence.append("Arborescence essentielle uniquement")
    if not unlinked_references:
        architecture_score += 3
        architecture_evidence.append("Références directement découvrables")
    dimensions["architecture"] = {"score": architecture_score, "max": 15, "evidence": architecture_evidence}

    context_score = 0
    context_evidence: list[str] = []
    if len(body_lines) <= 200:
        context_score += 7
        context_evidence.append(f"SKILL.md concis: {len(body_lines)} lignes")
    elif len(body_lines) <= 500:
        context_score += 4
        context_evidence.append(f"SKILL.md sous 500 lignes: {len(body_lines)}")
    if not unlinked_references:
        context_score += 2
    long_reference_without_toc = False
    for relative in reference_files:
        content = (skill_dir / relative).read_text(encoding="utf-8")
        if len(content.splitlines()) > 100 and not re.search(r"^##\s+(Sommaire|Table of contents)", content, re.I | re.M):
            long_reference_without_toc = True
    if not long_reference_without_toc:
        context_score += 1
        context_evidence.append("Références longues structurées")
    dimensions["context_efficiency"] = {"score": context_score, "max": 10, "evidence": context_evidence}

    script_files = [item for item in relative_files if item.startswith("scripts/") and not item.endswith(".pyc")]
    syntax_ok, syntax_failures = python_syntax(skill_dir)
    script_evidence: list[str] = []
    if not script_files:
        script_score = 15
        script_evidence.append("Aucun script requis")
    else:
        script_score = 0
        if syntax_ok:
            script_score += 6
            script_evidence.append("Syntaxe Python valide")
        else:
            critical_failures.extend(f"Script invalide: {item}" for item in syntax_failures)
        documented = sum(
            1
            for relative in script_files
            if (skill_dir / relative).suffix != ".py"
            or '"""' in (skill_dir / relative).read_text(encoding="utf-8", errors="ignore")[:500]
        )
        if documented == len(script_files):
            script_score += 3
            script_evidence.append("Scripts documentés")
        if category_passed(cases, "script"):
            script_score += 6
            script_evidence.append("Tests de scripts réussis")
    dimensions["script_reliability"] = {"score": script_score, "max": 15, "evidence": script_evidence}

    error_score = 0
    error_evidence: list[str] = []
    if keyword_hit(body, (r"erreur", r"échec", r"absent", r"introuvable", r"solution de repli", r"stop")):
        error_score += 4
        error_evidence.append("Erreurs ou ressources absentes traitées")
    if keyword_hit(body, (r"\bsi\b", r"\bwhen\b", r"\bif\b", r"condition")):
        error_score += 3
        error_evidence.append("Branches conditionnelles explicites")
    if category_passed(cases, "missing-resource"):
        error_score += 3
        error_evidence.append("Test de ressource absente réussi")
    dimensions["error_handling"] = {"score": error_score, "max": 10, "evidence": error_evidence}

    safety_score = 0
    safety_evidence: list[str] = []
    if keyword_hit(body, (r"confirm", r"sensible", r"destruct", r"externe", r"réversible", r"permission")):
        safety_score += 5
        safety_evidence.append("Règles de sécurité ou confirmation présentes")
    if category_passed(cases, "safety"):
        safety_score += 5
        safety_evidence.append("Test de sécurité réussi")
    dimensions["safety_confirmations"] = {"score": safety_score, "max": 10, "evidence": safety_evidence}

    tests_total = len(cases)
    tests_passed = sum(1 for case in cases if case["passed"])
    critical_cases = [case for case in cases if case.get("critical", False)]
    critical_passed = sum(1 for case in critical_cases if case["passed"])
    failed_critical = [str(case.get("id", "sans-id")) for case in critical_cases if not case["passed"]]
    if failed_critical:
        critical_failures.append("Tests critiques en échec: " + ", ".join(failed_critical))
    if tests_total:
        real_test_score = round(7 * tests_passed / tests_total)
        if critical_cases:
            real_test_score += round(3 * critical_passed / len(critical_cases))
    else:
        real_test_score = 0
    dimensions["real_tests"] = {
        "score": real_test_score,
        "max": 10,
        "evidence": [f"{tests_passed}/{tests_total} tests réussis", f"{critical_passed}/{len(critical_cases)} critiques réussis"],
    }

    score = sum(item["score"] for item in dimensions.values())
    if critical_failures:
        status = "failed"
    elif official_validation != "passed":
        status = "incomplete"
    elif score >= 90 and tests_total:
        status = "ready"
    elif score >= 75:
        status = "needs-review"
    else:
        status = "needs-work"

    return {
        "schema_version": 2,
        "skill": metadata.get("name", preflight.get("name", "")),
        "path": str(skill_dir),
        "status": status,
        "score": score,
        "max_score": 100,
        "official_validation": official_validation,
        "dimensions": dimensions,
        "critical_failures": sorted(set(critical_failures)),
        "warnings": preflight["warnings"],
        "unlinked_references": unlinked_references,
        "test_summary": {
            "passed": tests_passed,
            "total": tests_total,
            "critical_passed": critical_passed,
            "critical_total": len(critical_cases),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    rows = ["| Dimension | Score | Preuve |", "|---|---:|---|"]
    labels = {
        "trigger_precision": "Déclenchement précis",
        "instruction_clarity": "Instructions claires",
        "architecture": "Architecture",
        "context_efficiency": "Efficacité contextuelle",
        "script_reliability": "Fiabilité des scripts",
        "error_handling": "Gestion des erreurs",
        "safety_confirmations": "Sécurité et confirmations",
        "real_tests": "Tests réels",
    }
    for key, item in report["dimensions"].items():
        evidence = "; ".join(item["evidence"]) or "Aucune preuve"
        rows.append(f"| {labels[key]} | {item['score']}/{item['max']} | {evidence} |")
    failures = report["critical_failures"]
    failure_text = "Aucune" if not failures else "<br>".join(failures)
    return "\n".join(
        [
            f"# Rapport final — {report['skill'] or 'skill inconnu'}",
            "",
            f"- Statut : **{report['status']}**",
            f"- Score automatique : **{report['score']}/100**",
            f"- Validation officielle : **{report['official_validation']}**",
            f"- Défaillances critiques : {failure_text}",
            "",
            *rows,
            "",
            f"Tests : {report['test_summary']['passed']}/{report['test_summary']['total']} réussis, dont {report['test_summary']['critical_passed']}/{report['test_summary']['critical_total']} critiques.",
            "",
            "Le score automatique reste un indicateur; vérifier séparément la pertinence métier et le comportement en contexte neuf.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Auditer et noter un skill")
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument("--tests", type=Path)
    parser.add_argument("--official-validation", choices=("passed", "failed", "not-run"), default="not-run")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        cases = load_test_results(args.tests)
        report = audit_skill(args.skill_dir, cases, args.official_validation)
    except (OSError, ValueError) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 1

    rendered = render_markdown(report) if args.format == "markdown" else json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if not report["critical_failures"] else 1


if __name__ == "__main__":
    sys.exit(main())
