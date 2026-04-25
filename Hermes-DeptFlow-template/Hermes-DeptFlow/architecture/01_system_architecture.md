# Architecture système

## Objectif

Créer un profil Hermes clonable permettant de faire tourner un SDR IA autonome pour un client DeptFlow.

## Composants

```text
Hermes profile
├── SOUL.md
├── config.yaml
├── .env
├── icp_config.yaml
├── campaign_config.yaml
├── prompts/
├── scripts/
└── src/deptflow_sdr/
```

## Workflow

```text
Config -> Query generation -> BeReach search -> Normalize -> Dedupe
      -> Enrich posts -> Score -> QA -> Store -> Message draft -> Report
```

## Stockage

Deux modes sont supportés :

1. **Local fallback** : JSONL dans `data/`.
2. **Supabase** : REST API Supabase si configuré.

Le fallback local garantit que le profil est testable immédiatement.

## Autonomie

Le système est semi-autonome par défaut :

- il recherche et qualifie seul ;
- il prépare les messages ;
- il ne les envoie pas automatiquement ;
- il bloque les actions risquées par défaut.

## Séparation des responsabilités

- `integrations/` : API externes.
- `domain/` : modèles métier.
- `workflows/` : orchestration.
- `safety/` : limites, déduplication, policy.
- `observability/` : logs, rapports.
- `agents/` : logique SDR spécialisée.
