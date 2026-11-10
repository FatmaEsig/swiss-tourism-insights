"""Vue transversale des indicateurs de fréquentation."""

import plotly.express as px
import streamlit as st

from app import analysis_rows, filter_context, load_data, render_source_note


data = load_data()
years = sorted(data["Annee"].dropna().astype(int).unique().tolist())
regions = sorted(data["Region_Nom"].dropna().unique().tolist())

with st.sidebar:
    selected_years = st.slider(
        "Période d'analyse",
        min_value=years[0],
        max_value=years[-1],
        value=(years[0], years[-1]),
        key="analyse_years",
    )
    selected_regions = st.multiselect(
        "Régions",
        regions,
        default=regions,
        key="analyse_regions",
    )

filtered = data[
    data["Annee"].between(*selected_years)
    & data["Region_Nom"].isin(selected_regions)
].copy()

st.title(f"Analyse des indicateurs ({filter_context(filtered)})")
st.markdown(
    "Cette page résume les volumes annuels. Les **nuitées** mesurent les nuits "
    "passées dans les hébergements ; les **arrivées** comptent les clients qui "
    "commencent un séjour."
)

if filtered.empty:
    st.info("Aucune donnée ne correspond aux filtres sélectionnés.")
else:
    annual = analysis_rows(filtered)
    total_nights = annual["Nuitees"].sum()
    total_arrivals = annual["Arrivees"].sum()
    duration = total_nights / total_arrivals if total_arrivals else 0
    columns = st.columns(3)
    columns[0].metric("Nuitées totales", f"{total_nights:,.0f}".replace(",", " "))
    columns[1].metric("Arrivées totales", f"{total_arrivals:,.0f}".replace(",", " "))
    columns[2].metric("Durée moyenne", f"{duration:.1f} nuitées / arrivée")

    ranking = (
        annual.groupby("Region_Nom", as_index=False)["Nuitees"]
        .sum()
        .sort_values("Nuitees", ascending=True)
    )
    figure = px.bar(
        ranking,
        x="Nuitees",
        y="Region_Nom",
        orientation="h",
        color_discrete_sequence=["#0072B2"],
        labels={"Nuitees": "Nuitées totales", "Region_Nom": "Région"},
    )
    figure.update_layout(
        height=600,
        showlegend=False,
        xaxis={"tickformat": ",.0f"},
    )
    st.subheader("Classement des régions par volume de nuitées")
    st.caption("Ce graphique compare les volumes ; il ne mesure pas la qualité ou la satisfaction.")
    st.plotly_chart(figure, use_container_width=True)

render_source_note()