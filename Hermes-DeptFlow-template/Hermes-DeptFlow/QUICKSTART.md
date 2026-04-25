# Quickstart — profil Hermes DeptFlow

## 1. Créer un profil client

```bash
mkdir -p ~/.hermes/profiles
cp -r template_prospection ~/.hermes/profiles/client-demo
cd ~/.hermes/profiles/client-demo
cp .env.template .env
```

## 2. Configurer les secrets

Dans `.env` :

```env
BEREACH_API_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
DRY_RUN=true
```

Le système fonctionne aussi sans Supabase : il écrira dans `data/*.jsonl`.

## 3. Configurer l'ICP

Modifier `icp_config.yaml`.

Le fichier est volontairement au format JSON-compatible YAML pour éviter toute dépendance Python externe. Il reste lisible par les loaders YAML standards.

## 4. Valider

```bash
python3 scripts/validate_config.py
```

## 5. Lancer un dry-run

```bash
python3 scripts/dry_run.py --limit 5
```

Le dry-run utilise des fixtures locales et ne consomme aucun crédit BeReach.

## 6. Lancer avec BeReach, sans action LinkedIn

```bash
DRY_RUN=true USE_BEREACH_IN_DRY_RUN=true python3 scripts/daily_prospecting.py --limit 10
```

Cela appelle BeReach pour rechercher/enrichir, mais ne fait pas d'action LinkedIn.

## 7. Lancer en réel

```bash
DRY_RUN=false python3 scripts/daily_prospecting.py --limit 25
```

Par défaut, même en réel, le système ne fait que rechercher, scorer, sauvegarder et préparer les messages. Les actions LinkedIn sensibles restent désactivées tant qu'elles ne sont pas explicitement activées dans `campaign_config.yaml`.

## 8. Cron recommandé

```cron
0 8 * * 1-5 cd ~/.hermes/profiles/client-demo && /usr/bin/python3 scripts/daily_prospecting.py --limit 25 >> logs/cron.log 2>&1
```
