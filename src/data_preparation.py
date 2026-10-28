"""Préparation et fusion des données statistiques de l'OFS.

Le script est exécutable depuis la racine du projet :

    python src/data_preparation.py

Les fichiers Excel sont lus depuis ``data/raw`` et le fichier aplati est
écrit dans ``data/processed/master_data.csv``.
"""

from __future__ import annotations

from pathlib import Path
import re

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"

OFFER_FILE = RAW_DIR / "OFS_offre_demande.xlsx"
PROVENANCE_FILE = RAW_DIR / "OFS_provenance.xlsx"
OUTPUT_FILE = PROCESSED_DIR / "master_data.csv"

KEY_COLUMNS = [
    "Annee",
    "Mois_No",
    "Mois_Nom",
    "Region_Code",
    "Region_Nom",
]

DIMENSION_COLUMNS = [
    "Annee",
    "Annee_Ref",
    "Mois_No",
    "Mois_Nom",
    "Region_Code",
    "Region_Nom",
]

OFFER_COLUMNS = [
    "Etablissements",
    "Chambres",
    "Lits",
    "Arrivees",
    "Nuitees",
    "Nuitees_chambres",
    "Taux_occupation_chambres_pct",
    "Taux_occupation_lits_pct",
]


def _clean_column_name(value: object) -> str:
    """Transforme un libellé Excel en nom de colonne stable et lisible."""
    text = "" if pd.isna(value) else str(value).strip()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^\w%]+", "_", text, flags=re.UNICODE)
    text = text.strip("_").replace("%", "pct")
    return text or "Colonne"


def _make_unique(names: list[str]) -> list[str]:
    """Ajoute un suffixe aux noms répétés après aplatissement."""
    counts: dict[str, int] = {}
    unique_names: list[str] = []
    for name in names:
        counts[name] = counts.get(name, 0) + 1
        suffix = f"_{counts[name]}" if counts[name] > 1 else ""
        unique_names.append(f"{name}{suffix}")
    return unique_names


def _read_dimensions(frame: pd.DataFrame) -> pd.DataFrame:
    """Extrait et normalise les six colonnes communes aux deux fichiers."""
    if frame.shape[1] < 6:
        raise ValueError("Le fichier OFS doit contenir au moins six colonnes de dimensions.")

    dimensions = frame.iloc[:, :6].copy()
    dimensions.columns = DIMENSION_COLUMNS
    dimensions = dimensions.ffill()

    # La valeur YYYY désigne le total annuel ; 0 permet de la représenter
    # proprement dans une colonne numérique tout en conservant son libellé.
    dimensions["Annee"] = pd.to_numeric(dimensions["Annee"], errors="coerce")
    dimensions["Mois_No"] = (
        dimensions["Mois_No"].replace({"YYYY": 0}).pipe(pd.to_numeric, errors="coerce")
    )
    dimensions["Region_Code"] = pd.to_numeric(
        dimensions["Region_Code"], errors="coerce"
    )
    dimensions["Mois_Nom"] = dimensions["Mois_Nom"].astype("string").str.strip()
    dimensions["Region_Nom"] = dimensions["Region_Nom"].astype("string").str.strip()

    dimensions = dimensions.dropna(subset=KEY_COLUMNS).copy()
    dimensions["Annee"] = dimensions["Annee"].astype("int64")
    dimensions["Mois_No"] = dimensions["Mois_No"].astype("int64")
    dimensions["Region_Code"] = dimensions["Region_Code"].astype("int64")
    return dimensions.drop(columns=["Annee_Ref"])


def _read_offer(path: Path) -> pd.DataFrame:
    """Lit le fichier offre/demande dont la première ligne contient les mesures."""
    raw = pd.read_excel(path, header=None, engine="openpyxl")
    dimensions = _read_dimensions(raw.iloc[1:, :])

    if raw.shape[1] < 14:
        raise ValueError("Le fichier offre/demande ne contient pas les huit mesures attendues.")

    offer = raw.iloc[1:, 6:14].copy()
    offer.columns = OFFER_COLUMNS
    offer = pd.concat([dimensions.reset_index(drop=True), offer.reset_index(drop=True)], axis=1)
    offer = offer.dropna(subset=["Region_Nom"]).copy()

    for column in OFFER_COLUMNS:
        offer[column] = pd.to_numeric(offer[column], errors="coerce")
    return offer


def _flatten_provenance_columns(raw: pd.DataFrame) -> list[str]:
    """Aplati les deux lignes d'en-tête pays/sous-catégorie."""
    countries = raw.iloc[0, 6:].ffill()
    categories = raw.iloc[1, 6:]
    names = [
        f"{_clean_column_name(country)}_{_clean_column_name(category)}"
        for country, category in zip(countries, categories)
    ]
    return _make_unique(names)


def _read_provenance(path: Path) -> pd.DataFrame:
    """Lit le fichier de provenance et transforme son MultiIndex en colonnes."""
    raw = pd.read_excel(path, header=None, engine="openpyxl")
    if raw.shape[0] < 3 or raw.shape[1] < 8:
        raise ValueError("Le fichier de provenance ne contient pas les en-têtes attendus.")

    dimensions = _read_dimensions(raw.iloc[2:, :])
    provenance = raw.iloc[2:, 6:].copy()
    provenance.columns = _flatten_provenance_columns(raw)
    provenance = pd.concat(
        [dimensions.reset_index(drop=True), provenance.reset_index(drop=True)],
        axis=1,
    )
    provenance = provenance.dropna(subset=["Region_Nom"]).copy()

    for column in provenance.columns[6:]:
        provenance[column] = pd.to_numeric(provenance[column], errors="coerce")
    return provenance


def _add_coordinates(data: pd.DataFrame) -> pd.DataFrame:
    """Ajoute des coordonnées d'exemple pour Genève et la région zurichoise."""
    coordinates = {
        "Genève": (46.2044, 6.1432),
        "Gen�ve": (46.2044, 6.1432),
        "Zurich": (47.3769, 8.5417),
        "Région zurichoise": (47.3769, 8.5417),
        "R�gion zurichoise": (47.3769, 8.5417),
    }
    data["Latitude"] = data["Region_Nom"].map(
        lambda region: coordinates.get(str(region), (None, None))[0]
    )
    data["Longitude"] = data["Region_Nom"].map(
        lambda region: coordinates.get(str(region), (None, None))[1]
    )
    return data


def prepare_master_data() -> pd.DataFrame:
    """Prépare, fusionne et exporte les données OFS."""
    offer = _read_offer(OFFER_FILE)
    provenance = _read_provenance(PROVENANCE_FILE)

    master = offer.merge(
        provenance,
        on=KEY_COLUMNS,
        how="inner",
        validate="one_to_one",
    )
    master = _add_coordinates(master)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    master.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"Fichier créé : {OUTPUT_FILE} ({len(master)} lignes, {len(master.columns)} colonnes)")
    return master


if __name__ == "__main__":
    prepare_master_data()
