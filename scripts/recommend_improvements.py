#!/usr/bin/env python3
"""Generate prioritized, evidence-backed improvements from V2/V3 reports."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DIMENSION_ACTIONS = {
    "trigger_precision": ("P1", "Préciser la description et renforcer les cas positifs/négatifs", "Répéter les tests de déclenchement"),
    "instruction_clarity": ("P1", "Rendre le workflow et le contrat de sortie directement exécutables", "Faire exécuter une tâche sans contexte préalable"),
    "architecture": ("P1", "Supprimer les fichiers superflus et relier chaque référence depuis SKILL.md", "Relancer le précontrôle"),
    "context_efficiency": ("P2", "Réduire SKILL.md et déplacer les détails vers des références ciblées", "Mesurer les lignes et vérifier les liens directs"),
    "script_reliability": ("P0", "Ajouter ou réparer les tests nominaux et d'échec des scripts", "Exécuter tous les tests de scripts"),
    "error_handling": ("P1", "Ajouter des arrêts, solutions de repli et messages d'erreur observables", "Tester une ressource absente et une erreur d'outil"),
    "safety_confirmations": ("P0", "Ajouter des portes de confirmation proportionnées aux actions sensibles", "Exécuter le scénario de sécurité"),
    "real_tests": ("P1", "Élargir et réexécuter le portefeuille de tests réels", "Atteindre le seuil sur toutes les catégories critiques"),
}


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


def add_recommendation(
    target: dict[str, dict[str, Any]],
    key: str,
    priority: str,
    evidence: str,
    action: str,
    verification: str,
) -> None:
    candidate = {
        "id": key,
        "priority": priority,
        "evidence": evidence,
        "action": action,
        "verification": verification,
    }
    existing = target.get(key)
    order = {"P0": 0, "P1": 1, "P2": 2}
    if existing is None or order[priority] < order[existing["priority"]]:
        target[key] = candidate


def recommendations(audit: dict[str, Any], benchmark: dict[str, Any], failures: dict[str, Any]) -> dict[str, Any]:
    skill_names = {value for value in (audit.get("skill"), benchmark.get("skill_name"), failures.get("skill_name")) if value}
    if len(skill_names) > 1:
        raise ValueError("les rapports concernent des skills différents")
    skill_name = next(iter(skill_names), "unknown-skill")
    items: dict[str, dict[str, Any]] = {}

    for failure in audit.get("critical_failures", []):
        add_recommendation(items, "resolve-critical-audit", "P0", str(failure), "Corriger toutes les défaillances critiques de l'audit", "Relancer l'audit sans défaillance critique")
    for key, dimension in audit.get("dimensions", {}).items():
        if key not in DIMENSION_ACTIONS or not isinstance(dimension, dict):
            continue
        score = dimension.get("score", 0)
        maximum = dimension.get("max", 0)
        if score < maximum:
            priority, action, verification = DIMENSION_ACTIONS[key]
            add_recommendation(items, f"improve-{key}", priority, f"{key}: {score}/{maximum}", action, verification)

    overall = benchmark.get("overall", {})
    if overall.get("critical_pass_rate", 100) < 100:
        add_recommendation(items, "critical-benchmark", "P0", f"Taux critique: {overall.get('critical_pass_rate')}%", "Corriger les scénarios critiques avant toute publication", "Atteindre 100% sur les runs critiques")
    if overall.get("pass_rate", 100) < 90:
        add_recommendation(items, "benchmark-pass-rate", "P1", f"Taux de réussite: {overall.get('pass_rate')}%", "Corriger les catégories les plus faibles du benchmark", "Atteindre au moins 90% de réussite")
    if overall.get("average_quality", 100) < 80:
        add_recommendation(items, "benchmark-quality", "P1", f"Qualité moyenne: {overall.get('average_quality')}", "Renforcer les critères métier et les exemples de sortie", "Atteindre une qualité moyenne de 80")
    if overall.get("average_attempts", 1) > 1.5:
        add_recommendation(items, "benchmark-retries", "P2", f"Tentatives moyennes: {overall.get('average_attempts')}", "Réduire les ambiguïtés et automatiser les étapes répétitives", "Ramener la moyenne à 1,5 tentative ou moins")
    if benchmark.get("representative") is False:
        add_recommendation(items, "benchmark-coverage", "P1", "Benchmark limité à une seule catégorie", "Ajouter plusieurs familles de tâches représentatives", "Couvrir au moins deux catégories")

    for cluster in failures.get("clusters", []):
        if not isinstance(cluster, dict) or not (cluster.get("recurring") or cluster.get("priority") == "P0"):
            continue
        code = str(cluster.get("code", "unclassified"))
        priority = str(cluster.get("priority", "P1"))
        if "permission" in code:
            action = "Ajouter un contrôle de permission et une voie de reprise explicite"
        elif "timeout" in code:
            action = "Définir un budget de temps, un nombre de tentatives et une sortie contrôlée"
        elif "missing" in code or "resource" in code:
            action = "Détecter la ressource absente avant l'exécution et demander uniquement l'élément requis"
        elif "trigger" in code:
            action = "Resserrer la description et les cas de non-déclenchement"
        else:
            action = "Reproduire le cluster, identifier sa cause puis ajouter un test de non-régression"
        add_recommendation(
            items,
            f"failure-{code}",
            priority if priority in {"P0", "P1", "P2"} else "P1",
            f"{code}: {cluster.get('count', 0)} occurrence(s)",
            action,
            f"Le code {code} ne doit plus récidiver sur le portefeuille de tests",
        )

    order = {"P0": 0, "P1": 1, "P2": 2}
    ranked = sorted(items.values(), key=lambda item: (order[item["priority"]], item["id"]))
    readiness = "blocked" if any(item["priority"] == "P0" for item in ranked) else "improve" if ranked else "stable"
    return {
        "schema_version": 1,
        "skill_name": skill_name,
        "readiness": readiness,
        "recommendation_count": len(ranked),
        "recommendations": ranked,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Recommander les améliorations d'un skill")
    parser.add_argument("audit", type=Path)
    parser.add_argument("benchmark", type=Path)
    parser.add_argument("failures", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = recommendations(load_object(args.audit), load_object(args.benchmark), load_object(args.failures))
    except (OSError, ValueError) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 1
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["readiness"] != "blocked" else 1


if __name__ == "__main__":
    sys.exit(main())
