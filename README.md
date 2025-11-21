# 📊 Google Trends Analytics Pipeline - AI & Data Science

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![Grafana](https://img.shields.io/badge/Grafana-Latest-orange.svg)](https://grafana.com/)
[![Docker](https://img.shields.io/badge/Docker%2FPodman-Compatible-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Pipeline complet d'analyse des tendances Google pour l'IA et Data Science avec détection de corrélations et prévisions ML.

---

## 🎯 Aperçu du Projet

Ce projet implémente un **pipeline ETL complet** pour collecter, analyser et visualiser les tendances de recherche Google. Il permet de suivre l'évolution de l'intérêt public pour des technologies clés (ChatGPT, Python, Machine Learning, etc.) et d'identifier les corrélations entre keywords.

### 🔑 Fonctionnalités Clés

- ✅ **Extraction automatisée** depuis Google Trends API (PyTrends)
- ✅ **Analyse statistique avancée** (z-score, moyennes mobiles, corrélations)
- ✅ **Détection de corrélations temporelles** avec time-lag analysis
- ✅ **Prévisions Machine Learning** (modèles ARIMA)
- ✅ **Visualisation professionnelle** avec Grafana (7 dashboards)
- ✅ **Base de données PostgreSQL** (7 tables, 411 records)
- ✅ **Déploiement conteneurisé** (Docker/Podman)

### 📈 Résultats Principaux

| Métrique | Valeur | Insight |
|----------|--------|---------|
| **Croissance ChatGPT** | +86.5% | Explosion d'intérêt en 12 mois |
| **Corrélation ChatGPT ↔ Data Science** | 0.442 (p=0.017) | Significative, lag 4 semaines |
| **Early Adoption** | 4 semaines | Data Scientists ont adopté ChatGPT 1 mois avant le grand public |
| **Records analysés** | 411 | 12 mois de données historiques |

---

## 📸 Dashboards Grafana

### 1️⃣ Évolution ChatGPT (12 Mois)

![Evolution ChatGPT](img/Evolution%20ChatGPT12mois.png)

**Description:** Graphique temporel montrant la croissance explosive de ChatGPT avec moyenne mobile sur 28 jours. Visualisation claire de l'augmentation de +86.5% en un an (52 → 97).

---

### 2️⃣ Python - Top 10 Pays

![Python Top 10](img/Python%20-%20Top%2010%20Pays.png)

**Description:** Tableau classé des pays avec le plus d'intérêt pour Python. La Chine domine (100), suivie d'Érythrée (44) et Singapour (34). Montre la distribution géographique mondiale de l'intérêt Python.

---

### 3️⃣ Machine Learning France vs USA

![ML France vs USA](img/Machine%20Learning%20France%20vs%20USA.png)

**Description:** Comparaison temporelle de l'intérêt pour Machine Learning entre la France et les USA. Les USA montrent 2-3× plus d'intérêt avec un écart constant de -15 à -30 points.

---

### 4️⃣ Prévisions AI (30 Jours)

![Prevision AI](img/Prevision%20Ai%2030%20jours.png)

**Description:** Prédictions Machine Learning (ARIMA) pour les 30 prochains jours avec intervalles de confiance à 80%. Prévoit une croissance continue de 93 → 97 (+4%).

---

### 5️⃣ Comparaison Tous les Keywords

![Comparaison Keywords](img/Comparaison%20Tous%20les%20Keywords.png)

**Description:** Vue d'ensemble des 5 keywords principaux (AI, Machine Learning, Python, Data Science, ChatGPT). ChatGPT domine clairement avec la croissance la plus rapide.

---

### 6️⃣ Corrélation ChatGPT vs Data Science ⭐ NOUVEAU

![Correlation ChatGPT Data Science](img/Corrélation%20ChatGPT%20vs%20Data%20Science.png)

**Description:** Visualisation de la corrélation modérée positive (0.442) entre ChatGPT et Data Science. Montre que Data Science mène ChatGPT de 4 semaines, prouvant l'early adoption par les professionnels.

---

### 7️⃣ Table des Corrélations

![Table Correlations](img/Table%20des%20correlations.png)

**Description:** Tableau récapitulatif des analyses de corrélation avec coefficient, lag optimal, et significativité statistique. Confirmation que la corrélation ChatGPT-Data Science est statistiquement significative (✅).

---

## 🏗️ Architecture

```
┌─────────────────┐
│  Google Trends  │  ← Source de données
└────────┬────────┘
         │ API PyTrends
         ↓
┌─────────────────┐
│  Extraction     │  ← extract_to_postgres.py
│  Python Scripts │     load_csv_to_postgres.py
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Transformation  │  ← transform_to_postgres.py
│  & Analyse      │     analyze_correlation.py
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  PostgreSQL     │  ← 7 tables (411 records)
│  (Container)    │     trends_db
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│    Grafana      │  ← 7 dashboards interactifs
│  (Container)    │     http://localhost:3000
└─────────────────┘
```

---

## 🚀 Démarrage Rapide

### Prérequis

- **Podman** ou **Docker**
- **Python 3.13+**
- **Git**

### Installation en 5 Minutes

```powershell
# 1. Cloner le projet
git clone https://github.com/semragse/firstprojectipssidata.git
cd firstprojectipssidata

# 2. Démarrer les services
podman-compose -f docker-compose-simple.yml up -d

# 3. Charger les données (depuis CSV)
podman cp scripts/load_csv_to_postgres.py trends_postgres:/tmp/
podman cp -r data trends_postgres:/tmp/
podman exec -w /tmp trends_postgres python3 load_csv_to_postgres.py

# 4. Exécuter l'analyse de corrélation
podman cp scripts/analyze_correlation.py trends_postgres:/tmp/
podman exec -w /tmp trends_postgres python3 analyze_correlation.py

# 5. Accéder à Grafana
# http://localhost:3000
# Username: admin / Password: admin
```

### Configuration Grafana

1. **Data Source:**
   - Host: `trends_postgres:5432`
   - Database: `trends_db`
   - User: `trends_user`
   - Password: `trends_pass`

2. **Créer les dashboards** en suivant `GRAFANA_GUIDE.md`

---

## 📂 Structure du Projet

```
firstprojectipssidata/
├── docker-compose-simple.yml      # Configuration conteneurs
├── requirements-simple.txt        # Dépendances Python
├── scripts/
│   ├── init_db.sql               # Schéma base de données
│   ├── load_csv_to_postgres.py   # Chargement données CSV
│   ├── extract_to_postgres.py    # Extraction Google Trends
│   ├── transform_to_postgres.py  # Transformations & ML
│   ├── analyze_correlation.py    # Analyse corrélations ⭐
│   └── run_pipeline.ps1          # Orchestration complète
├── data/
│   ├── raw/                      # Données brutes CSV
│   └── processed/analytics/       # Résultats analyses
├── dashboards/
│   └── grafana_ai_dashboard.json # Dashboard Grafana
├── img/                          # Screenshots dashboards
├── DEPLOYMENT_GUIDE.md           # Guide déploiement détaillé
├── GRAFANA_GUIDE.md              # Configuration Grafana complète
└── PRESENTATION_PROJET.md        # Présentation académique
```

---

## 🔬 Technologies Utilisées

| Technologie | Version | Usage |
|-------------|---------|-------|
| **Python** | 3.13 | Scripts ETL et ML |
| **Pandas** | 2.3.3 | Manipulation données |
| **PyTrends** | 4.9.2 | API Google Trends |
| **SciPy** | 1.16.3 | Corrélations & stats |
| **NumPy** | 2.3.5 | Calculs numériques |
| **PostgreSQL** | 15 | Base de données |
| **Grafana** | Latest | Visualisation |
| **Podman/Docker** | - | Containerisation |

---

## 📊 Base de Données

### 7 Tables PostgreSQL

1. **trends_raw** (265 records) - Données brutes Google Trends
2. **chatgpt_evolution** (53 records) - Évolution ChatGPT avec moyenne mobile
3. **ai_peaks** (variable) - Pics détectés (z-score > 1.5)
4. **geo_distribution** (10 records) - Top 10 pays par keyword
5. **ml_comparison** (53 records) - France vs USA pour Machine Learning
6. **ai_forecast** (30 records) - Prévisions 30 jours avec IC 80%
7. **keyword_correlations** (1+ records) - Analyses de corrélation ⭐

**Total:** 411 enregistrements analytiques

---

## 🔍 Analyse de Corrélation

### Méthodologie

- **Méthode:** Corrélation de Pearson avec time-lag analysis
- **Plage:** ±10 semaines de décalage temporel
- **Test:** p-value < 0.05 pour significativité statistique

### Résultats ChatGPT ↔ Data Science

```
Corrélation: 0.442 (modérée positive)
Lag optimal: 4 semaines (Data Science mène)
p-value: 0.017 ✅ Statistiquement significatif
Interprétation: Les professionnels Data Science ont adopté 
                ChatGPT ~1 mois avant le grand public
```

---

## 📚 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Déploiement pas à pas avec troubleshooting
- **[GRAFANA_GUIDE.md](GRAFANA_GUIDE.md)** - Configuration Grafana et création dashboards
- **[PRESENTATION_PROJET.md](PRESENTATION_PROJET.md)** - Présentation académique complète

---

## 🎯 Cas d'Usage

### 1. Veille Technologique
Identifier les technologies émergentes et anticiper les besoins en formation.

### 2. Marketing Digital
Optimiser le SEO sur keywords populaires et cibler les marchés géographiques porteurs.

### 3. Recrutement IT
Comprendre la demande de compétences et ajuster les offres d'emploi.

### 4. Investissement Tech
Évaluer l'intérêt public pour des technologies et détecter les tendances futures.

---

## 💡 Insights Clés Découverts

1. **🚀 ChatGPT domine** - Croissance explosive +86.5% en 12 mois
2. **🐍 Python reste stable** - Intérêt constant et élevé (65-75)
3. **🔗 Corrélation significative** - Data Science early adopters de ChatGPT
4. **🌍 USA leader** - Domine tous les keywords (2-3× France)
5. **📈 Croissance continue** - Prévisions positives pour les 30 prochains jours

---

## 🛠️ Commandes Utiles

### Vérification Données

```powershell
# Compter les enregistrements
podman exec trends_postgres psql -U trends_user -d trends_db -c "SELECT COUNT(*) FROM trends_raw;"

# Voir la corrélation
podman exec trends_postgres psql -U trends_user -d trends_db -c "SELECT * FROM keyword_correlations;"

# Top 5 Python pays
podman exec trends_postgres psql -U trends_user -d trends_db -c "SELECT * FROM geo_distribution WHERE keyword='Python' ORDER BY rank LIMIT 5;"
```

### Pipeline Complet

```powershell
# Exécuter tout le pipeline automatiquement
.\scripts\run_pipeline.ps1
```


