"""Fonctions partagées par l'application et ses pages Streamlit."""

from pathlib import Path

import pandas as pd
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "data" / "processed" / "master_data.csv"

MONTH_NAMES = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]

REQUIRED_COLUMNS = {
    "Annee", "Mois_No", "Mois_Nom", "Region_Nom", "Arrivees", "Nuitees",
    "Suisse_Nuitées", "Taux_occupation_chambres_pct", "Latitude", "Longitude",
}


@st.cache_data
def load_data() -> pd.DataFrame:
    """Charge le fichier maître et normalise les colonnes numériques."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Le fichier de données est introuvable : {DATA_PATH}. "
            "Exécutez d'abord src/data_preparation.py."
        )
    data = pd.read_csv(DATA_PATH)
    missing_columns = REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        raise ValueError(
            "Colonnes obligatoires absentes du fichier maître : "
            + ", ".join(sorted(missing_columns))
        )
    for column in (
        "Annee", "Mois_No", "Arrivees", "Nuitees", "Suisse_Nuitées",
        "Taux_occupation_chambres_pct", "Latitude", "Longitude",
    ):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data["Region_Nom"] = data["Region_Nom"].astype("string").str.strip()
    data["Mois_Nom"] = data["Mois_Nom"].astype("string").str.strip()
    return data.dropna(subset=["Annee", "Mois_No", "Region_Nom"]).copy()


def annual_rows(data: pd.DataFrame) -> pd.DataFrame:
    """Retourne les lignes annuelles sans additionner les lignes mensuelles."""
    annual = data[data["Mois_No"] == 0].copy()
    return annual if not annual.empty else data[data["Mois_No"].between(1, 12)].copy()


def analysis_rows(data: pd.DataFrame) -> pd.DataFrame:
    """Évite de compter l'agrégat Suisse avec les régions détaillées."""
    rows = annual_rows(data)
    regional_rows = rows[rows["Region_Nom"] != "Suisse"].copy()
    return regional_rows if not regional_rows.empty else rows


def filter_context(data: pd.DataFrame) -> str:
    """Construit un résumé des filtres pour les titres."""
    years = sorted(data["Annee"].dropna().astype(int).unique().tolist())
    regions = data["Region_Nom"].dropna().nunique()
    if not years:
        return "aucune donnée"
    period = str(years[0]) if len(years) == 1 else f"{years[0]}–{years[-1]}"
    return f"{period} · {regions} région(s) sélectionnée(s)"


def format_number(value: float) -> str:
    """Formate un nombre avec des espaces, lisibles en français."""
    return f"{value:,.0f}".replace(",", " ")


def render_source_note() -> None:
    """Affiche la source et les transformations réalisées."""
    with st.expander("Source des données et méthode", expanded=False):
        st.markdown(
            """
            **Source :** Office fédéral de la statistique (OFS), statistiques de
            l'hôtellerie suisse. Fichiers bruts :
            `data/raw/OFS_offre_demande.xlsx` et `data/raw/OFS_provenance.xlsx`.

            **Préparation :** en-têtes Excel aplatis, cellules fusionnées propagées,
            puis fusion des deux fichiers sur l'année, le mois et la région.
            Résultat : `data/processed/master_data.csv`.

            **Définitions :** une *nuitée* est une nuit passée dans un hébergement ;
            une *arrivée* est le début d'un séjour ; la durée moyenne est
            `nuitées ÷ arrivées`. La simulation est un scénario indicatif, pas une
            prévision économétrique.
            """
        )
