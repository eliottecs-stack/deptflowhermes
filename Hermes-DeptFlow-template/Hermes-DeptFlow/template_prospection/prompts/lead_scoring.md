# Prompt — Lead scoring

Score un lead sur 100 uniquement avec les données disponibles.

Dimensions :
- ICP fit : 35
- Account fit : 20
- Buying intent : 20
- Activity : 10
- Outreach feasibility : 10
- Data confidence : 5

Règles :
- Ne pas inventer de signal.
- Si les données sont insuffisantes, réduire `data_confidence`.
- Si une exclusion ICP est détectée, rejeter.
- Expliquer les raisons du score.
