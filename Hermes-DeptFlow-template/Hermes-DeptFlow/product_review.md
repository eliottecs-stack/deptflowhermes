# Revue Produit — DeptFlow SDR IA autonome

## Décision produit

DeptFlow doit être vendu et construit comme un **département SDR IA supervisé**, pas comme un bot LinkedIn.

Le MVP doit être fiable avant d'être agressif :

- rechercher ;
- enrichir ;
- scorer ;
- qualifier ;
- sauvegarder ;
- préparer les messages ;
- produire un rapport ;
- laisser l'humain valider l'outreach.

## Architecture choisie

Un profil Hermes = un client ou une campagne client.

Chaque profil contient :

- ses variables `.env` ;
- son ICP ;
- son offre ;
- son état local ;
- ses rapports ;
- ses prompts ;
- sa configuration de limites.

## BeReach

Le workflow standard utilise les endpoints LinkedIn classiques :

- recherche unifiée LinkedIn ;
- résolution de paramètres ;
- collecte posts/commentaires/likes ;
- follow/unfollow si activé ;
- contacts.

Sales Navigator est exclu du chemin principal car la majorité des comptes LinkedIn clients n'y ont pas accès.

## Pipeline

1. Charger la configuration.
2. Générer ou lire les requêtes.
3. Rechercher des personnes LinkedIn.
4. Normaliser les résultats.
5. Dédupliquer.
6. Collecter les posts récents si possible.
7. Calculer un score explicable.
8. Passer le QA.
9. Sauvegarder.
10. Préparer un message.
11. Générer le rapport quotidien.

## MVP livré

Le MVP est volontairement simple :

- Python standard library ;
- dry-run sans API ;
- BeReach optionnel ;
- Supabase optionnel ;
- stockage local fallback ;
- aucune dépendance lourde ;
- aucune action LinkedIn intrusive par défaut.

## Critères de qualité

Le produit est considéré prêt si :

- `python3 scripts/validate_config.py` passe ;
- `python3 scripts/dry_run.py --limit 5` produit un rapport ;
- aucun secret n'est commité ;
- les leads ont un score explicable ;
- les messages ne contiennent pas d'information inventée ;
- les endpoints Sales Navigator ne sont pas utilisés par défaut.
