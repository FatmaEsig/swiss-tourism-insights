# Swiss Tourism Insights - Projet de Visualisation de Données

Application web interactive développée avec **Streamlit** et **Plotly** pour
analyser la fréquentation hôtelière en Suisse, comprendre la saisonnalité des
régions urbaines et alpines, et simuler des stratégies de développement hors
saison.

## Auteurs

- **Fatma AYDIN**
- **Nolan ZOSSO**
- **Tugba AYDIN**

Projet réalisé en **2026-2027**.

## Objectifs

L'application permet de :

- suivre les nuitées et les arrivées touristiques ;
- comparer les régions touristiques suisses ;
- analyser la part de clientèle suisse et étrangère ;
- étudier les profils de séjour ;
- visualiser la saisonnalité mensuelle ;
- simuler l'impact d'une hausse de fréquentation pendant les mois creux ;
- consulter des analyses et des recommandations basées sur les données.

## Sources de données

Les données proviennent de l'**Office fédéral de la statistique (OFS)**, dans le
cadre de la **Statistique de l’hébergement touristique (HESTA)**.

Les deux fichiers bruts utilisés sont :

- `data/raw/OFS_offre_demande.xlsx` ;
- `data/raw/OFS_provenance.xlsx`.

Le projet prépare ces fichiers en :

1. gérant les en-têtes Excel complexes et les cellules fusionnées ;
2. normalisant les dimensions temporelles et géographiques ;
3. fusionnant les données d'offre, de demande et de provenance ;
4. ajoutant les coordonnées indicatives des régions ;
5. exportant le fichier maître `data/processed/master_data.csv`.

## Structure du projet

```text
swiss-tourism-insights/
│
├── app.py
├── requirements.txt
├── README.md
│
├── data/
│   ├── raw/
│   │   ├── OFS_offre_demande.xlsx
│   │   └── OFS_provenance.xlsx
│   │
│   └── processed/
│       └── master_data.csv       # Généré par le script de préparation
│
├── pages/
│   ├── A_propos.py
│   ├── Analyse.py
│   └── Recommendations.py
│
├── src/
│   ├── analysis.py
│   ├── dashboard_utils.py
│   ├── data_preparation.py
│   └── data_processing.py
│
└── assets/
```

## Installation et exécution

### Prérequis

- Python 3.10 ou version ultérieure ;
- `pip` ;
- une connexion Internet lors de l'installation des dépendances.

### Étape 1 — Cloner le dépôt

```bash
git clone https://github.com/FatmaEsig/swiss-tourism-insights.git
cd swiss-tourism-insights
```

### Étape 2 — Créer et activer un environnement virtuel

Sous Windows PowerShell :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Sous macOS ou Linux :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Étape 3 — Installer les dépendances

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Étape 4 — Générer le fichier maître

Cette étape est indispensable avant le lancement de l'application : elle lit les
fichiers OFS bruts, les nettoie, les fusionne et génère le CSV utilisé par
Streamlit.

```bash
python src/data_preparation.py
```

Le fichier suivant doit alors être présent :

```text
data/processed/master_data.csv
```

### Étape 5 — Lancer l'application

```bash
streamlit run app.py
```

L'application s'ouvre ensuite dans le navigateur à l'adresse indiquée par
Streamlit, généralement `http://localhost:8501`.

## Navigation dans l'application

L'application principale propose quatre chapitres :

1. **Vue d'ensemble** : indicateurs globaux, repérage spatial et évolution des
   nuitées ;
2. **Profils de clientèle** : parts de nuitées domestiques et internationales,
   ainsi que durée moyenne des séjours ;
3. **Typologie et saisonnalité** : heatmap des parts mensuelles et comparaison
   entre régions ;
4. **Outil de simulation** : scénario d'augmentation des nuitées pendant les
   quatre mois les moins fréquentés.

Les pages complémentaires sont accessibles depuis le menu Streamlit :

- **Analyse** : classement et indicateurs régionaux ;
- **Recommandations** : périodes prioritaires et pistes d'action ;
- **À propos** : contexte, auteurs, méthode et limites du projet.

## Technologies utilisées

- **Python** : langage de développement ;
- **Pandas** : lecture, nettoyage, transformation et agrégation des données ;
- **Plotly** : visualisations interactives ;
- **Streamlit** : interface web et navigation ;
- **OpenPyXL** : lecture des fichiers Excel OFS.

## Définitions principales

- **Nuitée** : nuit passée par un client dans un établissement d'hébergement ;
- **Arrivée** : début du séjour d'un client ;
- **Durée moyenne** : nombre moyen de nuitées par arrivée, calculé par
  `Nuitées / Arrivées` ;
- **Taux d'occupation des chambres** : part des chambres disponibles occupées ;
- **Basse saison** : dans l'outil de simulation, les quatre mois présentant les
  plus faibles nuitées historiques pour la région sélectionnée.

## Limites

Les analyses décrivent les données historiques disponibles auprès de l'OFS.
Les coordonnées utilisées dans la carte sont des points indicatifs des régions
et ne représentent pas leurs frontières administratives ou touristiques.

La simulation du chapitre 4 est un scénario pédagogique : elle ne constitue pas
une prévision et ne modélise pas les prix, la capacité hôtelière, la météo, les
événements ou les effets de substitution entre régions.
