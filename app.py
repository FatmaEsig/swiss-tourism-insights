"""Application Streamlit de visualisation du tourisme suisse."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

MONTH_NAMES = [
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

# Coordonnées indicatives des centres des régions touristiques OFS.
# Elles servent uniquement au repérage spatial, pas à représenter une frontière.
REGION_COORDINATES = {
    "Suisse": (46.80, 8.23),
    "Grisons": (46.70, 9.60),
    "Suisse orientale": (47.35, 9.25),
    "Région zurichoise": (47.38, 8.54),
    "R�gion zurichoise": (47.38, 8.54),
    "Lucerne / Lac des Quatre Cantons": (46.98, 8.25),
    "Région Bâloise": (47.56, 7.59),
    "R�gion B�loise": (47.56, 7.59),
    "Région Berne": (46.95, 7.45),
    "Jura & Trois-Lacs": (47.10, 7.05),
    "Vaud": (46.62, 6.63),
    "Genève": (46.20, 6.14),
    "Gen�ve": (46.20, 6.14),
    "Valais": (46.25, 7.55),
    "Tessin": (46.15, 8.95),
    "Fribourg": (46.80, 7.15),
    "Région Argovie et Soleure": (47.40, 8.05),
    "R�gion Argovie et Soleure": (47.40, 8.05),
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


def annual_rows(data: pd.DataFrame) -> pd.DataFrame:
    """Retourne une ligne annuelle par année et région sans double comptage."""
    annual = data[data["Mois_No"] == 0].copy()
    if not annual.empty:
        return annual
    return data[data["Mois_No"].between(1, 12)].copy()


def analysis_rows(data: pd.DataFrame) -> pd.DataFrame:
    """Évite de compter l'agrégat Suisse avec ses régions détaillées."""
    rows = annual_rows(data)
    regional_rows = rows[rows["Region_Nom"] != "Suisse"].copy()
    return regional_rows if not regional_rows.empty else rows


def format_number(value: float) -> str:
    """Formate un nombre avec des espaces, lisibles en français."""
    return f"{value:,.0f}".replace(",", " ")


def filter_context(data: pd.DataFrame) -> str:
    """Construit un résumé court des filtres visibles dans les titres."""
    years = sorted(data["Annee"].dropna().astype(int).unique().tolist())
    regions = data["Region_Nom"].dropna().nunique()
    if not years:
        return "aucune donnée"
    period = str(years[0]) if len(years) == 1 else f"{years[0]}–{years[-1]}"
    return f"{period} · {regions} région(s) sélectionnée(s)"


def render_source_note() -> None:
    """Explique la source OFS et les transformations réalisées dans le projet."""
    with st.expander("Source des données et méthode", expanded=False):
        st.markdown(
            """
            **Source :** Office fédéral de la statistique (OFS), statistiques de
            l'hôtellerie suisse. Les fichiers bruts sont
            `data/raw/OFS_offre_demande.xlsx` et `data/raw/OFS_provenance.xlsx`.

            **Préparation réalisée dans ce projet :** les en-têtes Excel complexes
            ont été aplatis, les valeurs fusionnées ont été propagées, puis les
            deux fichiers ont été fusionnés sur l'année, le mois et la région.
            Le résultat est `data/processed/master_data.csv`.

            **Précaution :** une *nuitée* correspond à une nuit passée dans un
            établissement, tandis qu'une *arrivée* correspond à l'arrivée d'un
            client. Le taux d'occupation est exprimé en pourcentage. Les
            coordonnées de la carte sont des points indicatifs des régions.
            """
        )


