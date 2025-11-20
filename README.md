# Correlation-DQ-outilsdeDQ

**Analyse spatio-temporelle des tendances Data Quality et corrélation avec les outils de gouvernance**

Pipeline complet d'extraction Google Trends, transformations analytics, corrélation événements/outils, prédiction ML et dashboards interactifs.

## 🎯 Fonctionnalités

✅ **Extraction automatique** Google Trends (Airflow, Databricks, Collibra, Data Engineering, Data Quality)  
✅ **Transformations & Analytics** (évolutions, pics, comparaisons géographiques)  
✅ **Corrélation** pics Data Quality avec événements externes et outils concurrents  
✅ **Prédiction** Databricks via SARIMAX (30 jours avec intervalles de confiance)  
✅ **Monitoring** alertes Slack + logs structurés + métriques Stats  
✅ **Dashboard API** FastAPI exposant tous les endpoints analytics  
✅ **Grafana** dashboards interactifs (6 panels)  

## 📁 Structure du projet

```
DataLakeVendredi/
├── airflow/
│   └── dags/
│       ├── google_trends_pipeline.py          # Extraction quotidienne multi-keywords
│       ├── transform_trends.py                # Transformations analytics
│       ├── correlation_events.py              # Corrélation DQ/événements
│       ├── correlation_tools.py               # Corrélation DQ/outils
│       ├── databricks_forecast_pipeline.py    # DAG prédiction
│       ├── extract_trends.py                  # Script standalone extraction
│       └── trends_utils.py                    # Utilitaires locaux
├── data/
│   ├── raw/                                   # Données brutes Google Trends (CSV)
│   └── processed/
│       ├── analytics/                         # Fichiers analytics générés
│       │   ├── airflow_evolution.csv
│       │   ├── databricks_peaks.csv
│       │   ├── collibra_top_countries.csv
│       │   ├── data_engineering_fr_us.csv
│       │   ├── data_quality_event_correlation.json
│       │   ├── data_quality_tools_correlation.json
│       │   └── databricks_forecast.csv
│       └── google_trends_all_daily_*.csv      # Merge quotidien
├── ml/
│   └── databricks_forecast.py                 # Modèle SARIMAX + fallback naïf
├── monitoring/
│   └── alerts.py                              # Callbacks Airflow (Slack/logs)
├── dashboards/
│   ├── api_server.py                          # FastAPI avec 7 endpoints
│   ├── requirements.txt                       # Dépendances API standalone
│   └── GRAFANA_SETUP.md                       # Guide configuration Grafana
├── docker-compose.yml                         # Stack Airflow + Postgres + API + Grafana
└── requirements.txt                           # Dépendances globales

```

## 🚀 Démarrage rapide

### Prérequis

- Python 3.11+ (3.13 pour API, 3.8-3.11 pour Airflow)
- Podman ou Docker
- Git

### Installation

```powershell
# Cloner le repo
git clone https://github.com/semragse/Correlation-DQ-outilsdeDQ.git
cd Correlation-DQ-outilsdeDQ

# Option 1: Lancer avec Podman Compose (recommandé)
podman-compose up -d postgres
podman-compose up -d airflow-webserver airflow-scheduler

# Option 2: Installation locale
pip install -r requirements.txt
```

### Lancer les services

```powershell
# API Dashboard (locale)
pip install -r dashboards/requirements.txt
python -m uvicorn dashboards.api_server:app --host 0.0.0.0 --port 8000

# Grafana (container)
podman run -d --name grafana -p 3000:3000 grafana/grafana:latest

# Postgres (container)
podman run -d --name postgres -p 5432:5432 \
  -e POSTGRES_USER=airflow \
  -e POSTGRES_PASSWORD=airflow \
  -e POSTGRES_DB=airflow \
  postgres:15
```

### Accès aux interfaces

- **Airflow**: http://localhost:8080 (airflow/airflow)
- **Grafana**: http://localhost:3000 (admin/admin)
- **API Swagger**: http://localhost:8000/docs

## 📊 Endpoints API Dashboard

| Endpoint | Description |
|----------|-------------|
| `GET /airflow/evolution` | Série temporelle Airflow 12 mois + rolling mean 28j |
| `GET /databricks/peaks` | Pics détectés (date, valeur, z-score) |
| `GET /collibra/map` | Top pays recherches Collibra |
| `GET /data-engineering/fr-vs-us` | Comparaison France vs USA |
| `GET /data-quality/events-correlation` | Metrics + matches DQ/événements |
| `GET /databricks/forecast` | Prédiction 30j + intervalles 80% |
| `GET /health` | Santé API |

