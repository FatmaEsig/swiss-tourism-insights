"""Recommandations fondées sur la saisonnalité observée."""

import pandas as pd
import streamlit as st

from app import MONTH_NAMES, filter_context, load_data, render_source_note


data = load_data()
years = sorted(data["Annee"].dropna().astype(int).unique().tolist())
regions = sorted(data["Region_Nom"].dropna().unique().tolist())

with st.sidebar:
    selected_years = st.slider(
        "Période d'analyse",
        min_value=years[0],
        max_value=years[-1],
        value=(years[0], years[-1]),
        key="recommendations_years",
    )
    selected_regions = st.multiselect(
        "Régions",
        regions,
        default=regions,
        key="recommendations_regions",
    )

filtered = data[
    data["Annee"].between(*selected_years)
    & data["Region_Nom"].isin(selected_regions)
].copy()

st.title(f"Recommandations ({filter_context(filtered)})")
st.markdown(
    "Les recommandations ci-dessous sont des pistes de lecture basées sur les "
    "mois où le volume de nuitées est le plus faible. Elles ne constituent pas "
    "une prévision et doivent être complétées par des informations de terrain."
)

if filtered.empty:
    st.info("Aucune donnée ne correspond aux filtres sélectionnés.")
else:
    monthly = filtered[filtered["Mois_No"].between(1, 12)].copy()
    monthly = (
        monthly.groupby(["Region_Nom", "Mois_No"], as_index=False)["Nuitees"]
        .sum()
    )
    month_average = monthly.groupby("Mois_No", as_index=False)["Nuitees"].mean()
    quiet_months = month_average.nsmallest(4, "Nuitees")["Mois_No"].tolist()
    quiet_names = [MONTH_NAMES[month - 1] for month in quiet_months]

    st.subheader("Périodes prioritaires")
    st.info(
        "Les mois les moins fréquentés dans la sélection sont : "
        + ", ".join(quiet_names)
        + ". Ce sont les périodes les plus adaptées à une promotion ciblée."
    )

    region_summary = (
        monthly.groupby("Region_Nom", as_index=False)["Nuitees"]
        .agg(Nuitees_moyennes="mean", Variabilite="std")
    )
    region_summary["Variabilite"] = region_summary["Variabilite"].fillna(0)
    most_seasonal = region_summary.sort_values("Variabilite", ascending=False).iloc[0]

    columns = st.columns(2)
    columns[0].metric(
        "Région la plus saisonnière",
        str(most_seasonal["Region_Nom"]),
        help="Région présentant la plus forte dispersion de ses volumes mensuels.",
    )
    columns[1].metric(
        "Mois prioritaires",
        len(quiet_names),
        help="Nombre de mois retenus pour une action de promotion hors-saison.",
    )

    st.subheader("Pistes d'action")
    st.markdown(
        f"""
        1. **Cibler {', '.join(quiet_names)}** avec des offres adaptées aux
           clientèles locales et internationales.
        2. **Différencier les actions par région** : une région très saisonnière
           nécessite une promotion hors-saison plus forte qu'une région stable.
        3. **Mesurer l'effet** avec les nuitées, les arrivées et le taux
           d'occupation après chaque campagne.
        """
    )

render_source_note()