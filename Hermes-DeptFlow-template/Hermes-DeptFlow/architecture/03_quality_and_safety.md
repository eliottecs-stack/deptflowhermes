# Qualité et sécurité

## Garde-fous

- `DRY_RUN=true` par défaut.
- Pas de Sales Navigator par défaut.
- Pas d'envoi automatique de DM.
- Pas de commentaire automatique.
- Pas de like automatique.
- Follow désactivé par défaut.
- Toute personnalisation doit venir d'une donnée réelle.
- Les leads sous seuil sont rejetés.

## QA lead

Un lead est bloqué si :

- URL LinkedIn manquante ;
- nom manquant ;
- headline vide ;
- exclusion ICP détectée ;
- score inférieur au seuil ;
- doublon ;
- `doNotContact=true`.

## QA message

Un message est bloqué si :

- il contient une information non présente dans les données ;
- il est trop long ;
- il promet un résultat non prouvé ;
- il utilise un ton agressif ;
- il demande trop tôt un rendez-vous sans contexte.

## Rate limits

Le système respecte :

- limites configurées localement ;
- `retryAfter` retourné par BeReach ;
- arrêt propre en cas de 429.

## Journaux

Les logs doivent exclure :

- API keys ;
- service role Supabase ;
- contenu sensible non nécessaire.