## 🔧 Configuration Airflow

### Variables d'environnement (docker-compose.yml)

```yaml
AIRFLOW__CORE__EXECUTOR: LocalExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
AIRFLOW__CORE__FERNET_KEY: <générer avec cryptography.fernet>
AIRFLOW__WEBSERVER__SECRET_KEY: <secret random>
```

### DAGs disponibles

1. **google_trends_pipeline** (quotidien 03:00): Extraction multi-keywords + merge
2. **databricks_forecast_pipeline** (quotidien 05:00): Génération prédictions
3. **transform_trends** (manuel): Analytics batch complet
4. **correlation_events** (manuel): Matching peaks/événements
5. **correlation_tools** (manuel): Comparaison DQ vs outils

## 📈 Dashboards Grafana

Voir [dashboards/GRAFANA_SETUP.md](dashboards/GRAFANA_SETUP.md) pour configuration complète.

**6 panels implémentés:**
1. Évolution Airflow (time series)
2. Pics Databricks (table + annotations)
3. Map Collibra (geomap/table)
4. FR vs USA (dual axis)
5. Corrélation DQ/événements (stat + table)
6. Prédiction Databricks (forecast + confidence bands)

## 🧪 Tests & Validation

```powershell
# Test extraction manuelle
python airflow/dags/extract_trends.py --keyword "Airflow" --days 30

# Test transformations
python airflow/dags/transform_trends.py

# Test forecast
python ml/databricks_forecast.py

# Test corrélation outils
python airflow/dags/correlation_tools.py

# Vérifier API
curl http://localhost:8000/health
curl http://localhost:8000/airflow/evolution | jq '.[:3]'
```

## 🔍 Analyses disponibles

### Évolution temporelle
- Rolling mean 28 jours
- Détection pics (z-score > threshold)
- Tendance weekly/monthly

### Comparaisons géographiques
- Top 10 pays par keyword
- France vs USA Data Engineering
- Distribution mondiale Collibra

### Corrélations
- **Data Quality ↔ Événements**: Matching ±3 jours avec scoring
- **Data Quality ↔ Outils**: Cross-correlation avec lag detection (Collibra, Talend, Informatica, etc.)
- Métriques: match_rate, mean_score, lead_ratio

### Prédictions
- SARIMAX (1,1,1)(1,0,1,7) pour Databricks
- Fallback naïf saisonnier (repeat last 7 days)
- Intervalles de confiance 80%

## 🛠️ Troubleshooting

### Certificat SSL
Si erreur `certificate signed by unknown authority`:
```python
# Dans extract_trends.py, ajouter:
pytrends = TrendReq(hl='en-US', tz=360, requests_args={'verify': False})
```

### Parquet engine missing
Installer pyarrow:
```powershell
pip install pyarrow
```

### Airflow incompatible Python 3.13
Utiliser Python 3.11 pour Airflow, 3.13 pour API standalone.

### Grafana plugin JSON API
```bash
podman exec -it grafana grafana-cli plugins install marcusolsson-json-datasource
podman restart grafana
```

## 📝 Monitoring

- **Alertes**: Slack webhook (monitoring/alerts.py)
- **Logs structurés**: `monitoring/failures.jsonl`
- **Métriques**: Stats.incr() dans DAGs (trends_extract_success, trends_merge_*, etc.)
- **Prometheus/Grafana** (optionnel): Ajouter statsd_exporter dans docker-compose

## 🤝 Contribution

```powershell
# Créer branche feature
git checkout -b feature/nom-feature

# Commit changements
git add .
git commit -m "feat: description"

# Push & PR
git push origin feature/nom-feature
```

## 📄 Licence

MIT

## 👤 Auteur

Saad-Eddine GARMES  
GitHub: [@semragse](https://github.com/semragse)

## 🔗 Liens utiles

- [Pytrends Documentation](https://github.com/GeneralMills/pytrends)
- [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [Grafana JSON API Plugin](https://grafana.com/grafana/plugins/marcusolsson-json-datasource/)
- [SARIMAX Statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html)
