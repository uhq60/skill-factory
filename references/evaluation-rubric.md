# Grille d'évaluation

Noter uniquement à partir d'éléments observables : fichiers, sorties, tests et comportements. Ne pas attribuer les points sur la seule intention.

## Défaillances critiques

Un seul de ces défauts interdit le statut « prêt », quel que soit le score :

- validateur officiel en échec ;
- action destructive ou externe sans contrôle adapté ;
- description incapable de distinguer les principaux cas positifs et négatifs ;
- script non testé ou en échec sur son scénario nominal ;
- dépendance essentielle absente et sans solution de repli ;
- affirmation d'installation sans vérification finale.

## Barème sur 100

| Dimension | Points | Preuve attendue |
|---|---:|---|
| Déclenchement précis | 15 | Tests positifs et négatifs discriminants |
| Instructions claires | 15 | Workflow exécutable sans interprétation majeure |
| Architecture pertinente | 15 | Ressources justifiées, aucun fichier superflu |
| Efficacité contextuelle | 10 | Corps concis, divulgation progressive |
| Fiabilité des scripts | 15 | Cas nominal et cas d'échec réussis |
| Gestion des erreurs | 10 | Arrêts, reprises et messages utiles |
| Sécurité et confirmations | 10 | Portes proportionnées aux risques |
| Réussite des tests réels | 10 | Matrice exécutée et résultats observables |

## Interprétation

- 90 à 100 : prêt si aucune défaillance critique n'existe.
- 75 à 89 : corrections mineures ou tests supplémentaires nécessaires.
- 60 à 74 : révision substantielle du workflow ou de l'architecture.
- Moins de 60 : reprendre le cadrage.

## Rapport minimal

| Élément | Valeur |
|---|---|
| Score total | /100 |
| Défaillances critiques | Aucune / liste |
| Tests réussis | /total |
| Tests critiques réussis | /total |
| Décision | Brouillon / À corriger / Prêt / Installé |
| Prochaine action |  |
