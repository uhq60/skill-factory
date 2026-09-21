# Amélioration continue V3

## Boucle de référence

1. Sélectionner le patron d'architecture avec `select_pattern.py`.
2. Concevoir ou modifier le skill selon ce patron.
3. Valider et auditer avec les outils V2.
4. Exécuter un portefeuille de tâches représentatives.
5. Mesurer les performances avec `benchmark_skill.py`.
6. Agréger les échecs avec `analyze_failures.py`.
7. Produire les corrections prioritaires avec `recommend_improvements.py`.
8. Retester puis enregistrer l'état de maintenance.

## Brief de sélection

```json
{
  "summary": "Interpréter un règlement interne versionné",
  "desired_outputs": ["réponse sourcée", "signalement des règles absentes"],
  "tools": [],
  "constraints": ["ne jamais inventer une règle"]
}
```

## Résultats de benchmark

```json
{
  "skill_name": "example-skill",
  "runs": [
    {
      "task_id": "T1",
      "category": "nominal",
      "passed": true,
      "critical": true,
      "latency_ms": 1200,
      "tokens": 1800,
      "attempts": 1,
      "quality_score": 92
    }
  ]
}
```

Ajouter un `error_code` stable lorsqu'un run échoue. Omettre le message brut dès que le code suffit ; `analyze_failures.py` ne conserve jamais ce message. Ne jamais stocker une requête brute susceptible de contenir des données privées ou confidentielles.

## État de maintenance

```json
{
  "skill_name": "example-skill",
  "version": "3.0.0",
  "last_reviewed_at": "2026-09-21T12:00:00Z",
  "last_score": 94
}
```

Le contrôle de maintenance indique si une revue est due et génère, avec `--record-state`, un nouvel état. Il ne crée pas à lui seul une tâche planifiée.

## Portes de décision

- Bloquer la publication si un run critique échoue.
- Exiger au moins trois tâches et plusieurs catégories pour un benchmark représentatif.
- Prioriser une erreur récurrente dès deux occurrences.
- Refuser une recommandation non reliée à une preuve mesurée.
- Retester les scénarios concernés après chaque correction.
- Conserver les rapports hors du dossier installable afin de ne pas gonfler le contexte du skill.
