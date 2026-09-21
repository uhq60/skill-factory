# Règles d'architecture

## Arbre de décision

| Besoin | Emplacement | Raison |
|---|---|---|
| Instruction indispensable à chaque exécution | `SKILL.md` | Chargement systématique après déclenchement |
| Documentation longue ou spécialisée | `references/` | Chargement progressif selon le besoin |
| Opération répétitive, calcul ou transformation fragile | `scripts/` | Exécution déterministe et testable |
| Modèle, image, police ou squelette copié dans un livrable | `assets/` | Utilisation sans chargement contextuel |
| Explication sur la conception du skill | Nulle part | N'améliore pas son exécution |

## Degré de liberté

- Employer des instructions textuelles lorsque plusieurs approches peuvent réussir.
- Employer un pseudo-code ou un script paramétrable lorsqu'un patron doit rester stable.
- Employer un script strict lorsque l'ordre des opérations, les formats ou la sécurité ne tolèrent pas l'improvisation.

## Règles de découpage

1. Garder `SKILL.md` sous 500 lignes.
2. Relier chaque référence directement depuis `SKILL.md`; éviter les chaînes de références imbriquées.
3. Ajouter une table des matières aux références de plus de 100 lignes.
4. Ne jamais dupliquer une même règle dans `SKILL.md` et une référence.
5. Supprimer les répertoires de ressources vides.
6. Éviter les scripts qui ne font qu'imprimer un modèle textuel facile à conserver en Markdown.

## Description de déclenchement

La description doit indiquer :

- ce que fait le skill ;
- les contextes précis dans lesquels l'utiliser ;
- les formats, outils ou tâches discriminants ;
- les exclusions utiles si le risque de faux déclenchement est réel.

Mettre toutes les règles de déclenchement dans la description du frontmatter. Ne pas créer une section « Quand utiliser ce skill » dans le corps : le corps n'est chargé qu'après le déclenchement.

## Critères pour ajouter un script

Ajouter un script seulement si au moins une condition est vraie :

- le même code serait réécrit dans plusieurs exécutions ;
- une erreur manuelle pourrait corrompre un fichier ou produire un résultat faux ;
- la sortie doit être reproductible ;
- une validation automatisée apporte une preuve observable.

Tester chaque script sur un cas nominal et au moins un cas d'échec.
