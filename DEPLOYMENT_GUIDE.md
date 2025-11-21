# 🚀 Guide de Déploiement - Google Trends Analytics

Guide complet pour déployer ce projet sur une nouvelle machine.

---

## 📋 Prérequis

### Logiciels Requis
- **Podman** (ou Docker) installé
- **Git** pour cloner le projet
- **Python 3.11+** (optionnel, seulement pour scripts locaux)

### Ports Nécessaires
- Port **5432** : PostgreSQL
- Port **3000** : Grafana

---

## 📦 Étape 1 : Cloner le Projet

```powershell
# Cloner le dépôt
git clone https://github.com/semragse/firstprojectipssidata.git
cd firstprojectipssidata
```

---

## 🐳 Étape 2 : Télécharger les Images Docker

Si vous êtes derrière un proxy d'entreprise avec certificats SSL :

```powershell
# Télécharger PostgreSQL
podman pull --tls-verify=false docker.io/library/postgres:15

# Télécharger Grafana
podman pull --tls-verify=false docker.io/grafana/grafana:latest
```

Sans proxy SSL :
```powershell
podman pull postgres:15
podman pull grafana/grafana:latest
```

---

## 🚀 Étape 3 : Démarrer les Services

```powershell
# Démarrer PostgreSQL et Grafana
podman-compose -f docker-compose-simple.yml up -d

# Vérifier que les conteneurs sont démarrés
podman ps
```

Vous devriez voir :
```
CONTAINER ID  IMAGE                             STATUS
xxxxxxxxxx    postgres:15                       Up (healthy)
xxxxxxxxxx    grafana/grafana:latest            Up
```

---

## 📊 Étape 4 : Charger les Données dans PostgreSQL

### Option A : Avec les Données Existantes (Recommandé)

```powershell
# 1. Copier le script Python dans le conteneur
podman cp scripts/load_csv_to_postgres.py trends_postgres:/tmp/

# 2. Copier les données CSV dans le conteneur
podman cp data/. trends_postgres:/tmp/data/

# 3. Installer Python et les dépendances dans le conteneur PostgreSQL
podman exec trends_postgres bash -c "apt-get update && apt-get install -y python3 python3-pip && pip3 install pandas psycopg2-binary --break-system-packages"

# 4. Charger les données
podman exec -w /tmp trends_postgres python3 load_csv_to_postgres.py
```

Vous devriez voir :
```
✅ Loaded 265 records to trends_raw
✅ Loaded 53 records to chatgpt_evolution
✅ Loaded 10 records to geo_distribution
✅ Loaded 53 records to ml_comparison
✅ Loaded 30 records to ai_forecast
```

### Option B : Extraire de Nouvelles Données

Si vous voulez extraire des données fraîches depuis Google Trends :

```powershell
# 1. Créer un environnement virtuel Python
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Installer les dépendances
pip install -r requirements-simple.txt

# 3. Extraire les données (avec --insecure si proxy SSL)
python scripts/extract_to_postgres.py --insecure

# 4. Transformer et analyser les données
python scripts/transform_to_postgres.py
```

---

## 🎨 Étape 5 : Configurer Grafana

### 5.1 Accéder à Grafana

Ouvrez votre navigateur : **http://localhost:3000**

**Identifiants par défaut :**
- Username : `admin`
- Password : `admin`

### 5.2 Ajouter la Source de Données PostgreSQL

1. Cliquez sur **⚙️ Configuration** → **Data sources**
2. Cliquez sur **Add data source**
3. Sélectionnez **PostgreSQL**
4. Configurez avec ces paramètres **EXACTS** :

```
Name: Trends Database
Host: trends_postgres:5432    ⚠️ IMPORTANT: Utiliser le nom du conteneur, pas localhost
Database: trends_db
User: trends_user
Password: trends_pass
SSL Mode: disable
Version: 15.0
```

5. Cliquez sur **Save & test**
6. Vous devriez voir : ✅ **"Database Connection OK"**

### 5.3 Importer le Dashboard

**Option 1 : Import JSON (Recommandé)**

1. Allez dans **Dashboards** → **Import**
2. Cliquez sur **Upload JSON file**
3. Sélectionnez : `dashboards/grafana_postgres_dashboard_v2.json`
4. Dans le menu déroulant, sélectionnez **"Trends Database"**
5. Cliquez sur **Import**

**Option 2 : Créer Manuellement**

Créez un nouveau dashboard et ajoutez ces requêtes :

#### Panel 1 : ChatGPT Evolution
```sql
SELECT
  EXTRACT(EPOCH FROM date) * 1000 AS "time",
  value AS "ChatGPT Interest",
  rolling_28d_mean AS "28-Day Average"
FROM chatgpt_evolution
ORDER BY date
```
Type : **Time series**

#### Panel 2 : Python Top 10 Countries
```sql
SELECT
  region AS "Country",
  value AS "Search Interest",
  rank AS "Rank"
FROM geo_distribution
WHERE keyword = 'Python'
ORDER BY rank
```
Type : **Table**

#### Panel 3 : Machine Learning France vs USA
```sql
SELECT
  EXTRACT(EPOCH FROM date) * 1000 AS "time",
  fr_value AS "France",
  us_value AS "USA",
  diff AS "Difference"
FROM ml_comparison
ORDER BY date
```
Type : **Time series**

#### Panel 4 : AI Forecast (30 Days)
```sql
SELECT
  EXTRACT(EPOCH FROM date) * 1000 AS "time",
  forecast AS "AI Forecast",
  lower_bound AS "Lower 80%",
  upper_bound AS "Upper 80%"
FROM ai_forecast
ORDER BY date
```
Type : **Time series**

