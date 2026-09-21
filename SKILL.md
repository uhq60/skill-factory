---
name: skill-factory
description: Concevoir, structurer, tester et préparer l'installation de skills personnels robustes en orchestrant le skill officiel skill-creator. Utiliser lorsque l'utilisateur demande une fabrique de skills, la création complète d'un skill avec cahier des charges et tests, l'audit ou l'amélioration méthodique d'un skill, une matrice de déclenchement et de non-déclenchement, ou un rapport qualité avant installation. Ne pas utiliser pour une simple question générale sur les skills ni pour une installation directe sans travail de conception.
---

# Skill Factory

## Mission

Transformer une intention en skill personnel testable, économe en contexte et prêt à être installé. Orchestrer le skill officiel `skill-creator`; ne jamais dupliquer ni contourner ses règles d'initialisation, de validation ou d'installation.

## Principe de fonctionnement

Traiter la création d'un skill comme une chaîne de production avec des portes de qualité. Ne pas confondre validité structurelle et efficacité réelle.

Toujours :

1. Lire intégralement `skill-creator` avant toute création, modification ou installation.
2. Déterminer si la demande concerne une création, un audit, une amélioration ou une conversion de procédure.
3. Conserver `SKILL.md` bref et déplacer les détails dans des ressources chargées à la demande.
4. Utiliser des scripts seulement pour les opérations déterministes ou répétitives.
5. Tester les déclenchements positifs et négatifs avant de déclarer le skill prêt.

## Workflow de production

### 1. Cadrer le besoin

Recueillir ou déduire les informations du modèle [specification-template.md](references/specification-template.md). Demander uniquement les éléments manquants qui changeraient matériellement le résultat.

Obtenir au minimum :

- trois requêtes représentatives qui doivent déclencher le skill ;
- trois requêtes proches qui ne doivent pas le déclencher ;
- les sorties attendues et les critères de réussite ;
- les outils, fichiers, sources et contraintes ;
- les actions sensibles nécessitant une confirmation.

Si la demande est suffisamment précise, annoncer brièvement les hypothèses et poursuivre sans bloquer.

### 2. Concevoir l'architecture

Lire [architecture-rules.md](references/architecture-rules.md), puis décider ce qui appartient à :

- `SKILL.md` pour le workflow essentiel ;
- `references/` pour les connaissances détaillées ;
- `scripts/` pour la fiabilité déterministe ;
- `assets/` pour les modèles ou fichiers destinés aux livrables.

Écarter tout fichier auxiliaire sans utilité opérationnelle. Ne jamais ajouter de README, journal des changements ou guide d'installation au skill.

### 3. Initialiser et implémenter

Suivre exactement la procédure courante de `skill-creator` :

1. Résoudre le répertoire officiel des skills personnels.
2. Vérifier qu'aucun skill actif ou désactivé ne porte déjà le même `name`.
3. Initialiser le skill avec le script officiel et uniquement les répertoires de ressources nécessaires.
4. Rédiger le frontmatter avec seulement `name` et `description`.
5. Écrire le corps à l'impératif ou à l'infinitif.
6. Générer `agents/openai.yaml` selon la référence officielle.
7. Tester réellement chaque script ajouté.

Ne jamais créer une copie installable dans un répertoire de travail temporaire.

### 4. Valider

Exécuter d'abord le validateur officiel indiqué par `skill-creator`, puis le contrôle complémentaire :

```bash
python3 scripts/preflight_skill.py /chemin/vers/le-skill
```

Corriger toutes les erreurs. Examiner les avertissements un par un au lieu de les ignorer globalement.

Lancer ensuite l'audit V2. Lire [v2-automation.md](references/v2-automation.md) avant de préparer ses fichiers d'entrée.

```bash
python3 scripts/audit_skill.py /chemin/vers/le-skill \
  --tests /chemin/vers/test-results.json \
  --format markdown
```

Traiter le score automatique comme un indicateur traçable, jamais comme une preuve suffisante de qualité.

### 5. Tester le comportement

Lire [test-patterns.md](references/test-patterns.md) et établir une matrice couvrant :

- déclenchement attendu ;
- non-déclenchement ;
- demande ambiguë ou incomplète ;
- erreur d'outil ou ressource absente ;
- action sensible ;
- tâche réaliste sans contexte préalable ;
- non-régression après modification.

Générer la matrice normalisée à partir des exemples validés dans les spécifications :

```bash
python3 scripts/generate_trigger_tests.py specification.json \
  --output trigger-tests.json
```

Exécuter ensuite les cas avec un contexte neuf et consigner les observations dans `test-results.json`. La génération de cas ne vaut pas exécution des tests.

Pour un skill complexe, effectuer des essais indépendants avec un minimum de contexte, lorsque l'environnement et l'autorisation permettent d'utiliser des agents séparés. Ne jamais transmettre la réponse attendue ou le diagnostic supposé au testeur.

### 6. Évaluer et décider

Appliquer [evaluation-rubric.md](references/evaluation-rubric.md). Un skill est prêt seulement si :

- aucune défaillance critique n'est présente ;
- le validateur officiel réussit ;
- le contrôle complémentaire ne retourne aucune erreur ;
- tous les tests critiques passent ;
- le score manuel atteint 90 sur 100.

En dessous du seuil, corriger puis reprendre validation, tests et évaluation.

Lors d'une mise à jour, comparer l'ancienne version et la candidate :

```bash
python3 scripts/compare_skills.py /chemin/ancienne /chemin/candidate \
  --format markdown
```

Examiner les fichiers ajoutés, supprimés et modifiés ainsi que l'évolution du score. Une hausse du score ne compense pas une régression fonctionnelle.

### 7. Installer ou remettre le résultat

Si la demande autorise la création ou la mise à jour, suivre `skill-creator` jusqu'à l'installation et à sa vérification complète. Ne jamais annoncer qu'un skill est installé avant cette vérification.

Si l'utilisateur demande uniquement un plan, un audit ou un prototype, ne pas installer. Remettre plutôt les spécifications, l'architecture, les résultats des tests et la prochaine décision attendue.

## Contrat de sortie

Présenter une synthèse courte comprenant :

- le nom et la fonction du skill ;
- les composants créés ou modifiés ;
- les validations et tests exécutés ;
- les limites ou risques restants ;
- le statut exact : brouillon, à corriger, prêt, ou installé.

Ne pas masquer un échec derrière un score moyen. Signaler clairement toute défaillance critique.

Le rapport Markdown produit par `audit_skill.py` constitue le rapport final avant installation. Le compléter avec les résultats qualitatifs des essais indépendants lorsque ceux-ci ont été exécutés.
