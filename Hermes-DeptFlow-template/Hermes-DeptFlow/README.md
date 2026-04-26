# Hermes DeptFlow - SDR IA autonome supervise

Ce dossier contient une V1 de **control plane local Hermes DeptFlow** : un dashboard Python local pour creer et piloter des profils clients Hermes de prospection LinkedIn via BeReach.

Objectif produit : un createur non technique installe le repo GitHub, ouvre un dashboard local, configure un client, lance un dry-run, valide un echantillon, puis active une prospection moderee avec suivi Google Sheets.

## Positionnement

DeptFlow n'est pas un simple bot LinkedIn. C'est un **departement SDR IA supervise** :

1. il lit l'ICP et l'offre du client ;
2. il genere ou lit des requetes de prospection LinkedIn ;
3. il recherche des personnes via BeReach ;
4. il enrichit avec les posts publics disponibles ;
5. il score les leads ;
6. il rejette les mauvais profils ;
7. il prepare des messages sans hallucination ;
8. il sauvegarde les resultats ;
9. il synchronise un suivi CRM Google Sheets ou CSV ;
10. il bloque les actions reelles tant que le gate go-live n'est pas valide.

## Lancement dashboard

```bash
git clone https://github.com/eliottecs-stack/deptflowhermes.git
cd deptflowhermes/Hermes-DeptFlow-template/Hermes-DeptFlow/template_prospection
python3 scripts/start_dashboard.py
```

Ouvrir `http://127.0.0.1:8765`.

## Structure

```text
Hermes-DeptFlow/
├── README.md
├── QUICKSTART.md
├── architecture/
└── template_prospection/
    ├── .env.template
    ├── profile.manifest.json
    ├── config.schema.json
    ├── secrets.schema.json
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

## Control plane local

La V1 ajoute :

- registry SQLite locale : clients, profils, releases, runs, leads, quotas, CRM syncs ;
- vault local chiffre pour secrets client ;
- generation de profils Hermes isoles depuis un formulaire ;
- dashboard local avec onboarding et bouton dry-run ;
- gate go-live : dry-run valide, 10 validations, quotas configures ;
- contrat BeReach mis a jour : `POST /search/linkedin/people`, `POST /connect/linkedin/profile`, `GET /me/limits` ;
- sync CRM Google Sheets/CSV via lignes standardisees.

## Garde-fous

- Dry-run par defaut.
- Pas de Sales Navigator par defaut.
- Demande de connexion sans note en V1.
- Aucun DM envoye automatiquement.
- Stop-run sur limites BeReach a cabler cote operateur.
- Aucun secret ne doit etre commite ni affiche dans les logs.

## Tests

Depuis `template_prospection` :

```bash
python3 -m unittest discover -s tests -v
```
