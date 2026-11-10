"""Présentation du projet et de ses données."""

import streamlit as st

from src.dashboard_utils import render_source_note


st.title("À propos de Swiss Tourism Insights")
st.markdown(
    """
    ## Contexte

    Cette application a été réalisée dans le cadre d'un projet de visualisation
    des données touristiques suisses. Elle aide à comprendre les volumes de
    fréquentation, les profils de clientèle et la saisonnalité des régions.

    ## Objectifs

    - comparer les régions sur des indicateurs clairement définis ;
    - distinguer la clientèle résidente et étrangère ;
    - repérer les périodes de forte et de faible fréquentation ;
    - tester un scénario simple de promotion hors-saison.

    ## Équipe

    Projet développé par **Nolan, Tugba et Fatma** dans le cadre du cours de
    visualisation des données.

    ## Limites d'interprétation

    Les graphiques décrivent les données historiques disponibles. Une corrélation
    ne prouve pas une causalité et la simulation du chapitre 4 est un scénario
    pédagogique : elle ne tient pas compte des capacités hôtelières, des prix,
    de la météo ou des comportements de substitution.
    """
)
render_source_note()
