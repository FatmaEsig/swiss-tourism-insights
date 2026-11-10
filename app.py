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


def render_typologie(data: pd.DataFrame) -> None:
    """Analyse la répartition mensuelle des nuitées par région."""
    st.title("Chapitre 3 : Typologie et analyse de la saisonnalité")

    if data.empty:
        st.info("Aucune donnée ne correspond aux filtres sélectionnés.")
        return

    monthly_data = data[
        data["Mois_No"].between(1, 12)
        & data["Nuitees"].notna()
        & data["Region_Nom"].notna()
    ].copy()
    if monthly_data.empty:
        st.info("Aucune donnée mensuelle disponible pour analyser la saisonnalité.")
        return

    month_labels = (
        monthly_data[["Mois_No", "Mois_Nom"]]
        .dropna()
        .drop_duplicates()
        .sort_values("Mois_No")
    )
    month_order = month_labels["Mois_Nom"].tolist()
    monthly_data["Mois_Nom"] = pd.Categorical(
        monthly_data["Mois_Nom"],
        categories=month_order,
        ordered=True,
    )

    seasonal = (
        monthly_data.groupby(["Region_Nom", "Mois_Nom"], observed=False, as_index=False)[
            "Nuitees"
        ]
        .sum()
    )
    seasonal["Total_annuel_region"] = seasonal.groupby("Region_Nom")[
        "Nuitees"
    ].transform("sum")
    seasonal = seasonal[seasonal["Total_annuel_region"] > 0].copy()
    seasonal["Part_nuitees_pct"] = (
        seasonal["Nuitees"] / seasonal["Total_annuel_region"] * 100
    )

    st.subheader("Répartition mensuelle des nuitées par région")
    heatmap_figure = px.density_heatmap(
        seasonal,
        x="Mois_Nom",
        y="Region_Nom",
        z="Part_nuitees_pct",
        histfunc="sum",
        text_auto=".1f",
        category_orders={"Mois_Nom": month_order},
        color_continuous_scale="Blues",
        labels={
            "Mois_Nom": "Mois",
            "Region_Nom": "Région",
            "Part_nuitees_pct": "Part des nuitées annuelles (%)",
        },
    )
    heatmap_figure.update_layout(
        coloraxis_colorbar_title="Part (%)",
        xaxis={"categoryorder": "array", "categoryarray": month_order},
    )
    st.plotly_chart(heatmap_figure, use_container_width=True)

    regions = sorted(monthly_data["Region_Nom"].dropna().unique().tolist())
    if not regions:
        st.info("Aucune région disponible pour la comparaison saisonnière.")
        return

    def default_region(candidates: list[str]) -> int:
        """Retourne l'index du premier candidat disponible."""
        for candidate in candidates:
            if candidate in regions:
                return regions.index(candidate)
        return 0

    st.subheader("Comparaison de la concentration saisonnière")
    selector_columns = st.columns(2)
    with selector_columns[0]:
        region_1 = st.selectbox(
            "Région 1 (ex: Alpine)",
            options=regions,
            index=default_region(["Grisons", "Valais"]),
            key="typologie_region_1",
        )
    with selector_columns[1]:
        region_2 = st.selectbox(
            "Région 2 (ex: Urbaine)",
            options=regions,
            index=default_region(["Région zurichoise", "R�gion zurichoise", "Genève", "Gen�ve"]),
            key="typologie_region_2",
        )

    comparison = (
        monthly_data[monthly_data["Region_Nom"].isin([region_1, region_2])]
        .groupby(["Mois_No", "Region_Nom"], as_index=False)["Nuitees"]
        .sum()
    )
    comparison = comparison.sort_values(["Mois_No", "Region_Nom"])
    comparison_figure = px.line(
        comparison,
        x="Mois_No",
        y="Nuitees",
        color="Region_Nom",
        markers=True,
        category_orders={"Mois_No": list(range(1, 13))},
        labels={
            "Mois_No": "Mois",
            "Nuitees": "Nuitées",
            "Region_Nom": "Région",
        },
    )
    comparison_figure.update_layout(
        xaxis={"dtick": 1, "range": [1, 12]},
        yaxis={"tickformat": ",.0f"},
        hovermode="x unified",
        legend_title_text="",
    )
    st.plotly_chart(comparison_figure, use_container_width=True)


