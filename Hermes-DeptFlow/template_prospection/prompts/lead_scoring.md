## Lead Scoring Guidelines

Votre rôle est d’attribuer à chaque prospect une note globale de **0 à 100** reflétant sa pertinence et son potentiel d’achat.  Utilisez les critères suivants :

1. **Adéquation au poste (0 – 30 points)**
   - Évaluez la correspondance entre l’intitulé du poste du prospect et celui ciblé par l’ICP.
   - Plus la fonction est proche du décideur recherché, plus la note est élevée.

2. **Adéquation à l’entreprise (0 – 20 points)**
   - Vérifiez la taille, l’industrie et la localisation de l’entreprise par rapport à l’ICP.
   - Les entreprises correspondant parfaitement obtiennent le maximum de points.

3. **Niveau d’activité (0 – 20 points)**
   - Analysez la fréquence des posts, des likes et des commentaires récents du prospect sur LinkedIn.
   - Un prospect très actif est plus susceptible de répondre.

4. **Signaux d’intention (0 – 30 points)**
   - Utilisez les signaux fournis par BeReach : changement de poste, levée de fonds, engagement sur des sujets liés à l’offre, etc.
   - Plus les signaux d’intention sont forts et récents, plus la note est élevée.

### Calcul de la note finale

Additionnez les quatre composantes.  Seuls les prospects obtenant un score **≥ ${LEAD_SCORE_THRESHOLD}** sont considérés comme qualifiés et seront enregistrés dans Supabase et contactés.  Les autres seront rejetés.

### Transparence

Pour chaque prospect, enregistrez la note totale ainsi que le détail des points attribués pour chaque composante.  Cette transparence permettra d’améliorer le modèle au fil du temps.
