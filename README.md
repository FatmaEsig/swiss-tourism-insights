# 📊 Swiss Tourism Insights — Visualisation du Tourisme Suisse

Application Streamlit permettant d’analyser la saisonnalité du tourisme en Suisse, d’explorer les profils régionaux et de simuler des scénarios d’occupation hôtelière.

---

## 🚀 Installation & Lancement

### 1. Cloner le dépôt
```bash
git clone https://github.com/FatmaEsig/swiss-tourism-insights.git
cd swiss-tourism-insights
```
#### 2. Créer et activer l’environnement virtuel
```bash
python -m venv .venv
```

## Windows :
```bash
.venv\Scripts\activate
```

## Mac / Linux :
```bash
source .venv/bin/activate <br>
```

### 3. Installer les dépendances
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

(ou simplement : pip install -r requirements.txt)
```

### 4. Lancer l'application
```bash
streamlit run app.py  
```

🧱 Architecture des Données (Star Schema)
Le projet utilise une modélisation en étoile pour optimiser les performances de filtrage et la lisibilité des visualisations.

📁 Dimensions
Dim_Temps : Annee, Mois, Mois_No

Dim_Region : Region_Touristique, Latitude, Longitude

Dim_Pays : Pays_de_provenance

📊 Table de Fait — Fact_Hotellerie
Contient :

Clés : Annee, Mois, Region_Touristique, Pays_de_provenance

Offre : Etablissements_ouverts, Chambres_disponibles, Lits_disponibles

Demande : Arrivees, Nuitees, Taux_occupation_chambres (%)

🛠️ Pipeline Technique
✔ Préparation des données (Pandas)
Chargement des fichiers OFS

Fusion des tables via pd.merge

Ajout des coordonnées géographiques

Export en .csv ou .parquet pour Streamlit

✔ Application Streamlit
Layout large : st.set_page_config(layout="wide")

Sidebar avec filtres globaux (Année, Région, Pays)

Navigation en chapitres

✔ Visualisations (Plotly)
Carte interactive (scatter_mapbox)

Courbes temporelles (line)

Barres empilées 100%

Heatmap de saisonnalité

Simulation de scénarios (projection linéaire ou waterfall)

📦 Dépendances principales
streamlit

pandas

plotly

openpyxl

🎯 Objectif du Projet
Offrir un outil de Business Intelligence permettant :

d’analyser la saisonnalité du tourisme suisse,

d’identifier les périodes creuses,

de comparer les régions touristiques,

de simuler des scénarios d’augmentation de la demande hors saison.

📁 Structure du Projet
Code
swiss-tourism-insights/
│
├── app.py
├── data/
│   ├── OFS_offre_demande.xlsx
│   ├── OFS_provenance.xlsx
│   └── df_final.csv
│
├── requirements.txt
└── README.md


📝 Auteur
Projet développé par Nolan, Tugba, Fatma dans le cadre d'un travail de visualisation et analyse de données.