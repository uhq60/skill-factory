# Automatisation V2

## Formats d'entrée

### specification.json

```json
{
  "skill_name": "example-skill",
  "positive_prompts": ["requête positive 1", "requête positive 2", "requête positive 3"],
  "negative_prompts": ["requête négative 1", "requête négative 2", "requête négative 3"],
  "ambiguous_prompts": ["demande incomplète"],
  "missing_resource_prompts": ["demande avec ressource absente"],
  "sensitive_prompts": ["demande nécessitant une confirmation"]
}
```

Fournir au moins trois requêtes positives et trois négatives. Le générateur attribue des identifiants stables et une action attendue; il n'exécute pas les cas.

### test-results.json

```json
{
  "cases": [
    {
      "id": "P1",
      "category": "trigger",
      "passed": true,
      "critical": true,
      "notes": "Déclenchement observé"
    }
  ]
}
```

Utiliser les catégories `trigger`, `non-trigger`, `ambiguous`, `missing-resource`, `safety`, `script` et `regression`. Un cas critique en échec interdit le statut « prêt ».

## Commandes

- `generate_trigger_tests.py` : normaliser la matrice de tests depuis les spécifications.
- `audit_skill.py` : contrôler la structure, calculer les huit dimensions et produire le rapport final.
- `compare_skills.py` : comparer les inventaires, empreintes et scores de deux versions.
- `preflight_skill.py` : exécuter les contrôles statiques complémentaires.

## Interprétation

Le score automatique est une estimation reproductible fondée sur les preuves disponibles. Il ne mesure pas directement la qualité du raisonnement d'un agent ni la pertinence métier des réponses. Conserver les essais indépendants et l'examen humain comme portes de qualité obligatoires pour les skills complexes ou sensibles.
