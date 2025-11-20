# Configuration Dashboard Grafana

## Services actifs

- **API Dashboard**: http://localhost:8000
- **Grafana**: http://localhost:3000 (admin/admin)
- **Postgres**: localhost:5432

## Étape 1: Ajouter la source de données JSON API

1. Ouvrir Grafana: http://localhost:3000
2. Login: `admin` / `admin` (changer au premier login)
3. Menu → **Connections** → **Data sources** → **Add data source**
4. Rechercher et sélectionner **JSON API** (si pas disponible, installer le plugin manuellement)
5. Configuration:
   - **Name**: `Dashboard API`
   - **URL**: `http://host.containers.internal:8000` (ou `http://localhost:8000` si Grafana local)
   - **Auth**: None
   - Cliquer **Save & Test**

### Installation manuelle du plugin JSON API (si nécessaire)

```bash
podman exec -it grafana grafana-cli plugins install marcusolsson-json-datasource
podman restart grafana
```

## Étape 2: Créer les panels

### Panel 1: Évolution Airflow sur 12 mois

- **Type**: Time series
- **Data source**: Dashboard API
- **Query**:
  - Path: `/airflow/evolution`
  - Fields: `date` (time), `value` (number), `rolling_28d_mean` (number)
- **Transform**:
  - Convert field type: `date` → Time
  - Rename: `value` → "Recherches Airflow", `rolling_28d_mean` → "Moyenne 28j"
- **Panel options**:
  - Title: "Évolution Airflow (12 mois)"
  - Legend: Show, Bottom
  - Line width: 2
  - Fill opacity: 10%

### Panel 2: Pics Databricks + Dates

- **Type**: Table
- **Data source**: Dashboard API
- **Query**:
  - Path: `/databricks/peaks`
  - Fields: `date`, `peak_value`, `z_score`
- **Transform**:
  - Convert field type: `date` → Time
- **Panel options**:
  - Title: "Pics Databricks détectés"
  - Column width: Auto
  - Cell display mode: Color text (z_score > 2 → Orange, > 3 → Red)

### Panel 3: Map des recherches Collibra

- **Type**: Geomap (ou Table si carte indisponible)
- **Data source**: Dashboard API
- **Query**:
  - Path: `/collibra/map`
  - Fields: `region` (string), `value` (number)
- **Panel options (Table)**:
  - Title: "Top pays - Recherches Collibra"
  - Sort by: `value` descending
  - Bar gauge: Value (0-100)

**Alternative Geomap** (si plugin worldmap disponible):
- Mapping: `region` → Location name
- Value: `value`
- Color scheme: Blues

### Panel 4: Comparaison FR vs USA

- **Type**: Time series
- **Data source**: Dashboard API
- **Query**:
  - Path: `/data-engineering/fr-vs-us`
  - Fields: `date`, `fr_value`, `us_value`, `diff`
- **Transform**:
  - Convert field type: `date` → Time
- **Display**:
  - Series 1: `fr_value` → Line (Blue) "France"
  - Series 2: `us_value` → Line (Red) "USA"
  - Series 3: `diff` → Bars (Gray, secondary Y-axis) "Écart"
- **Panel options**:
  - Title: "Data Engineering: France vs USA"
  - Legend: Show
  - Dual Y-axis

### Panel 5: Corrélation Data Quality / Événements

- **Type**: Stat (pour metrics) + Table (pour sample matches)
- **Data source**: Dashboard API
- **Query**:
  - Path: `/data-quality/events-correlation`

**Panel 5A: Stat**
- Extract field: `metrics.match_rate`
- Display: Percentage
- Title: "Taux de corrélation DQ/Événements"
- Thresholds: < 30% Red, 30-60% Orange, > 60% Green

**Panel 5B: Table**
- Extract: `sample_matches` array
- Columns: `peak_date`, `event_date`, `event_type`, `score`
- Title: "Événements corrélés (échantillon)"

### Panel 6: Prédiction Databricks

- **Type**: Time series
- **Data source**: Dashboard API
- **Query**:
  - Path: `/databricks/forecast`
  - Fields: `date`, `forecast`, `lower80`, `upper80`
- **Transform**:
  - Convert field type: `date` → Time
- **Display**:
  - Main series: `forecast` → Line (Blue) "Prévision"
  - Band: `lower80` / `upper80` → Area fill (Light blue) "Intervalle 80%"
- **Panel options**:
  - Title: "Prédiction Databricks (30 jours)"
  - Legend: Show
  - Fill area between lower/upper

## Étape 3: Disposition du dashboard

Organiser les panels en grille 2x3:

```
┌─────────────────┬─────────────────┐
│  Airflow (1)    │  Databricks (6) │
│  Evolution      │  Forecast       │
├─────────────────┼─────────────────┤
│  FR vs USA (4)  │  Collibra Map(3)│
│                 │                 │
├─────────────────┴─────────────────┤
│  Corrélation DQ/Events (5)        │
│  Stat + Table                     │
├───────────────────────────────────┤
│  Databricks Peaks Table (2)       │
└───────────────────────────────────┘
```

## Étape 4: Variables & Refresh

- **Auto-refresh**: 5 minutes
- **Time range**: Last 12 months (ou custom pour forecast)
- **Variables optionnelles**:
  - `$z_threshold` pour ajuster détection peaks
  - `$forecast_horizon` pour prédictions

## Export du dashboard

Une fois configuré:
1. Menu dashboard → **Share** → **Export**
2. Sauvegarder JSON: `dashboards/grafana_dashboard.json`
3. Commit au repo pour versioning

## Tests de validation

```powershell
# Test tous les endpoints
curl http://localhost:8000/airflow/evolution
curl http://localhost:8000/databricks/peaks
curl http://localhost:8000/collibra/map
curl http://localhost:8000/data-engineering/fr-vs-us
curl http://localhost:8000/data-quality/events-correlation
curl http://localhost:8000/databricks/forecast
```

## Troubleshooting

### Plugin JSON API non trouvé
```bash
# Installer manuellement
podman exec -it grafana grafana-cli plugins install marcusolsson-json-datasource
podman restart grafana
```

### API non accessible depuis Grafana
- Vérifier que l'API tourne: `curl http://localhost:8000/health`
- Dans data source, utiliser `http://host.containers.internal:8000` au lieu de `localhost`
- Ou lancer Grafana avec `--add-host=host.docker.internal:host-gateway`

### Données vides
- Vérifier que les fichiers analytics existent: `ls data/processed/analytics/`
- Relancer transformations: `python airflow/dags/transform_trends.py`
- Relancer forecast: `python ml/databricks_forecast.py`