def render_simulation(data: pd.DataFrame) -> None:
    """Simule une hausse de fréquentation pendant les quatre mois les plus creux."""
    st.title("Chapitre 4 : Outil de simulation (Hors-saison)")
    st.markdown(
        "Simulez l'impact d'une politique de promotion touristique ciblée sur les "
        "mois dits 'creux' (basse saison) pour lisser la fréquentation annuelle."
    )

    if data.empty:
        st.info("Aucune donnée ne correspond aux filtres sélectionnés.")
        return

    monthly_data = data[
        data["Mois_No"].between(1, 12)
        & data["Nuitees"].notna()
        & data["Region_Nom"].notna()
    ].copy()
    regions = sorted(monthly_data["Region_Nom"].unique().tolist())
    if monthly_data.empty or not regions:
        st.info("Aucune donnée mensuelle disponible pour lancer la simulation.")
        return

    region = st.selectbox(
        "Région à analyser",
        options=regions,
        index=0,
        key="simulation_region",
    )
    region_data = monthly_data[monthly_data["Region_Nom"] == region].copy()

    month_names = [
        "Janvier",
        "Février",
        "Mars",
        "Avril",
        "Mai",
        "Juin",
        "Juillet",
        "Août",
        "Septembre",
        "Octobre",
        "Novembre",
        "Décembre",
    ]
    month_labels = (
        region_data[["Mois_No", "Mois_Nom"]]
        .dropna()
        .drop_duplicates("Mois_No")
        .set_index("Mois_No")["Mois_Nom"]
        .to_dict()
    )
    historical_by_year = (
        region_data.groupby(["Annee", "Mois_No"], as_index=False)["Nuitees"]
        .sum()
    )
    monthly_history = (
        historical_by_year.groupby("Mois_No", as_index=False)["Nuitees"]
        .mean()
        .rename(columns={"Nuitees": "Nuitees_Historiques"})
    )
    simulation = pd.DataFrame({"Mois_No": range(1, 13)})
    simulation["Mois_Nom"] = simulation["Mois_No"].map(
        lambda month_number: month_labels.get(month_number, month_names[month_number - 1])
    )
    simulation = simulation.merge(monthly_history, on="Mois_No", how="left")
    simulation["Nuitees_Historiques"] = simulation["Nuitees_Historiques"].fillna(0)

    low_season_months = (
        simulation.nsmallest(4, "Nuitees_Historiques")["Mois_No"].tolist()
    )
    low_season_names = simulation.loc[
        simulation["Mois_No"].isin(low_season_months), "Mois_Nom"
    ].tolist()
    st.info(
        f"Mois de basse saison identifiés pour {region} : "
        f"{', '.join(low_season_names)}"
    )

    increase = st.slider(
        "Hypothèse : Augmentation des nuitées en basse saison (%)",
        min_value=0,
        max_value=100,
        value=20,
        step=5,
        key="simulation_increase",
    )
    simulation["Nuitees_Simulees"] = simulation["Nuitees_Historiques"]
    low_season_mask = simulation["Mois_No"].isin(low_season_months)
    simulation.loc[low_season_mask, "Nuitees_Simulees"] *= 1 + increase / 100

    annual_history = simulation["Nuitees_Historiques"].sum()
    annual_simulation = simulation["Nuitees_Simulees"].sum()
    estimated_gain = annual_simulation - annual_history
    kpi_columns = st.columns(3)
    kpi_columns[0].metric(
        "Total annuel Historique",
        f"{annual_history:,.0f}".replace(",", " "),
    )
    kpi_columns[1].metric(
        "Total annuel Simulé",
        f"{annual_simulation:,.0f}".replace(",", " "),
    )
    kpi_columns[2].metric(
        "Gain total estimé",
        f"{estimated_gain:,.0f}".replace(",", " "),
        delta=f"+{estimated_gain:,.0f}".replace(",", " "),
    )

    chart_data = simulation.melt(
        id_vars=["Mois_No", "Mois_Nom"],
        value_vars=["Nuitees_Historiques", "Nuitees_Simulees"],
        var_name="Scenario",
        value_name="Nuitees",
    )
    chart_data["Scenario"] = chart_data["Scenario"].replace(
        {
            "Nuitees_Historiques": "Historique",
            "Nuitees_Simulees": "Simulation",
        }
    )
    simulation_figure = px.bar(
        chart_data,
        x="Mois_Nom",
        y="Nuitees",
        color="Scenario",
        barmode="group",
        category_orders={
            "Mois_Nom": simulation["Mois_Nom"].tolist(),
            "Scenario": ["Historique", "Simulation"],
        },
        color_discrete_map={"Historique": "#7D8A99", "Simulation": "#E67E22"},
        labels={"Mois_Nom": "Mois", "Nuitees": "Nuitées", "Scenario": ""},
    )
    simulation_figure.update_layout(
        xaxis={"categoryorder": "array", "categoryarray": simulation["Mois_Nom"].tolist()},
        yaxis={"tickformat": ",.0f", "title": "Nuitées moyennes"},
        legend_title_text="",
    )
    st.plotly_chart(simulation_figure, use_container_width=True)


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
    elif chapter == "Chapitre 3 : Typologie & Saisonnalité":
        render_typologie(filtered_data)
    elif chapter == "Chapitre 4 : Outil de simulation":
        render_simulation(filtered_data)


if __name__ == "__main__":
    main()
