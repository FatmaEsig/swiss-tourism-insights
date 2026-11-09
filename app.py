"""Application Streamlit de visualisation du tourisme suisse."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Tourisme Suisse",
    page_icon="🇨🇭",
    layout="wide",
)

DATA_PATH = Path(__file__).parent / "data" / "processed" / "master_data.csv"
REQUIRED_COLUMNS = {
    "Annee",
    "Mois_No",
    "Mois_Nom",
    "Region_Nom",
    "Arrivees",
    "Nuitees",
    "Suisse_Nuitées",
    "Taux_occupation_chambres_pct",
    "Latitude",
    "Longitude",
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
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Colonnes obligatoires absentes du fichier maître : {missing}")

    for column in (
        "Annee",
        "Mois_No",
        "Arrivees",
        "Nuitees",
        "Suisse_Nuitées",
        "Taux_occupation_chambres_pct",
        "Latitude",
        "Longitude",
    ):
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data["Region_Nom"] = data["Region_Nom"].astype("string").str.strip()
    data["Mois_Nom"] = data["Mois_Nom"].astype("string").str.strip()
    return data.dropna(subset=["Annee", "Mois_No", "Region_Nom"]).copy()


def render_sidebar(data: pd.DataFrame) -> tuple[str, tuple[int, int], list[str]]:
    """Affiche la navigation et renvoie les filtres globaux sélectionnés."""
    with st.sidebar:
        st.title("Tourisme Suisse")
        chapter = st.radio(
            "Navigation",
            options=[
                "Chapitre 1 : Vue d'ensemble",
                "Chapitre 2 : Profils de clientèle",
                "Chapitre 3 : Typologie & Saisonnalité",
                "Chapitre 4 : Outil de simulation",
            ],
        )

        st.subheader("Filtres globaux")
        years = sorted(data["Annee"].dropna().astype(int).unique().tolist())
        if not years:
            st.info("Aucune année disponible dans les données.")
            return chapter, (0, 0), []

        year_range = st.slider(
            "Période",
            min_value=years[0],
            max_value=years[-1],
            value=(years[0], years[-1]),
            step=1,
        )

        regions = sorted(data["Region_Nom"].dropna().unique().tolist())
        selected_regions = st.multiselect(
            "Régions",
            options=regions,
            default=regions,
        )

    return chapter, year_range, selected_regions


def filter_data(
    data: pd.DataFrame,
    year_range: tuple[int, int],
    selected_regions: list[str],
) -> pd.DataFrame:
    """Applique les filtres globaux sans modifier le DataFrame mis en cache."""
    start_year, end_year = year_range
    return data[
        data["Annee"].between(start_year, end_year)
        & data["Region_Nom"].isin(selected_regions)
    ].copy()


def render_overview(data: pd.DataFrame) -> None:
    """Affiche le chapitre 1 : carte spatiale et évolution temporelle."""
    st.title("Chapitre 1 : Vue d'ensemble de la fréquentation touristique suisse")

    if data.empty:
        st.info("Aucune donnée ne correspond aux filtres sélectionnés.")
        return

    total_nights = data["Nuitees"].sum()
    average_occupancy = data["Taux_occupation_chambres_pct"].mean()
    metric_columns = st.columns(2)
    metric_columns[0].metric("Nuitées", f"{total_nights:,.0f}".replace(",", " "))
    metric_columns[1].metric(
        "Taux moyen d'occupation des chambres",
        f"{average_occupancy:.1f} %",
    )

    st.subheader("Fréquentation par région")
    map_data = (
        data.dropna(subset=["Latitude", "Longitude"])
        .groupby("Region_Nom", as_index=False)
        .agg(
            Nuitees=("Nuitees", "sum"),
            Taux_occupation_chambres_pct=("Taux_occupation_chambres_pct", "mean"),
            Latitude=("Latitude", "first"),
            Longitude=("Longitude", "first"),
        )
    )

    if map_data.empty:
        st.info(
            "La carte ne peut pas être affichée : aucune région sélectionnée "
            "ne possède de coordonnées géographiques."
        )
    else:
        map_figure = px.scatter_map(
            map_data,
            lat="Latitude",
            lon="Longitude",
            size="Nuitees",
            color="Taux_occupation_chambres_pct",
            hover_name="Region_Nom",
            hover_data={
                "Nuitees": ":,.0f",
                "Taux_occupation_chambres_pct": ":.1f",
                "Latitude": False,
                "Longitude": False,
            },
            color_continuous_scale="Viridis",
            size_max=45,
            zoom=6.5,
            center={"lat": 46.8, "lon": 8.2},
            map_style="carto-positron",
            labels={
                "Nuitees": "Nuitées",
                "Taux_occupation_chambres_pct": "Occupation moyenne (%)",
            },
        )
        map_figure.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            coloraxis_colorbar_title="Occupation (%)",
        )
        st.plotly_chart(map_figure, use_container_width=True)

    st.subheader("Évolution temporelle des nuitées")
    monthly_data = data[data["Mois_No"].between(1, 12)].copy()
    if monthly_data.empty:
        yearly_data = (
            data.groupby(["Annee", "Region_Nom"], as_index=False)["Nuitees"]
            .sum()
            .assign(Temps=lambda frame: pd.to_datetime(frame["Annee"], format="%Y"))
        )
        x_column = "Temps"
        timeline_data = yearly_data
    else:
        timeline_data = (
            monthly_data.groupby(["Annee", "Mois_No", "Region_Nom"], as_index=False)[
                "Nuitees"
            ]
            .sum()
            .assign(
                Temps=lambda frame: pd.to_datetime(
                    frame["Annee"].astype(str)
                    + "-"
                    + frame["Mois_No"].astype(str)
                    + "-01",
                    format="%Y-%m-%d",
                )
            )
        )
        x_column = "Temps"

    timeline_figure = px.line(
        timeline_data.sort_values(x_column),
        x=x_column,
        y="Nuitees",
        color="Region_Nom" if timeline_data["Region_Nom"].nunique() > 1 else None,
        markers=True,
        labels={"Temps": "Période", "Nuitees": "Nuitées", "Region_Nom": "Région"},
    )
    timeline_figure.update_layout(
        hovermode="x unified",
        yaxis={"tickformat": ",.0f", "title": "Nuitées"},
        legend_title_text="Région",
    )
    st.plotly_chart(timeline_figure, use_container_width=True)


def render_profils(data: pd.DataFrame) -> None:
    """Affiche les indicateurs de dépendance internationale et de séjour."""
    st.title("Chapitre 2 : Analyser la demande et les profils de clientèle")

    if data.empty:
        st.info("Aucune donnée ne correspond aux filtres sélectionnés.")
        return

    profils = data[["Region_Nom", "Nuitees", "Suisse_Nuitées", "Arrivees"]].copy()
    profils["Etranger_Nuitees"] = (
        profils["Nuitees"] - profils["Suisse_Nuitées"]
    )

    provenance = (
        profils.groupby("Region_Nom", as_index=False)[
            ["Suisse_Nuitées", "Etranger_Nuitees"]
        ]
        .sum()
    )
    provenance["Total_Nuitees"] = provenance[
        ["Suisse_Nuitées", "Etranger_Nuitees"]
    ].sum(axis=1)
    provenance = provenance[provenance["Total_Nuitees"] > 0].copy()

    if provenance.empty:
        st.info("Les données de provenance ne permettent pas de calculer une répartition.")
    else:
        provenance_long = provenance.melt(
            id_vars="Region_Nom",
            value_vars=["Suisse_Nuitées", "Etranger_Nuitees"],
            var_name="Provenance",
            value_name="Nuitees",
        )
        provenance_long["Pourcentage"] = (
            provenance_long["Nuitees"]
            / provenance_long["Region_Nom"].map(
                provenance.set_index("Region_Nom")["Total_Nuitees"]
            )
            * 100
        )
        provenance_long["Provenance"] = provenance_long["Provenance"].replace(
            {
                "Suisse_Nuitées": "Suisse",
                "Etranger_Nuitees": "Étranger",
            }
        )
        region_order = sorted(provenance["Region_Nom"].tolist(), reverse=True)

        international_figure = px.bar(
            provenance_long,
            x="Pourcentage",
            y="Region_Nom",
            color="Provenance",
            orientation="h",
            category_orders={
                "Region_Nom": region_order,
                "Provenance": ["Suisse", "Étranger"],
            },
            color_discrete_map={"Suisse": "#163A5F", "Étranger": "#B8C2CC"},
            labels={
                "Pourcentage": "Part des nuitées (%)",
                "Region_Nom": "Région",
                "Provenance": "Provenance",
            },
        )
        international_figure.update_layout(
            barmode="stack",
            xaxis={"range": [0, 100], "ticksuffix": "%"},
            legend_title_text="",
        )
        st.subheader("Dépendance au tourisme international")
        st.plotly_chart(international_figure, use_container_width=True)

    duree = (
        profils.groupby("Region_Nom", as_index=False)[["Nuitees", "Arrivees"]]
        .sum()
    )
    duree = duree[duree["Arrivees"] > 0].copy()
    if duree.empty:
        st.info("Les données ne permettent pas de calculer une durée moyenne de séjour.")
        return

    duree["Duree_Moyenne"] = duree["Nuitees"] / duree["Arrivees"]
    duree = duree.sort_values("Duree_Moyenne", ascending=False)
    duration_figure = px.bar(
        duree,
        x="Duree_Moyenne",
        y="Region_Nom",
        orientation="h",
        text_auto=".1f",
        color_discrete_sequence=["#2F6B9A"],
        labels={
            "Duree_Moyenne": "Nuitées moyennes par arrivée",
            "Region_Nom": "Région",
        },
    )
    duration_figure.update_layout(
        showlegend=False,
        yaxis={"categoryorder": "array", "categoryarray": duree["Region_Nom"].tolist()},
    )
    st.subheader("Durée moyenne de séjour")
    st.plotly_chart(duration_figure, use_container_width=True)


def render_placeholder(chapter: str) -> None:
    """Affiche un emplacement explicite pour les chapitres non implémentés."""
    st.title(chapter)
    st.info("Ce chapitre sera disponible dans une prochaine étape.")


def main() -> None:
    """Point d'entrée de l'application."""
    try:
        data = load_data()
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        st.stop()

    chapter, year_range, selected_regions = render_sidebar(data)
    filtered_data = filter_data(data, year_range, selected_regions)

    if chapter == "Chapitre 1 : Vue d'ensemble":
        render_overview(filtered_data)
    elif chapter == "Chapitre 2 : Profils de clientèle":
        render_profils(filtered_data)
    else:
        render_placeholder(chapter)


if __name__ == "__main__":
    main()
