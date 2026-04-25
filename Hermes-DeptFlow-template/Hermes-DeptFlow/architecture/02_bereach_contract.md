# Contrat BeReach

## Endpoints autorisés dans le workflow standard

Le profil DeptFlow free LinkedIn utilise uniquement les endpoints classiques BeReach :

| Usage | Endpoint |
|---|---|
| Recherche unifiée | `POST /search/linkedin` |
| Résolution GEO/COMPANY/INDUSTRY | `GET /search/linkedin/parameters` |
| Posts d'un profil | `POST /collect/linkedin/posts` |
| Commentaires d'un post | `POST /collect/linkedin/comments` |
| Réponses de commentaires | `POST /collect/linkedin/comments/replies` |
| Likes d'un post | `POST /collect/linkedin/likes` |
| Follow profil | `POST /follow/linkedin/profile` |
| Unfollow profil | `POST /unfollow/linkedin/profile` |
| Contact par URL | `GET /contacts/by-url` |
| Bulk update contacts | `PATCH /contacts/bulk` |

## Endpoints exclus par défaut

Les endpoints suivants existent mais sont exclus du workflow standard :

```text
/search/linkedin/sales-nav
/search/linkedin/sales-nav/people
/search/linkedin/sales-nav/companies
```

Raison : ils nécessitent un abonnement LinkedIn Sales Navigator actif.

## Règles d'implémentation

1. Tous les appels passent par `BeReachClient`.
2. Le client lit `creditsUsed` et `retryAfter` quand ils existent.
3. Les erreurs 429 doivent être remontées avec `retryAfter`.
4. Aucune action LinkedIn sensible ne doit être déclenchée en dry-run.
5. Les méthodes Sales Navigator ne doivent pas être appelées sauf feature flag explicite futur.

## Authentification

Le client supporte par défaut :

```env
BEREACH_AUTH_HEADER=Authorization
BEREACH_AUTH_SCHEME=Bearer
```

Si BeReach fournit un autre format de token, changer ces variables sans modifier le code.

## Mapping minimum des données

Une personne BeReach est normalisée vers :

```text
first_name
last_name
full_name
headline
company_name
location
linkedin_url
public_identifier
profile_urn
source
raw
```
