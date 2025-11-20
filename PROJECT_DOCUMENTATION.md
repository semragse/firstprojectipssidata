# 📊 Projet DataLake Vendredi - Analyse des Tendances AI

## 🎯 Vue d'ensemble

Ce projet analyse les tendances Google Trends pour les technologies AI/Data Science, détecte les pics d'intérêt, corrèle avec des événements, et génère des prévisions. Le tout est visualisé dans un dashboard Grafana interactif.

**Technologies analysées:** ChatGPT, AI, Machine Learning, Python, Data Science

---

## 🏗️ Architecture du Projet

```
┌─────────────────────────────────────────────────────────────────┐
│                    GRAFANA DASHBOARD                             │
│                    (Port 3000)                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ ChatGPT  │ │ AI Peaks │ │  Python  │ │    ML    │          │
│  │Evolution │ │          │ │   Map    │ │ FR vs US │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────────────────────────────┐            │
│  │Data Sci. │ │      AI Forecast                 │            │
│  │ Correl.  │ │      (30 jours)                  │            │
│  └──────────┘ └──────────────────────────────────┘            │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP requests (JSON API)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI SERVER                                │
│                    (Port 8000)                                   │
│                                                                  │
│  Endpoints:                                                      │
│  • GET /chatgpt/evolution       → Évolution 12 mois             │
│  • GET /ai/peaks                → Pics détectés                 │
│  • GET /python/map              → Distribution géographique     │
│  • GET /machine-learning/fr-vs-us → Comparaison FR/USA         │
│  • GET /data-science/events-correlation → Corrélation          │
│  • GET /ai/forecast             → Prédictions 30 jours          │
│  • GET /health                  → Health check                  │
└────────────────────────┬────────────────────────────────────────┘
                         │ Lecture CSV
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              DATA PROCESSING PIPELINE                            │
│                                                                  │
│  1. EXTRACTION (extract_trends.py)                              │
│     └─> Google Trends API → data/raw/                           │
│         • google_trends_daily_YYYYMMDD_YYYYMMDD.csv             │
│                                                                  │
│  2. TRANSFORMATION (transform_trends.py)                         │
│     └─> Analyse & Agrégations → data/processed/analytics/       │
│         • chatgpt_evolution.csv                                  │
│         • chatgpt_evolution_series.csv                           │
│         • ai_peaks.csv                                           │
│         • python_top_countries.csv                               │
│         • machine_learning_fr_us.csv                             │
│         • data_science_peaks.csv                                 │
│                                                                  │
│  3. PRÉVISION (ml/databricks_forecast.py)                        │
│     └─> SARIMAX Model → data/processed/analytics/               │
│         • ai_forecast.csv                                        │
│                                                                  │
│  4. CORRÉLATION (correlation_events.py, correlation_tools.py)   │
│     └─> Analyse statistique → data/processed/analytics/         │
│         • data_quality_event_correlation.json                    │
│         • data_quality_tools_correlation.json                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Structure des Fichiers

```
DataLakeVendredi/
│
├── airflow/                      # Pipeline orchestration
│   └── dags/
│       ├── extract_trends.py     # Extraction Google Trends
│       ├── transform_trends.py   # Transformations & analytics
│       ├── correlation_events.py # Corrélation pics/événements
│       ├── correlation_tools.py  # Corrélation DQ/outils
│       └── trends_utils.py       # Utilitaires communs
│
├── ml/                           # Machine Learning
│   └── databricks_forecast.py    # Modèle de prévision SARIMAX
│
├── dashboards/                   # API & Dashboards
│   ├── api_server.py            # FastAPI REST API
│   ├── grafana_ai_dashboard.json # Export dashboard Grafana
│   ├── NEW_DASHBOARD_SETUP.md   # Guide de configuration
│   └── requirements.txt         # Dépendances API
│
├── data/
│   ├── raw/                     # Données brutes Google Trends
│   │   └── google_trends_daily_*.csv
│   │
│   └── processed/
│       └── analytics/           # Fichiers analytics générés
│           ├── chatgpt_evolution_series.csv
│           ├── ai_peaks.csv
│           ├── python_top_countries.csv
│           ├── machine_learning_fr_us.csv
│           ├── data_science_peaks.csv
│           ├── ai_forecast.csv
│           └── *_correlation.json
│
├── monitoring/                  # Alertes & monitoring
│   └── alerts.py               # Callbacks Airflow
│
├── docker-compose.yml          # Orchestration des services
├── requirements.txt            # Dépendances Python
└── README.md                  # Documentation principale
```

---

## 🔧 Composants Techniques

### 1. **Extraction de Données (extract_trends.py)**

**Rôle:** Récupère les données de Google Trends via PyTrends

**Fonctionnement:**
- Connexion à l'API Google Trends (avec contournement SSL pour proxy corporate)
- Extraction des 5 mots-clés: ChatGPT, AI, Machine Learning, Python, Data Science
- Timeframe: 12 derniers mois (granularité hebdomadaire)
- Export en CSV dans `data/raw/`

**Paramètres:**
```python
Keywords: ["ChatGPT", "AI", "Machine Learning", "Python", "Data Science"]
Timeframe: "today 12-m"
Geo: Multi-régions (Worldwide, FR, US, par pays)
```

**Commande:**
```bash
python airflow/dags/extract_trends.py --insecure --keywords ChatGPT AI "Machine Learning" Python "Data Science"
```

---

### 2. **Transformation & Analytics (transform_trends.py)**

**Rôle:** Transforme les données brutes en métriques exploitables

**Analyses effectuées:**

#### A. **Évolution temporelle (ChatGPT)**
- Calcul des statistiques: first_value, last_value, % change, mean, median
- Rolling mean 28 jours pour lisser les tendances
- Export: `chatgpt_evolution.csv` + `chatgpt_evolution_series.csv`

#### B. **Détection de pics (AI, Data Science)**
- Algorithme: Z-score avec fenêtre glissante (4 semaines)
- Seuil: z_threshold = 1.5 (configurable)
- Formule: `z = (valeur - rolling_mean) / rolling_std`
- Export: `ai_peaks.csv`, `data_science_peaks.csv`

#### C. **Distribution géographique (Python)**
- Extraction des top 10 pays par volume de recherche
- Normalisation sur 100 (max = 100)
- Export: `python_top_countries.csv`

#### D. **Comparaison géographique (Machine Learning)**
- Comparaison France vs USA
- Calcul de l'écart (diff = fr_value - us_value)
- Export: `machine_learning_fr_us.csv`

**Commande:**
```bash
python airflow/dags/transform_trends.py
```

---

### 3. **Prévisions (ml/databricks_forecast.py)**

**Rôle:** Génère des prédictions sur 30 jours

**Modèle utilisé:** SARIMAX (Seasonal AutoRegressive Integrated Moving Average with eXogenous factors)

**Paramètres du modèle:**
```python
order=(1, 1, 1)           # (p, d, q) - AR, Differencing, MA
seasonal_order=(1, 0, 1, 7) # (P, D, Q, s) - Seasonal components
horizon=30                 # Jours de prévision
confidence=80%            # Intervalle de confiance
```

**Fallback:** Si SARIMAX échoue, utilisation d'un modèle naïf saisonnier (répétition des 7 derniers jours)

**Output:**
```csv
date,forecast,lower80,upper80
2025-11-21,85.3,78.1,92.5
2025-11-22,87.2,79.8,94.6
...
```

**Commande:**
```bash
python ml/databricks_forecast.py
```

---

### 4. **Corrélation (correlation_events.py & correlation_tools.py)**

#### A. **Corrélation Pics / Événements**
- Compare les pics détectés avec des événements calendaires
- Fenêtre de matching: ±7 jours (configurable)
- Score de corrélation basé sur la proximité temporelle
- Export: `data_quality_event_correlation.json`

#### B. **Corrélation Data Quality / Outils**
- Analyse de cross-corrélation entre "Data quality" et outils (Collibra, Talend, etc.)
- Calcul du coefficient de corrélation de Pearson
- Détection du lag optimal (avance/retard)
- Export: `data_quality_tools_correlation.json`

**Résultats obtenus:**
```json
{
  "collibra": {"max_corr": 0.928, "lag_at_max_corr": 0},
  "soda": {"max_corr": 0.872, "lag_at_max_corr": -4},
  "informatica": {"max_corr": 0.709, "lag_at_max_corr": -30}
}
```

**Commande:**
```bash
python airflow/dags/correlation_tools.py
```

---

### 5. **API REST (dashboards/api_server.py)**

**Rôle:** Expose les données analytics via HTTP pour Grafana

**Framework:** FastAPI + Uvicorn

**Endpoints:**

| Endpoint | Méthode | Description | Données retournées |
|----------|---------|-------------|-------------------|
| `/chatgpt/evolution` | GET | Évolution ChatGPT 12 mois | `[{date, value, rolling_28d_mean}]` |
| `/ai/peaks` | GET | Pics AI détectés | `[{date, peak_value, z_score}]` |
| `/python/map` | GET | Top pays Python | `[{region, value}]` |
| `/machine-learning/fr-vs-us` | GET | Comparaison FR vs USA | `[{date, fr_value, us_value, diff}]` |
| `/data-science/events-correlation` | GET | Corrélation événements | `{metrics: {...}, sample_matches: [...]}` |
| `/ai/forecast` | GET | Prévisions AI 30j | `[{date, forecast, lower80, upper80}]` |
| `/health` | GET | Health check | `{status: "ok"}` |

**Démarrage:**
```bash
python -m uvicorn dashboards.api_server:app --host 0.0.0.0 --port 8000
```

**Test:**
```bash
curl http://localhost:8000/chatgpt/evolution
```

---

### 6. **Dashboard Grafana**

**Configuration:** JSON API Plugin (marcusolsson-json-datasource)

**Data Source:**
- Name: `Dashboard API`
- URL: `http://10.79.36.27:8000` (ou `localhost:8000`)
- Auth: None

