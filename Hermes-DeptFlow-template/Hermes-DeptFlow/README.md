# Hermes DeptFlow — SDR IA autonome LinkedIn

Ce dépôt contient le **template de profil Hermes DeptFlow** pour déployer un SDR IA autonome orienté prospection LinkedIn gratuite.

Objectif produit : permettre à Hermes de cloner ce repo comme base de profil client, puis de lancer une prospection quotidienne fiable, traçable et contrôlée.

## Positionnement

DeptFlow n'est pas un simple bot LinkedIn. C'est un **département SDR IA supervisé** :

1. il lit l'ICP et l'offre du client ;
2. il génère des requêtes de prospection LinkedIn ;
3. il recherche des personnes via BeReach ;
4. il enrichit avec les posts publics disponibles ;
5. il score les leads ;
6. il rejette les mauvais profils ;
7. il prépare des messages sans hallucination ;
8. il sauvegarde les résultats ;
9. il produit un rapport quotidien.

## Contraintes assumées

- **Pas de Sales Navigator par défaut** : le moteur utilise les endpoints LinkedIn classiques BeReach.
- **Dry-run par défaut** : aucune action LinkedIn réelle n'est exécutée tant que `DRY_RUN=false` n'est pas configuré explicitement.
- **Messages non envoyés automatiquement** : le MVP prépare les messages et les soumet au contrôle humain.
- **Aucun secret dans le repo** : copier `.env.template` vers `.env` puis remplir les clés.

## Structure

```text
Hermes-DeptFlow/
├── README.md
├── QUICKSTART.md
├── product_review.md
├── architecture/
│   ├── 01_system_architecture.md
│   ├── 02_bereach_contract.md
│   ├── 03_quality_and_safety.md
│   └── 04_release_checklist.md
└── template_prospection/
    ├── .env.template
    ├── config.yaml
    ├── SOUL.md
    ├── icp_config.yaml
    ├── campaign_config.yaml
    ├── prompts/
    ├── scripts/
    ├── src/deptflow_sdr/
    ├── supabase/schema.sql
    └── tests/
```

## Installation comme profil Hermes

Depuis la machine où Hermes tourne :

```bash
git clone https://github.com/eliottecs-stack/deptflowhermes.git
mkdir -p ~/.hermes/profiles
cp -r deptflowhermes/Hermes-DeptFlow/template_prospection ~/.hermes/profiles/client-acme
cd ~/.hermes/profiles/client-acme
cp .env.template .env
```

Modifier ensuite :

- `.env`
- `icp_config.yaml`
- `campaign_config.yaml`
- `SOUL.md`

Puis tester :

```bash
python3 scripts/validate_config.py
python3 scripts/dry_run.py --limit 5
```

Exécution réelle, après validation :

```bash
DRY_RUN=false python3 scripts/daily_prospecting.py --limit 25
```

## Résultat attendu

Le run produit :

- des leads scorés ;
- un fichier local `data/leads.jsonl` si Supabase n'est pas configuré ;
- une sauvegarde Supabase si `SUPABASE_URL` et `SUPABASE_SERVICE_KEY` sont renseignés ;
- des messages préparés, non envoyés automatiquement ;
- un rapport Markdown dans `reports/`.

## Endpoints BeReach utilisés

Le moteur par défaut s'appuie uniquement sur les endpoints classiques :

- `POST /search/linkedin`
- `GET /search/linkedin/parameters`
- `POST /collect/linkedin/posts`
- `POST /collect/linkedin/comments`
- `POST /collect/linkedin/comments/replies`
- `POST /collect/linkedin/likes`
- `POST /follow/linkedin/profile`
- `POST /unfollow/linkedin/profile`
- `GET /contacts/by-url`
- `PATCH /contacts/bulk`

Les endpoints `/search/linkedin/sales-nav*` sont volontairement exclus du workflow standard, car ils nécessitent Sales Navigator.

## Principes qualité

- Un lead non justifié n'est pas contacté.
- Une personnalisation non prouvée est interdite.
- Un lead en dessous du seuil est rejeté.
- Les messages sont préparés, pas envoyés automatiquement.
- Les quotas et `retryAfter` BeReach sont respectés.
- Le mode réel doit toujours passer par un dry-run validé.

## Licence interne

Template produit DeptFlow.
