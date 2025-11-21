# 📊 Guide Grafana - Configuration et Création de Dashboards

Guide complet pour connecter PostgreSQL à Grafana et créer vos dashboards de visualisation.

---

## 🔗 Étape 1 : Connecter PostgreSQL à Grafana

### 1.1 Accéder à Grafana
- Ouvrez votre navigateur : **http://localhost:3000**
- **Username:** `admin`
- **Password:** `admin`
- (Vous pouvez changer le mot de passe ou cliquer "Skip")

### 1.2 Ajouter la Source de Données PostgreSQL

1. Cliquez sur **⚙️ (Configuration)** dans le menu de gauche
2. Sélectionnez **"Data sources"**
3. Cliquez sur **"Add data source"**
4. Cherchez et sélectionnez **"PostgreSQL"**

### 1.3 Configurer la Connexion

Remplissez les champs suivants :

```
Name: Trends Database
Host: trends_postgres:5432
Database: trends_db
User: trends_user
Password: trends_pass
SSL Mode: disable
Version: 15.0
```

**⚠️ IMPORTANT:** 
- Utilisez `trends_postgres:5432` (nom du conteneur) et **PAS** `localhost:5432`
- Grafana tourne dans un conteneur et doit utiliser le nom du service Docker

### 1.4 Tester la Connexion

1. Cliquez sur **"Save & test"** en bas de la page
2. Vous devriez voir un message vert : ✅ **"Database Connection OK"**

Si erreur "connection refused" → vérifiez que vous utilisez bien `trends_postgres:5432`

---

## 📈 Étape 2 : Créer Votre Premier Dashboard

### 2.1 Créer un Nouveau Dashboard

1. Cliquez sur **"+"** dans le menu de gauche
2. Sélectionnez **"Dashboard"**
3. Cliquez sur **"Add visualization"**
4. Sélectionnez **"Trends Database"** comme source de données

---

## 🎨 Étape 3 : Panels de Visualisation

### Panel 1 : Évolution ChatGPT (12 Mois)

**Type de Panel:** Time series

**Configuration:**

1. Dans l'onglet **Query**, sélectionnez :
   - **Format:** Time series
   - **Code:** Activez le mode code (icône "Code" en haut à droite)

2. **Requête SQL:**
```sql
SELECT
  EXTRACT(EPOCH FROM date) * 1000 AS "time",
  value AS "ChatGPT Interest",
  rolling_28d_mean AS "Rolling 28-Day Average"
FROM chatgpt_evolution
ORDER BY date
```

**Pourquoi `EXTRACT(EPOCH FROM date) * 1000` ?**
- Grafana attend un timestamp en **millisecondes**
- `EXTRACT(EPOCH FROM date)` donne des secondes depuis 1970
- On multiplie par 1000 pour convertir en millisecondes

3. **Configuration du Panel:**
   - **Title:** "ChatGPT Evolution (12 Months)"
   - **Panel options → Legend:** Show legend
   - **Graph styles → Line interpolation:** Smooth
   - **Graph styles → Fill opacity:** 10

4. Cliquez sur **"Apply"** en haut à droite

---

### Panel 2 : Python - Top 10 Pays

**Type de Panel:** Table

**Requête SQL:**
```sql
SELECT
  region AS "Country",
  value AS "Search Interest",
  rank AS "Rank"
FROM geo_distribution
WHERE keyword = 'Python'
ORDER BY rank
```

**Configuration:**
- **Title:** "Python - Top 10 Countries"
- **Table options:** Activez "Show header"
- Pas besoin de time field pour une table

---

### Panel 3 : Machine Learning France vs USA

**Type de Panel:** Time series

**Requête SQL:**
```sql
SELECT
  EXTRACT(EPOCH FROM date) * 1000 AS "time",
  fr_value AS "France",
  us_value AS "USA",
  diff AS "Difference (FR - US)"
FROM ml_comparison
ORDER BY date
```

**Configuration:**
- **Title:** "Machine Learning - France vs USA"
- **Graph styles → Line width:** 2
- **Legend:** Bottom, show values

---

### Panel 4 : Prévisions AI (30 Jours)

**Type de Panel:** Time series

**Requête SQL:**
```sql
SELECT
  EXTRACT(EPOCH FROM date) * 1000 AS "time",
  forecast AS "AI Forecast",
  lower_bound AS "Lower 80% Confidence",
  upper_bound AS "Upper 80% Confidence"
FROM ai_forecast
ORDER BY date
```