#### Panel 5 : All Keywords Comparison
```sql
SELECT
  EXTRACT(EPOCH FROM date) * 1000 AS "time",
  keyword,
  value
FROM trends_raw
WHERE keyword IN ('AI', 'Machine Learning', 'Python', 'Data Science', 'ChatGPT')
ORDER BY date
```
Type : **Time series**

---

## 🔍 Étape 6 : Vérifier l'Installation

### Vérifier PostgreSQL
```powershell
# Se connecter à PostgreSQL
podman exec -it trends_postgres psql -U trends_user -d trends_db

# Dans psql, exécuter :
SELECT COUNT(*) FROM trends_raw;        -- Devrait retourner 265
SELECT COUNT(*) FROM chatgpt_evolution; -- Devrait retourner 53
SELECT COUNT(*) FROM ai_forecast;       -- Devrait retourner 30
\q
```

### Vérifier les Tables
```powershell
podman exec trends_postgres psql -U trends_user -d trends_db -c "\dt"
```

Vous devriez voir :
```
 trends_raw
 chatgpt_evolution
 ai_peaks
 geo_distribution
 ml_comparison
 ai_forecast
```

---

## 🛠️ Commandes de Gestion

### Arrêter les Services
```powershell
podman-compose -f docker-compose-simple.yml down
```

### Redémarrer les Services
```powershell
podman-compose -f docker-compose-simple.yml restart
```

### Voir les Logs
```powershell
# Logs PostgreSQL
podman logs trends_postgres

# Logs Grafana
podman logs trends_grafana

# Logs en temps réel
podman logs -f trends_postgres
```

### Supprimer les Données et Redémarrer
```powershell
# Arrêter et supprimer tout (y compris les volumes)
podman-compose -f docker-compose-simple.yml down -v

# Redémarrer proprement
podman-compose -f docker-compose-simple.yml up -d

# Recharger les données (refaire Étape 4)
```

---

## 🐛 Dépannage

### Problème : "Port 5432 already in use"
```powershell
# Trouver le processus utilisant le port
netstat -ano | findstr :5432

# Arrêter le processus ou changer le port dans docker-compose-simple.yml
```

### Problème : "Connection refused" dans Grafana
- ✅ Vérifiez que vous utilisez `trends_postgres:5432` et **pas** `localhost:5432`
- ✅ Vérifiez que le conteneur PostgreSQL est en état "healthy" : `podman ps`

### Problème : "No data" dans les Dashboards
1. Vérifiez que les données sont chargées :
```powershell
podman exec trends_postgres psql -U trends_user -d trends_db -c "SELECT COUNT(*) FROM trends_raw;"
```

2. Vérifiez la connexion Grafana à PostgreSQL
3. Vérifiez que les requêtes utilisent `EXTRACT(EPOCH FROM date) * 1000` pour le champ time

### Problème : Certificats SSL (Proxy Entreprise)
```powershell
# Toujours utiliser --tls-verify=false pour les pulls
podman pull --tls-verify=false docker.io/library/postgres:15
```

---

## 📂 Structure du Projet

```
firstprojectipssidata/
├── docker-compose-simple.yml       # Configuration conteneurs
├── scripts/
│   ├── init_db.sql                 # Schéma de base de données
│   ├── load_csv_to_postgres.py     # Script de chargement données
│   ├── extract_to_postgres.py      # Extraction Google Trends
│   └── transform_to_postgres.py    # Transformation données
├── data/
│   ├── raw/                        # Données brutes
│   └── processed/analytics/        # Données transformées (CSV)
├── dashboards/
│   └── grafana_postgres_dashboard_v2.json  # Dashboard Grafana
└── requirements-simple.txt         # Dépendances Python
```

---

## 🔐 Informations de Connexion

### PostgreSQL
```
Host: localhost (depuis la machine hôte)
      trends_postgres:5432 (depuis Grafana/conteneurs)
Port: 5432
Database: trends_db
User: trends_user
Password: trends_pass
```

### Grafana
```
URL: http://localhost:3000
Username: admin
Password: admin
```

---

## 📊 Données Incluses

Le projet contient des données Google Trends pour :
- **Période** : Novembre 2024 - Décembre 2025
- **Keywords** : AI, Machine Learning, Python, Data Science, ChatGPT
- **Analyses** :
  - Évolution ChatGPT (12 mois + moyenne mobile 28 jours)
  - Distribution géographique Python (Top 10 pays)
  - Comparaison ML France vs USA
  - Prévisions AI (30 jours avec intervalles de confiance)
  - Tendances générales tous keywords

---

## ✅ Checklist de Déploiement

- [ ] Podman/Docker installé
- [ ] Ports 5432 et 3000 disponibles
- [ ] Images Docker téléchargées
- [ ] Conteneurs démarrés (podman ps)
- [ ] Données chargées dans PostgreSQL (411 enregistrements total)
- [ ] Source de données PostgreSQL configurée dans Grafana
- [ ] Dashboard importé ou créé
- [ ] Visualisations affichent les données

---

## 🆘 Support

Si vous rencontrez des problèmes :
1. Consultez la section **Dépannage** ci-dessus
2. Vérifiez les logs : `podman logs trends_postgres`
3. Vérifiez les fichiers README-SIMPLE.md et QUICK_START.md

---

## 📝 Notes Importantes

⚠️ **Configuration Grafana** : Toujours utiliser `trends_postgres:5432` comme host, jamais `localhost` car Grafana tourne dans un conteneur.

⚠️ **Timestamps** : Les requêtes SQL doivent utiliser `EXTRACT(EPOCH FROM date) * 1000` pour convertir les dates en timestamps milliseconds pour Grafana.

⚠️ **Proxy SSL** : Si derrière un proxy d'entreprise, toujours utiliser `--tls-verify=false` pour les pulls d'images.

---

**Projet déployé avec succès ! 🎉**
