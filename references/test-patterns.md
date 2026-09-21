# Patrons de tests

## Matrice minimale

1. Trois requêtes qui doivent déclencher le skill.
2. Trois requêtes proches qui ne doivent pas le déclencher.
3. Deux demandes incomplètes ou ambiguës.
4. Un outil, fichier ou service indisponible.
5. Une action sensible nécessitant une confirmation.
6. Une tâche réaliste sans historique de conversation.
7. Un test de non-régression après toute correction importante.

Pour chaque essai, consigner la requête brute, le contexte réellement fourni, le comportement attendu, le résultat observé et la décision.

## Trois familles de référence

Utiliser ces familles pour vérifier que la méthode ne sur-adapte pas tous les skills au même type de tâche.

### A. Skill de connaissance procédurale

Exemple : interpréter un règlement interne versionné.

Architecture attendue : workflow concis dans `SKILL.md`, documents de référence séparés, stratégie explicite pour les règles absentes ou contradictoires. Aucun script n'est nécessaire sans traitement répétitif démontré.

### B. Skill de transformation déterministe

Exemple : convertir et contrôler un format de fichier structuré.

Architecture attendue : script paramétrable, erreurs explicites, tests sur entrée valide et invalide, instructions minimales dans `SKILL.md`.

### C. Skill créatif sous contraintes

Exemple : produire des supports respectant une identité visuelle.

Architecture attendue : règles dans `references/`, fichiers originaux verrouillés dans `assets/`, workflow de contrôle visuel et interdiction de régénérer les éléments de marque protégés.

## Tests de déclenchement

Vérifier séparément :

- les formulations directes ;
- les synonymes courants ;
- les formats de fichiers concernés ;
- les demandes voisines relevant d'un autre skill ;
- les demandes générales qui ne nécessitent aucune procédure spécialisée.

Un test négatif réussi signifie que le skill ne s'impose pas à une demande voisine. Un déclenchement trop large est un défaut, même si la réponse finale reste correcte.

## Test d'indépendance

Fournir au testeur uniquement :

- le skill accessible à l'emplacement normal ;
- la requête utilisateur brute ;
- les fichiers que l'utilisateur aurait réellement fournis.

Ne pas communiquer le résultat attendu, le défaut soupçonné ou les conclusions des essais précédents.
