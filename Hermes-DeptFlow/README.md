# Hermes DeptFlow

Ce dépôt contient l'architecture de référence et les fichiers modèles nécessaires pour déployer un département SDR IA autonome basé sur l'agent Hermes et l'API BeReach.  Le système est conçu pour identifier, scorer et contacter automatiquement des prospects LinkedIn correspondant à un profil client idéal (ICP) tout en respectant les limites de la plateforme.  Les fichiers sont structurés pour être clonés par profil client via `hermes profile create --clone --clone-from template_prospection`.

## Aperçu

* **template_prospection** – répertoire contenant les modèles d'environnement, de configuration et de prompts utilisés par chaque profil.  En clonant ce répertoire, vous créez une instance isolée de l'agent pour un nouveau client.
* **.env.template** – variables d'environnement à remplir pour chaque client (clés API, informations Supabase, limites, etc.).
* **config.yaml** – configuration Hermes définissant le modèle LLM, les limites d'actions et les plugins à utiliser, ainsi que le seuil de score pour qualifier un lead.
* **SOUL.md** – description haute‑niveau de la mission et des règles que l'agent doit suivre.  Il précise notamment l'utilisation de Supabase, le rejet automatique des leads notés en dessous de 75 et l'absence de note sur les invitations LinkedIn.
* **prompts/** – fichiers Markdown décrivant les instructions détaillées pour générer des requêtes à partir de l'ICP, calculer un score, rédiger des messages après acceptation, réaliser un suivi et produire un rapport quotidien.
* **product_review.md** – document décrivant l’architecture globale, les choix techniques, les modules agents et la roadmap proposée.

## Structure recommandée

```
Hermes-DeptFlow/
├── README.md
├── product_review.md
└── template_prospection/
    ├── .env.template
    ├── config.yaml
    ├── SOUL.md
    ├── prompts/
    │   ├── icp_to_queries.md
    │   ├── lead_scoring.md
    │   ├── connection_note.md
    │   ├── first_message.md
    │   ├── follow_up.md
    │   ├── daily_report.md
    │   └── qa_review.md
    └── scripts/
        └── README.md
```

Pour chaque client, copiez le dossier `template_prospection` dans un nouveau profil Hermes :

```bash
hermes profile create client_acme --clone --clone-from template_prospection
```

Ensuite, remplissez les variables d’environnement dans `.env` à partir du fichier `.env.template` et adaptez le contenu de `SOUL.md` en fonction de l’ICP et de l’offre du client.