**Configuration Avancée:**
- **Title:** "AI Forecast (30 Days)"
- **Graph styles → Fill opacity:** 20 (pour voir la bande de confiance)
- **Overrides (optionnel):**
  - Pour "Lower 80%" → Line width: 0, Fill below to: "Upper 80%"
  - Pour "Upper 80%" → Line width: 0

---

### Panel 5 : Comparaison Tous les Keywords

**Type de Panel:** Time series

**Requête SQL:**
```sql
SELECT
  EXTRACT(EPOCH FROM date) * 1000 AS "time",
  keyword,
  value
FROM trends_raw
WHERE keyword IN ('AI', 'Machine Learning', 'Python', 'Data Science', 'ChatGPT')
ORDER BY date
```

**Configuration:**
- **Title:** "All Keywords Comparison"
- **Graph styles → Line width:** 2
- **Tooltip mode:** All (pour voir toutes les valeurs au survol)

---

### Panel 6 : Corrélation ChatGPT vs Data Science (NOUVEAU!)

**Type de Panel:** Time series

**Requête SQL pour voir les deux courbes:**
```sql
SELECT
  EXTRACT(EPOCH FROM date) * 1000 AS "time",
  MAX(CASE WHEN keyword = 'ChatGPT' THEN value END) AS "ChatGPT",
  MAX(CASE WHEN keyword = 'Data Science' THEN value END) AS "Data Science"
FROM trends_raw
WHERE keyword IN ('ChatGPT', 'Data Science')
GROUP BY date
ORDER BY date
```

**Configuration:**
- **Title:** "ChatGPT vs Data Science Correlation"
- Ajoutez une annotation textuelle : "Correlation: 0.44 (Data Science leads by 4 weeks)"

---

### Panel 7 : Table des Corrélations

**Type de Panel:** Table

**Requête SQL:**
```sql
SELECT
  keyword1 AS "Keyword 1",
  keyword2 AS "Keyword 2",
  ROUND(CAST(correlation_coefficient AS NUMERIC), 3) AS "Correlation",
  optimal_lag_weeks AS "Lag (weeks)",
  CASE 
    WHEN is_significant THEN '✅ Significant'
    ELSE '⚠️ Not significant'
  END AS "Statistical Significance",
  analysis_date AS "Analysis Date"
FROM keyword_correlations
ORDER BY ABS(correlation_coefficient) DESC
```

**Configuration:**
- **Title:** "Keyword Correlations Analysis"
- Active "Show header"

---

## 🎯 Étape 4 : Organiser le Dashboard

### 4.1 Disposition des Panels

Organisez vos panels en glisser-déposer :

```
┌─────────────────────────────────────────────────────┐
│  ChatGPT Evolution    │  Python Top 10 Countries   │
│  (12 Months)          │  (Table)                   │
├─────────────────────────────────────────────────────┤
│  ML France vs USA     │  AI Forecast (30 Days)     │
│  (Time series)        │  (with confidence bands)   │
├─────────────────────────────────────────────────────┤
│  All Keywords Comparison (full width)               │
├─────────────────────────────────────────────────────┤
│  ChatGPT vs Data Science Correlation               │
├─────────────────────────────────────────────────────┤
│  Correlations Table (full width)                   │
└─────────────────────────────────────────────────────┘
```

### 4.2 Sauvegarder le Dashboard

1. Cliquez sur l'icône **💾 (Save dashboard)** en haut à droite
2. Donnez un nom : **"Google Trends AI Analytics"**
3. Ajoutez un dossier (optionnel) : **"Analytics"**
4. Cliquez sur **"Save"**

---

## ⏰ Étape 5 : Configurer le Time Range

### 5.1 Définir la Période

En haut à droite du dashboard :
1. Cliquez sur l'horloge (Time range picker)
2. Sélectionnez **"Absolute time range"**
3. **From:** `2024-11-01`
4. **To:** `2025-12-31`
5. Cliquez sur **"Apply time range"**

### 5.2 Auto-refresh (Optionnel)

Pour des données en temps réel :
1. Cliquez sur la flèche à côté de l'horloge
2. Sélectionnez **"5m"** (refresh toutes les 5 minutes)

---

## 🎨 Étape 6 : Personnalisation Avancée

### 6.1 Variables de Dashboard

Créer une variable pour sélectionner dynamiquement les keywords :

1. Paramètres du dashboard (⚙️) → **Variables** → **New variable**
2. **Name:** `keyword`
3. **Type:** Query
4. **Data source:** Trends Database
5. **Query:**
```sql
SELECT DISTINCT keyword FROM trends_raw ORDER BY keyword
```
6. **Multi-value:** Activé
7. **Include All option:** Activé

