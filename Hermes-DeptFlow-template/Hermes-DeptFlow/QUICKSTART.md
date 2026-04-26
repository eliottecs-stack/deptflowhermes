# Quickstart - Hermes DeptFlow Local Control Plane

## 1. Installer le repo dans Hermes

```bash
git clone https://github.com/eliottecs-stack/deptflowhermes.git
cd deptflowhermes/Hermes-DeptFlow-template/Hermes-DeptFlow/template_prospection
python3 scripts/start_dashboard.py
```

Ouvrir ensuite `http://127.0.0.1:8765`.

## 2. Creer un client sans terminal

Depuis le dashboard :

1. cliquer sur `Creer un client` ;
2. renseigner client, offre, ICP, exclusions et quota de connexions ;
3. generer le profil Hermes client ;
4. lancer un dry-run depuis la liste des profils.

Le dashboard cree un profil client sous `control_plane/profiles/<client-slug>/`.

## 3. Secrets et APIs

Le fichier `.env.template` documente les secrets attendus. En V1, le dashboard expose le contrat local; les secrets reels doivent etre stockes via le vault local chiffre ou injectes dans `.env` pour les tests CLI.

Secrets principaux :

```env
BEREACH_API_KEY=...
OPENAI_API_KEY=...
GOOGLE_SERVICE_ACCOUNT_JSON=...
GOOGLE_SHEET_ID=...
DRY_RUN=true
```

## 4. Mode dry-run

Le dry-run utilise les fixtures locales par defaut et ne consomme aucun credit BeReach :

```bash
python3 scripts/dry_run.py --limit 5
```

## 5. Gate go-live

L'auto-connexion reste bloquee tant que ces conditions ne sont pas remplies :

- un dry-run termine avec succes ;
- au moins 10 leads/messages approuves ;
- un quota quotidien de connexion configure ;
- les limites BeReach disponibles via `GET /me/limits`.

La V1 envoie des demandes de connexion sans note et prepare les brouillons DM pour suivi CRM.

## 6. Tests

```bash
python3 -m unittest discover -s tests -v
```