**6 Panels créés:**

#### Panel 1: ChatGPT Evolution
- **Type:** Time series
- **Données:** 53 points hebdomadaires
- **Résultat:** Croissance de 96% (51 → 100)
- **Visualisation:** 2 courbes (valeur + moyenne mobile 28j)

#### Panel 2: AI Peaks
- **Type:** Table
- **Données:** Pics avec z-score > 1.5
- **Colonnes:** date, peak_value, z_score
- **Status:** Vide (pas d'anomalies détectées)

#### Panel 3: Python Top Countries
- **Type:** Table
- **Données:** Top 10 pays
- **Résultat:** China (100), Eritrea (44), Singapore (34)
- **Tri:** Par score décroissant

#### Panel 4: Machine Learning FR vs USA
- **Type:** Time series
- **Données:** 53 semaines de comparaison
- **Résultat:** France domine USA de ~23 points
- **Visualisation:** 3 courbes (FR, US, Écart)

#### Panel 5: Data Science Correlation
- **Type:** Stat (match_rate) + Table (événements)
- **Résultat:** 0% (pas de pics = pas de corrélation)
- **Interprétation:** Données stables sans anomalies

#### Panel 6: AI Forecast
- **Type:** Time series avec bandes de confiance
- **Données:** 30 jours de prévision
- **Visualisation:** Ligne de prévision + intervalle 80%

---

## 🚀 Installation & Déploiement

### Prérequis
- Python 3.11+ (3.13 pour virtual env)
- Podman (ou Docker)
- Git

### Installation

```bash
# 1. Cloner le repo
git clone https://github.com/semragse/Correlation-DQ-outilsdeDQ.git
cd Correlation-DQ-outilsdeDQ

# 2. Créer un environnement virtuel
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Installer les dépendances
pip install -r requirements.txt
pip install -r dashboards/requirements.txt

# 4. Lancer Grafana (Podman)
podman run -d --name grafana -p 3000:3000 grafana/grafana:latest

# 5. Installer le plugin JSON API
podman exec -it grafana grafana-cli plugins install marcusolsson-json-datasource
podman restart grafana

# 6. Lancer l'API
python -m uvicorn dashboards.api_server:app --host 0.0.0.0 --port 8000
```

### Génération des données

```bash
# Extraction Google Trends
python airflow/dags/extract_trends.py --insecure --keywords ChatGPT AI "Machine Learning" Python "Data Science"

# Transformation & analytics
python airflow/dags/transform_trends.py

# Prévisions
python ml/databricks_forecast.py

# Corrélations
python airflow/dags/correlation_tools.py
```

### Configuration Grafana

1. Accéder à Grafana: http://localhost:3000 (admin/admin)
2. Ajouter la data source:
   - Type: JSON API
   - URL: http://10.79.36.27:8000 (ou localhost:8000)
3. Importer le dashboard: `dashboards/grafana_ai_dashboard.json`
4. Ou créer manuellement avec `dashboards/NEW_DASHBOARD_SETUP.md`

---

## 📊 Résultats & Insights

### Métriques Clés

| Métrique | Valeur | Insight |
|----------|--------|---------|
| **ChatGPT Growth** | +96% | Explosion des recherches ChatGPT en 12 mois (51→100) |
| **Python Top Country** | China (100) | Chine domine largement les recherches Python |
| **ML FR vs USA** | FR +23 pts | France plus intéressée par Machine Learning que USA |
| **Collibra Correlation** | 0.928 | Forte corrélation avec "Data quality" (recherches simultanées) |
| **AI Peaks Detected** | 0 | Données stables sans anomalies significatives |
| **Forecast Horizon** | 30 jours | Prévisions avec intervalle de confiance 80% |

### Interprétations

1. **ChatGPT Phenomenon:** Croissance explosive reflétant l'adoption massive de l'IA générative
2. **Geographic Insights:** Chine leader Python, France avancée en ML vs USA
3. **Tool Correlation:** Collibra fortement associé aux recherches "Data quality"
4. **Stable Trends:** Pas de pics viraux = intérêt constant et prévisible

---

## 🔐 Sécurité & SSL

**Problème:** Proxy corporate intercepte les certificats SSL

**Solution:** Contournement avec `--insecure` flag

```python
# Dans extract_trends.py et transform_trends.py
requests_args = {"verify": False}  # Désactive la vérification SSL
```

**Production:** Utiliser un bundle CA avec `--ca-bundle /path/to/ca.crt`

---

## 🛠️ Dépendances Principales

| Package | Version | Usage |
|---------|---------|-------|
| `pandas` | 2.2.3 | Manipulation de données |
| `pytrends` | 4.9.2 | API Google Trends |
| `statsmodels` | 0.14.5 | Modèle SARIMAX |
| `fastapi` | 0.115.4 | API REST |
| `uvicorn` | 0.32.1 | Serveur ASGI |
| `scipy` | 1.14.1 | Statistiques |
| `numpy` | 2.1.3 | Calculs numériques |

---

## 📈 Améliorations Futures

### Court Terme
- [ ] Ajouter d'autres mots-clés AI (GPT-4, Claude, Gemini)
- [ ] Implémenter un cache Redis pour l'API
- [ ] Alertes Slack sur pics détectés
- [ ] Export PDF des dashboards

### Moyen Terme
- [ ] Pipeline Airflow avec scheduling automatique
- [ ] Base de données PostgreSQL pour historisation
- [ ] Authentification API (JWT)
- [ ] Tests unitaires & CI/CD

### Long Terme
- [ ] Modèles de prévision avancés (Prophet, LSTM)
- [ ] Analyse de sentiment sur réseaux sociaux
- [ ] Dashboard mobile (React Native)
- [ ] Multi-tenancy pour plusieurs projets

---

## 🐛 Troubleshooting

### API inaccessible depuis Grafana
**Symptôme:** `Bad Gateway` ou `Connection refused`

**Solution:**
```bash
# Vérifier que l'API écoute sur 0.0.0.0
netstat -an | Select-String "8000"

# Utiliser l'IP de l'hôte Windows (pas localhost)
ipconfig | Select-String "IPv4"
# Utiliser cette IP dans Grafana: http://10.79.36.27:8000
```

### Plugin JSON API introuvable
**Symptôme:** Plugin non disponible dans Grafana

**Solution:**
```bash
# Installation manuelle
podman exec -it grafana wget --no-check-certificate https://github.com/marcusolsson/grafana-json-datasource/releases/download/v1.3.18/marcusolsson-json-datasource-1.3.18.zip -O /tmp/plugin.zip
podman exec -it grafana unzip /tmp/plugin.zip -d /var/lib/grafana/plugins/
podman restart grafana
```

### Données vides dans les panels
**Symptôme:** `No data` dans Grafana

**Solutions:**
1. Vérifier JSONPath: doit commencer par `$[*]` pour tableaux
2. Vérifier Type de champ (Time pour dates, Number pour valeurs)
3. Tester l'endpoint: `curl http://localhost:8000/chatgpt/evolution`
4. Regénérer les données: `python airflow/dags/transform_trends.py`

### Google Trends rate limiting
**Symptôme:** `TooManyRequestsError: code 429`

**Solution:** Attendre 30-60 secondes entre les requêtes
```bash
Start-Sleep -Seconds 30
python airflow/dags/extract_trends.py --insecure
```

---

## 📝 Licence & Auteurs

**Projet:** Correlation DQ / Outils de DQ  
**Auteur:** Saad-Eddine GARMES  
**Organisation:** Amadeus  
**Repository:** https://github.com/semragse/Correlation-DQ-outilsdeDQ  
**Date:** Novembre 2025  

---

## 📞 Support

Pour toute question ou problème:
1. Consulter les fichiers `GRAFANA_SETUP.md` et `NEW_DASHBOARD_SETUP.md`
2. Vérifier les logs: `Get-Content data/logs/*.log`
3. Tester les endpoints API: `curl http://localhost:8000/health`
4. Ouvrir une issue sur GitHub

---

**🎉 Dashboard opérationnel avec données AI réelles et prévisions sur 30 jours!**