Utilisez ensuite dans vos requêtes :
```sql
WHERE keyword IN ($keyword)
```

### 6.2 Annotations

Ajouter des annotations pour marquer des événements :

1. Paramètres → **Annotations** → **New annotation**
2. **Name:** "Événements Tech"
3. **Data source:** Trends Database
4. **Query:**
```sql
SELECT
  EXTRACT(EPOCH FROM date) * 1000 AS time,
  'Peak détecté' AS text,
  ARRAY['peak'] AS tags
FROM ai_peaks
WHERE z_score > 2.0
```

---

## 📤 Étape 7 : Exporter/Importer Dashboard

### 7.1 Exporter en JSON

1. Paramètres du dashboard (⚙️)
2. **JSON Model** dans le menu de gauche
3. Copiez le JSON ou cliquez **"Save to file"**
4. Fichier sauvegardé : `my_dashboard.json`

### 7.2 Importer un Dashboard

1. **"+"** → **"Import"**
2. **"Upload JSON file"**
3. Sélectionnez le fichier JSON
4. Choisissez la source de données : **"Trends Database"**
5. Cliquez **"Import"**

---

## 🐛 Dépannage Courant

### Problème : "No data" dans les panels

**Solution 1:** Vérifier le Time Range
- Les données vont de Nov 2024 à Dec 2025
- Ajustez le time range pour inclure ces dates

**Solution 2:** Vérifier la requête SQL
```sql
-- Testez directement dans psql
podman exec trends_postgres psql -U trends_user -d trends_db -c "SELECT COUNT(*) FROM trends_raw;"
```

**Solution 3:** Vérifier le format Time Series
- Le champ "time" doit être en millisecondes
- Utilisez toujours : `EXTRACT(EPOCH FROM date) * 1000`

### Problème : "Connection refused"

- Vérifiez que vous utilisez `trends_postgres:5432`
- PAS `localhost:5432` depuis Grafana

### Problème : Les courbes ne s'affichent pas

- Format de query : Assurez-vous d'avoir sélectionné **"Time series"**
- Le premier champ doit s'appeler **"time"**
- Utilisez des guillemets pour les alias : `AS "time"`

---

## 📊 Requêtes SQL Utiles Supplémentaires

### Taux de croissance par keyword
```sql
SELECT 
  keyword,
  MIN(value) AS min_value,
  MAX(value) AS max_value,
  ROUND((MAX(value) - MIN(value)) * 100.0 / MIN(value), 1) AS growth_pct
FROM trends_raw
GROUP BY keyword
ORDER BY growth_pct DESC
```

### Top 3 pics détectés
```sql
SELECT 
  date,
  value,
  ROUND(CAST(z_score AS NUMERIC), 2) AS z_score
FROM ai_peaks
ORDER BY z_score DESC
LIMIT 3
```

### Moyenne mobile sur N jours
```sql
SELECT 
  EXTRACT(EPOCH FROM date) * 1000 AS "time",
  value,
  AVG(value) OVER (
    ORDER BY date 
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) AS "7-day moving average"
FROM trends_raw
WHERE keyword = 'AI'
ORDER BY date
```

---

## 🎓 Bonnes Pratiques

1. **Nommage clair** : Utilisez des alias descriptifs avec guillemets
2. **Couleurs cohérentes** : Assignez des couleurs fixes par keyword
3. **Légendes informatives** : Activez les légendes avec valeurs
4. **Time range adapté** : Ajustez selon vos données (2024-2025)
5. **Refresh intelligent** : Pas de refresh si données statiques
6. **Documentation** : Ajoutez des descriptions dans les panels (Edit → Description)

---

## 🚀 Dashboard Prêt à l'Emploi

Vous avez maintenant un dashboard complet avec :

✅ 7 visualisations professionnelles
✅ Tendances temporelles (time series)
✅ Tables de données (tables)
✅ Analyses de corrélation
✅ Prévisions avec intervalles de confiance
✅ Comparaisons géographiques

**Temps de création estimé:** 30-45 minutes

---

## 📸 Pour la Présentation

Conseils pour capturer de beaux screenshots :

1. **Mode Plein Écran** : Appuyez sur `F` sur un panel
2. **Mode Kiosk** : Ajoutez `?kiosk` à l'URL pour masquer les menus
3. **Thème** : Paramètres → Preferences → UI Theme (Dark/Light)
4. **Export PNG** : Panel menu → Share → Link → Direct link rendered image

---

**Votre dashboard est maintenant opérationnel! 🎉**