def render_overview(data: pd.DataFrame) -> None:
    """Affiche le chapitre 1 : carte spatiale et évolution temporelle."""
    st.title(
        "Chapitre 1 : Vue d'ensemble de la fréquentation touristique suisse "
        f"({filter_context(data)})"
    )

    if data.empty:
        st.info("Aucune donnée ne correspond aux filtres sélectionnés.")
        return

    annual = annual_rows(data)
    national_rows = annual[annual["Region_Nom"] == "Suisse"]
    total_nights = (
        national_rows["Nuitees"].sum()
        if not national_rows.empty
        else annual["Nuitees"].sum()
    )
    average_occupancy = (
        national_rows["Taux_occupation_chambres_pct"].mean()
        if not national_rows.empty
        else annual["Taux_occupation_chambres_pct"].mean()
    )
    metric_columns = st.columns(2)
    metric_columns[0].metric(
        "Nuitées totales sur la période",
        format_number(total_nights),
        help="Nombre total de nuits passées dans les hébergements, sur la période filtrée.",
    )
    metric_columns[1].metric(
        "Taux moyen d'occupation des chambres",
        f"{average_occupancy:.1f} %",
        help="Part moyenne des chambres disponibles qui ont été occupées.",
    )
    st.caption(
        "Une nuitée correspond à une nuit passée dans un hébergement. "
        "Le taux d'occupation indique la part des chambres utilisées."
    )

    st.subheader("Repérage spatial des nuitées")
    st.markdown(
        "Chaque cercle représente une région sélectionnée : sa **taille** indique "
        "le volume de nuitées et sa **couleur** le taux moyen d'occupation. "
        "Les points sont des centres indicatifs, et non les frontières régionales."
    )
    map_data = (
        annual.groupby("Region_Nom", as_index=False)
        .agg(
            Nuitees=("Nuitees", "sum"),
            Taux_occupation_chambres_pct=("Taux_occupation_chambres_pct", "mean"),
        )
    )
    if (map_data["Region_Nom"] != "Suisse").any():
        map_data = map_data[map_data["Region_Nom"] != "Suisse"].copy()
    map_data[["Latitude", "Longitude"]] = map_data["Region_Nom"].map(
        REGION_COORDINATES
    ).apply(pd.Series)
    map_data = map_data.dropna(subset=["Latitude", "Longitude"])

    if map_data.empty:
        st.info("Aucune région ne peut être positionnée sur la carte.")
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
            size_max=38,
            zoom=6.5,
            center={"lat": 46.8, "lon": 8.2},
            map_style="carto-positron",
            labels={
                "Nuitees": "Nuitées",
                "Taux_occupation_chambres_pct": "Occupation moyenne (%)",
            },
        )
        map_figure.update_layout(
            height=500,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            coloraxis_colorbar_title="Occupation (%)",
        )
        st.plotly_chart(map_figure, use_container_width=True)
        st.caption(
            f"{len(map_data)} région(s) affichée(s). La carte sert au repérage "
            "géographique ; les positions sont indicatives."
        )

    st.subheader("Évolution des nuitées")
    st.markdown(
        "La vue nationale est proposée par défaut pour éviter la superposition de "
        "14 courbes. Le mode comparaison est limité à quatre régions."
    )
    monthly_data = data[data["Mois_No"].between(1, 12)].copy()
    if monthly_data.empty:
        st.info("Aucune donnée mensuelle disponible pour l'évolution temporelle.")
        return
    chart_mode = st.radio(
        "Niveau de lecture",
        ["Total des régions sélectionnées", "Comparer des régions"],
        horizontal=True,
    )
    if chart_mode == "Comparer des régions":
        available_regions = sorted(monthly_data["Region_Nom"].unique().tolist())
        comparison_regions = st.multiselect(
            "Régions à comparer (4 maximum)",
            available_regions,
            default=available_regions[:4],
        )
        if not comparison_regions:
            st.info("Sélectionnez au moins une région pour afficher la courbe.")
            return
        if len(comparison_regions) > 4:
            st.warning("Seules les quatre premières régions sont affichées.")
            comparison_regions = comparison_regions[:4]
        timeline_data = (
            monthly_data[monthly_data["Region_Nom"].isin(comparison_regions)]
            .groupby(["Annee", "Mois_No", "Region_Nom"], as_index=False)["Nuitees"]
            .sum()
        )
        color_column = "Region_Nom"
    else:
        timeline_data = (
            monthly_data.groupby(["Annee", "Mois_No"], as_index=False)["Nuitees"]
            .sum()
        )
        color_column = None

    timeline_data["Temps"] = pd.to_datetime(
        timeline_data["Annee"].astype(str)
        + "-"
        + timeline_data["Mois_No"].astype(str)
        + "-01",
        format="%Y-%m-%d",
    )

    timeline_figure = px.line(
        timeline_data.sort_values("Temps"),
        x="Temps",
        y="Nuitees",
        color=color_column,
        labels={"Temps": "Mois", "Nuitees": "Nuitées", "Region_Nom": "Région"},
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    timeline_figure.update_layout(
        height=520,
        hovermode="x unified",
        yaxis={"tickformat": ",.0f", "title": "Nuitées totales"},
        legend_title_text="",
    )
    st.plotly_chart(timeline_figure, use_container_width=True)


def render_profils(data: pd.DataFrame) -> None:
    """Affiche les indicateurs de dépendance internationale et de séjour."""
    st.title(
        "Chapitre 2 : Analyser la demande et les profils de clientèle "
        f"({filter_context(data)})"
    )

    if data.empty:
        st.info("Aucune donnée ne correspond aux filtres sélectionnés.")
        return

    st.markdown(
        "Ce chapitre décrit **d'où viennent les nuitées** et **combien de nuits "
        "dure en moyenne un séjour**. Les calculs utilisent les lignes annuelles "
        "OFS pour éviter d'additionner deux fois les mêmes données."
    )
    profils = analysis_rows(data)[
        ["Region_Nom", "Nuitees", "Suisse_Nuitées", "Arrivees"]
    ].copy()
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
        provenance["Part_etrangere_pct"] = (
            provenance["Etranger_Nuitees"] / provenance["Total_Nuitees"] * 100
        )
        region_order = provenance.sort_values(
            "Part_etrangere_pct", ascending=True
        )["Region_Nom"].tolist()

        international_figure = px.bar(
            provenance_long,
            x="Pourcentage",
            y="Region_Nom",
            color="Provenance",
            orientation="h",
            text="Pourcentage",
            category_orders={
                "Region_Nom": region_order,
                "Provenance": ["Suisse", "Étranger"],
            },
            color_discrete_map={"Suisse": "#0072B2", "Étranger": "#E69F00"},
            labels={
                "Pourcentage": "Part des nuitées (%)",
                "Region_Nom": "Région",
                "Provenance": "Provenance",
            },
        )
        international_figure.update_layout(
            barmode="stack",
            height=620,
            xaxis={"range": [0, 100], "ticksuffix": "%"},
            legend_title_text="",
        )
        international_figure.update_traces(
            texttemplate="%{text:.0f} %",
            textposition="inside",
            insidetextanchor="middle",
        )
        st.subheader("Part des nuitées domestiques et internationales")
        st.markdown(
            "**Lecture :** chaque barre représente 100 % des nuitées de la région. "
            "« Suisse » correspond aux résidents suisses ; « Étranger » correspond "
            "à la différence entre les nuitées totales et les nuitées suisses. "
            "Une part étrangère élevée indique une plus grande dépendance aux marchés "
            "internationaux, pas nécessairement une meilleure performance."
        )
        st.plotly_chart(international_figure, use_container_width=True)
        most_international = provenance.loc[
            provenance["Part_etrangere_pct"].idxmax()
        ]
        most_domestic = provenance.loc[
            provenance["Part_etrangere_pct"].idxmin()
        ]
        st.info(
            f"**Analyse :** {most_international['Region_Nom']} présente la plus "
            f"forte part étrangère ({most_international['Part_etrangere_pct']:.1f} %), "
            f"tandis que {most_domestic['Region_Nom']} présente la plus forte part "
            f"suisse ({100 - most_domestic['Part_etrangere_pct']:.1f} %). "
            "Une action réaliste consiste à diversifier les marchés internationaux "
            "des régions dépendantes et à renforcer les offres nationales pendant "
            "les périodes creuses."
        )

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
        color_discrete_sequence=["#56B4E9"],
        labels={
            "Duree_Moyenne": "Durée moyenne (nuits par arrivée)",
            "Region_Nom": "Région",
        },
    )
    duration_figure.update_layout(
        showlegend=False,
        yaxis={"categoryorder": "array", "categoryarray": duree["Region_Nom"].tolist()},
    )
    st.subheader("Durée moyenne estimée d'un séjour")
    st.markdown(
        "**Calcul :** nuitées totales ÷ arrivées totales. Par exemple, une valeur "
        "de 2,0 signifie qu'une arrivée correspond en moyenne à deux nuits. "
        "Il s'agit d'une moyenne agrégée sur la période, pas de la durée de chaque "
        "séjour individuel."
    )
    st.plotly_chart(duration_figure, use_container_width=True)
    longest = duree.iloc[0]
    shortest = duree.iloc[-1]
    st.info(
        f"**Analyse :** la durée moyenne est la plus élevée à {longest['Region_Nom']} "
        f"({longest['Duree_Moyenne']:.1f} nuits) et la plus faible à "
        f"{shortest['Region_Nom']} ({shortest['Duree_Moyenne']:.1f} nuits). "
        "Les séjours courts peuvent être ciblés par des offres de week-end ; "
        "les séjours longs par des offres de fidélisation ou de séjour prolongé."
    )


