# Data Pipeline Google Trends (Initialisation)

Structure minimale créée:
- airflow/
- data/raw
- data/processed
- ml/
- monitoring/
- dashboards/
- docker-compose.yml (à venir)
- requirements.txt (à venir)

Etapes suivantes:
1. Ajouter premier DAG d'extraction (pytrends)
2. Définir schéma stockage (Postgres / parquet)
3. Monitoring & dashboards
4. Modèle de prédiction

## Lancer Airflow (après creation docker-compose.yml)
```powershell
docker compose up -d
```

Générer une clé Fernet si nécessaire:
```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Ajouter la valeur dans un fichier `.env` (optionnel) ou directement dans compose.
