# Checklist release

Avant d'utiliser un profil client en production :

```text
[ ] .env créé depuis .env.template
[ ] BEREACH_API_KEY renseignée
[ ] DRY_RUN=true testé
[ ] python3 scripts/validate_config.py OK
[ ] python3 scripts/dry_run.py --limit 5 OK
[ ] Rapport généré dans reports/
[ ] ICP relu
[ ] Exclusions renseignées
[ ] Seuil de qualification validé
[ ] Supabase configuré ou fallback local accepté
[ ] Aucune action LinkedIn sensible activée sans validation
[ ] Messages relus par un humain sur les 10 premiers leads
[ ] Cron configuré uniquement après validation
```