def render_typologie(data: pd.DataFrame) -> None:
    """Analyse la répartition mensuelle des nuitées par région."""
    st.title(
        "Chapitre 3 : Typologie et analyse de la saisonnalité "
        f"({filter_context(data)})"
    )

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
    if (monthly_data["Region_Nom"] != "Suisse").any():
        monthly_data = monthly_data[monthly_data["Region_Nom"] != "Suisse"].copy()

    st.markdown(
        "Cette vue compare la **répartition des nuitées dans l'année**, et non "
        "leur volume absolu. Ainsi, une petite région et une grande région sont "
        "comparées sur la même base : la somme des 12 cases d'une région vaut 100 %."
    )
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

    heatmap_values = (
        seasonal.pivot(index="Region_Nom", columns="Mois_Nom", values="Part_nuitees_pct")
        .reindex(columns=month_order)
        .fillna(0)
    )
    heatmap_figure = go.Figure(
        go.Heatmap(
            z=heatmap_values.to_numpy(),
            x=month_order,
            y=heatmap_values.index.tolist(),
            text=[[f"{value:.1f} %" for value in row] for row in heatmap_values.to_numpy()],
            texttemplate="%{text}",
            colorscale="Blues",
            colorbar={"title": "Part annuelle (%)"},
            hovertemplate=(
                "Région : %{y}<br>Mois : %{x}<br>"
                "Part des nuitées annuelles : %{z:.1f} %<extra></extra>"
            ),
        )
    )
    heatmap_figure.update_layout(
        xaxis_title="Mois",
        yaxis_title="Région",
        height=650,
    )
    heatmap_figure.update_layout(
        xaxis={"categoryorder": "array", "categoryarray": month_order},
    )
    st.subheader("Répartition mensuelle des nuitées par région")
    st.markdown(
        "**Lecture :** une case foncée signifie que le mois représente une part "
        "importante de l'année de cette région. La valeur affichée est un "
        "pourcentage, pas un nombre de nuitées. Cette normalisation met en évidence "
        "la saisonnalité, indépendamment de la taille de la région."
    )
    st.plotly_chart(heatmap_figure, use_container_width=True)

    concentration = (
        seasonal.groupby("Region_Nom", as_index=False)["Part_nuitees_pct"]
        .agg(
            Part_max="max",
            Part_min="min",
            Variabilite="std",
        )
        .sort_values("Variabilite", ascending=False)
    )
    most_seasonal = concentration.iloc[0]
    most_stable = concentration.iloc[-1]
    st.info(
        f"**Analyse :** {most_seasonal['Region_Nom']} est la région la plus "
        f"contrastée selon la dispersion mensuelle ({most_seasonal['Variabilite']:.1f} "
        f"points de pourcentage), tandis que {most_stable['Region_Nom']} est la "
        f"plus régulière ({most_stable['Variabilite']:.1f} points). "
        "Pour une région très saisonnière, une promotion ciblée sur les mois "
        "faibles est plus pertinente qu'une campagne uniforme toute l'année."
    )

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
    comparison["Mois_Nom"] = comparison["Mois_No"].map(
        dict(zip(month_labels["Mois_No"], month_labels["Mois_Nom"]))
    )
    comparison_figure = px.line(
        comparison,
        x="Mois_Nom",
        y="Nuitees",
        color="Region_Nom",
        markers=True,
        category_orders={"Mois_Nom": month_order},
        color_discrete_sequence=["#0072B2", "#E69F00"],
        labels={
            "Mois_Nom": "Mois",
            "Nuitees": "Nuitées cumulées sur la période",
            "Region_Nom": "Région",
        },
    )
    comparison_figure.update_layout(
        xaxis={"categoryorder": "array", "categoryarray": month_order},
        yaxis={"tickformat": ",.0f"},
        hovermode="x unified",
        legend_title_text="",
    )
    st.plotly_chart(comparison_figure, use_container_width=True)


def render_simulation(data: pd.DataFrame) -> None:
    """Simule une hausse de fréquentation pendant les quatre mois les plus creux."""
    st.title(
        "Chapitre 4 : Outil de simulation (Hors-saison) "
        f"({filter_context(data)})"
    )
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

    render_source_note()


if __name__ == "__main__":
    main()
