# Revue Produit – SDR IA LinkedIn via Hermes

Ce document consolide les éléments de design et les choix techniques discutés pour construire et faire évoluer le département SDR IA autonome.  Il sert de référence pour valider ou ajuster les fonctionnalités avant implémentation.

## A. Architecture générale

1. **VM unique avec profils Hermes** : chaque client est isolé dans un profil Hermes (`client_x`) cloné à partir d’un template (`template_prospection`).  Cette isolation garantit des configurations, des clés API et des mémoires séparées tout en mutualisant l’infrastructure.
2. **Table Supabase par client** : la base de données Supabase stocke les leads qualifiés (score ≥ 75).  Les leads non qualifiés ne sont pas enregistrés.  Supabase remplace Firebase pour le bloc CRM.
3. **Agent autonome orchestré par Hermes** : l’agent planifie ses actions (recherche, scoring, sauvegarde, connexion, messages) et apprend des retours (via le QA et les rapports quotidiens).
4. **Dashboard no‑code** : interface Web permettant de créer un client via formulaire, de lancer/arrêter les agents, de visualiser les KPIs (leads trouvés, qualification, invitations envoyées, etc.) et de modifier l’ICP/l’offre sans utiliser la ligne de commande.
5. **Sous‑agents spécialisés** : modules complémentaires pour le contrôle qualité (QA), l’analyse des signaux d’intention et la génération de rapports.

## B. Pipeline de prospection

1. **Onboarding** : saisie structurée de l’ICP, de l’offre et des clés API via le dashboard.  Création automatique d’un profil Hermes en clonant le template.
2. **Recherche** : génération de requêtes ciblées depuis l’ICP (prompts `icp_to_queries.md`), appel de l’API BeReach pour récupérer des prospects potentiels.
3. **Enrichissement et scoring** : enrichissement des profils via BeReach, calcul d’une note (0–100) selon quatre composantes (poste, entreprise, activité, signaux) décrit dans `lead_scoring.md`.
4. **Filtrage** : rejet immédiat des leads en dessous de 75.  Seuls les leads qualifiés sont sauvegardés dans Supabase et reçoivent une demande de connexion.
5. **Connexion sans note** : envoi d’une invitation LinkedIn sans message (motif : limitation sur les comptes gratuits).  Si la connexion est acceptée, envoi d’un message d’introduction (`first_message.md`), suivi d’un relance éventuelle (`follow_up.md`).
6. **QA et rapport** : après chaque batch, passage par le sous‑agent QA (`qa_review.md`) pour vérifier la cohérence.  À la fin de la journée, génération d’un rapport (`daily_report.md`).

## C. Contraintes et décisions clés

- **Supabase** : choisi comme CRM pour sa simplicité et son interface SQL.  Les variables d’environnement incluent `SUPABASE_URL` et `SUPABASE_ANON_KEY`.
- **Seuil de qualification** : fixé à 75/100.  Modifiable via `.env`.  Les leads en dessous ne sont pas stockés.
- **Note dans la connexion** : absente pour contourner la limite de 3 notes par jour sur les comptes LinkedIn gratuits.
- **Contrôle qualité** : indispensable pour éviter d’enregistrer des leads incorrects ou non pertinents.  Un sous‑agent QA évalue les données avant insertion finale.
- **Multi‑compte** : non géré dans la version initiale ; chaque profil représente un seul compte LinkedIn.  Pour les agences, il suffira de créer autant de profils que de comptes.

## D. Roadmap suggérée

1. **MVP** (Semaine 1–2)
   - Mise en place du template de profil (`template_prospection`).
   - Dashboard minimal pour onboarding (nom du client, ICP, offre, clés API).
   - Appel de l’API BeReach et calcul du score avec rejet sous 75.
   - Sauvegarde Supabase et envoi d’invitations sans note.
   - Rapports quotidiens.

2. **Qualité et IA (Semaine 3–4)**
   - Ajout du sous‑agent QA et des messages après acceptation et de suivi.
   - Amélioration des prompts de recherche et du scoring.
   - Intégration des signaux additionnels de BeReach (job change, likes, etc.).

3. **Évolutions futures**
   - Support multi‑compte / multi‑canal (email en plus de LinkedIn).
   - Tableaux de bord avancés (A/B testing, analyse de campagne).
   - Enrichissement des leads via d’autres sources (Apollo, Clearbit, etc.).
   - Feedback loop automatique pour ajuster le scoring selon le taux de réponse.

## E. Questions en suspens pour validation

1. **Signaux supplémentaires** : quels signaux d’intention faut‑il intégrer en priorité ?  L’usage des données BeReach est‑il suffisant ou faut‑il connecter d’autres sources ?
2. **Traitement des réponses** : comment gérer la suite de la conversation une fois le prospect engagé ?  Souhaite‑t‑on automatiser ce volet ou rester en main humaine ?
3. **Interfaçage CRM** : l’export Supabase vers un CRM tiers (HubSpot, Salesforce) est‑il nécessaire dès le départ ?
4. **Évolution vers multi‑compte** : quand planifier l’implémentation d’un système multi‑compte dans le même profil ?  Quels défis (rate limit, warm‑up) cela pose‑t‑il ?

---

**Cette revue est destinée à être commentée et ajustée.  N’hésitez pas à annoter les sections (conserver / modifier / supprimer) afin d’orienter le développement.**
