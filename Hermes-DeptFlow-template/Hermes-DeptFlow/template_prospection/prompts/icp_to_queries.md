# Prompt — ICP vers requêtes LinkedIn

Transforme l'ICP en requêtes LinkedIn classiques compatibles BeReach.

Règles :
- Ne pas utiliser Sales Navigator.
- Utiliser des opérateurs booléens LinkedIn simples : `AND`, `OR`, `NOT`, guillemets.
- Générer peu de requêtes, mais précises.
- Inclure les exclusions importantes.
- Privilégier les titres/personas et la localisation.

Sortie attendue :
```json
{
  "queries": [
    "..."
  ],
  "rationale": "..."
}
```
