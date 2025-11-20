# New AI Trends Dashboard Setup

## Quick Setup - 6 Panels

### Data Source (Already configured)
- Name: Dashboard API
- URL: `http://10.79.36.27:8000`

---

## Panel 1: ChatGPT Evolution (12 months)

- **Type**: Time series
- **Path**: `/chatgpt/evolution`
- **Fields**:
  1. `$[*].date` → **Time**
  2. `$[*].value` → **Number** (Alias: "Recherches ChatGPT")
  3. `$[*].rolling_28d_mean` → **Number** (Alias: "Moyenne 28j")
- **Title**: "Évolution ChatGPT (12 mois)"

---

## Panel 2: AI Peaks (Anomalies détectées)

- **Type**: Table
- **Path**: `/ai/peaks`
- **Fields**:
  1. `$[*].date` → **String**
  2. `$[*].peak_value` → **Number**
  3. `$[*].z_score` → **Number**
- **Title**: "Pics AI détectés"

---

## Panel 3: Python - Top Pays

- **Type**: Table
- **Path**: `/python/map`
- **Fields**:
  1. `$[*].region` → **String** (Alias: "Pays")
  2. `$[*].value` → **Number** (Alias: "Score")
- **Title**: "Top pays - Recherches Python"
- **Table Options**: Sort by value descending

---

## Panel 4: Machine Learning - France vs USA

- **Type**: Time series
- **Path**: `/machine-learning/fr-vs-us`
- **Fields**:
  1. `$[*].date` → **Time**
  2. `$[*].fr_value` → **Number** (Alias: "France")
  3. `$[*].us_value` → **Number** (Alias: "USA")
  4. `$[*].diff` → **Number** (Alias: "Écart")
- **Title**: "Machine Learning: France vs USA"

---

## Panel 5: Data Science / Événements (Corrélation)

### Panel 5A: Stat
- **Type**: Stat
- **Path**: `/data-science/events-correlation`
- **Fields**:
  1. `$.metrics.match_rate` → **Number**
- **Title**: "Taux corrélation Data Science/Événements"
- **Unit**: Percent (0-100)

### Panel 5B: Table
- **Type**: Table
- **Path**: `/data-science/events-correlation`
- **Fields**:
  1. `$.sample_matches[*].peak_date` → **String**
  2. `$.sample_matches[*].event_date` → **String**
  3. `$.sample_matches[*].event_type` → **String**
  4. `$.sample_matches[*].score` → **Number**
- **Title**: "Événements corrélés"

---

## Panel 6: AI Forecast (30 jours)

- **Type**: Time series
- **Path**: `/ai/forecast`
- **Fields**:
  1. `$[*].date` → **Time**
  2. `$[*].forecast` → **Number** (Alias: "Prévision")
  3. `$[*].lower80` → **Number** (Alias: "Limite basse")
  4. `$[*].upper80` → **Number** (Alias: "Limite haute")
- **Title**: "Prédiction AI (30 jours)"

---

## Expected Results

✅ **Panel 1**: ChatGPT shows 96% growth (51 → 100)
✅ **Panel 3**: Python top country is China (100)
✅ **Panel 4**: France leads USA by ~23 points in Machine Learning searches
✅ **Panel 6**: AI forecast with 30-day predictions

---

## Steps to Create

1. Go to Grafana: http://localhost:3000
2. Create new dashboard (+ icon → Dashboard)
3. For each panel:
   - Click "Add visualization"
   - Select "Dashboard API" data source
   - Choose visualization type
   - Enter Path
   - Add Fields with JSONPath expressions
   - Set field Types
   - Add Aliases
   - Set Title
   - Click "Apply"
4. Arrange panels in grid
5. Save dashboard as "AI Trends Analytics"
6. Export JSON to `dashboards/grafana_ai_dashboard.json`
