import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

from data import load_data, filter_data, FC_DEPARTMENTS

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Rythmes scolaires — Franche-Comté",
    page_icon="🏫",
    layout="wide",
)

COULEURS = {"4 jours": "#E74C3C", "4,5 jours": "#27AE60"}

# ── Chargement ───────────────────────────────────────────────────────────────
df_all = load_data()

if df_all.empty:
    st.error(
        "Impossible de charger les données depuis l'API de l'Éducation nationale. "
        "Vérifiez votre connexion internet et réessayez."
    )
    st.stop()

# ── Sidebar — filtres ─────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Filtres")

    annees = ["Toutes"]
    if "annee_scolaire" in df_all.columns:
        annees += sorted(df_all["annee_scolaire"].dropna().unique().tolist(), reverse=True)
    annee_sel = st.selectbox("Année scolaire", annees)

    dept_options = sorted(FC_DEPARTMENTS.values())
    dept_sel = st.multiselect(
        "Département(s)",
        options=dept_options,
        default=dept_options,
    )

    type_options = sorted(df_all["type_ecole"].dropna().unique().tolist())
    type_sel = st.multiselect(
        "Type d'école",
        options=type_options,
        default=type_options,
    )

    st.divider()
    st.caption(
        "Source : [data.education.gouv.fr](https://data.education.gouv.fr/explore/"
        "dataset/fr-en-organisation-du-temps-scolaire/)  \n"
        "Licence Ouverte v2.0 (Etalab)"
    )

# ── Données filtrées ──────────────────────────────────────────────────────────
df = filter_data(df_all, annee_sel, dept_sel, type_sel)

# ── Titre ─────────────────────────────────────────────────────────────────────
st.title("🏫 Rythmes scolaires en Franche-Comté")
st.markdown(
    "Répartition des écoles primaires entre **4 jours** et **4,5 jours** "
    "dans les départements du Doubs, Jura, Haute-Saône et Territoire de Belfort."
)

# ── KPIs ──────────────────────────────────────────────────────────────────────
total = len(df)
n_4j = (df["rythme"] == "4 jours").sum()
n_45j = (df["rythme"] == "4,5 jours").sum()

pct_4j = n_4j / total * 100 if total else 0
pct_45j = n_45j / total * 100 if total else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total écoles", f"{total:,}".replace(",", " "))
col2.metric(
    "4 jours",
    f"{n_4j:,}".replace(",", " "),
    delta=f"{pct_4j:.1f} %",
    delta_color="off",
)
col3.metric(
    "4,5 jours",
    f"{n_45j:,}".replace(",", " "),
    delta=f"{pct_45j:.1f} %",
    delta_color="off",
)

st.divider()

# ── Carte ─────────────────────────────────────────────────────────────────────
st.subheader("Carte des écoles")

df_map = df.dropna(subset=["latitude", "longitude"])

m = folium.Map(
    location=[47.3, 6.1],
    zoom_start=8,
    tiles="CartoDB positron",
)

for _, row in df_map.iterrows():
    color = "#E74C3C" if row["rythme"] == "4 jours" else "#27AE60"
    tooltip = (
        f"<b>{row.get('nom_etablissement', 'École')}</b><br>"
        f"Commune : {row.get('commune', '—')}<br>"
        f"Type : {row.get('type_ecole', '—')}<br>"
        f"Rythme : <b>{row['rythme']}</b>"
    )
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=5,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        tooltip=folium.Tooltip(tooltip),
    ).add_to(m)

# Légende
legend_html = """
<div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
     background: white; padding: 10px 15px; border-radius: 8px;
     box-shadow: 0 2px 6px rgba(0,0,0,.3); font-size: 13px;">
  <b>Rythme scolaire</b><br>
  <span style="color:#E74C3C;">&#9679;</span> 4 jours<br>
  <span style="color:#27AE60;">&#9679;</span> 4,5 jours
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, width="100%", height=520, returned_objects=[])

st.divider()

# ── Graphiques ────────────────────────────────────────────────────────────────
col_pie, col_bar = st.columns([1, 2])

with col_pie:
    st.subheader("Répartition globale")
    pie_data = df["rythme"].value_counts().reset_index()
    pie_data.columns = ["Rythme", "Nombre"]
    fig_pie = px.pie(
        pie_data,
        names="Rythme",
        values="Nombre",
        color="Rythme",
        color_discrete_map=COULEURS,
        hole=0.4,
    )
    fig_pie.update_traces(textinfo="percent+value")
    fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), showlegend=True)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_bar:
    st.subheader("Par département")
    bar_data = (
        df.groupby(["departement_nom", "rythme"])
        .size()
        .reset_index(name="Nombre")
    )
    fig_bar = px.bar(
        bar_data,
        x="departement_nom",
        y="Nombre",
        color="rythme",
        color_discrete_map=COULEURS,
        barmode="stack",
        labels={"departement_nom": "Département", "rythme": "Rythme"},
        text_auto=True,
    )
    fig_bar.update_layout(margin=dict(t=20, b=20), legend_title_text="Rythme")
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Répartition par type ──────────────────────────────────────────────────────
st.subheader("Par type d'école")
type_data = (
    df.groupby(["type_ecole", "rythme"])
    .size()
    .reset_index(name="Nombre")
)
fig_type = px.bar(
    type_data,
    x="type_ecole",
    y="Nombre",
    color="rythme",
    color_discrete_map=COULEURS,
    barmode="group",
    labels={"type_ecole": "Type d'école", "rythme": "Rythme"},
    text_auto=True,
)
fig_type.update_layout(margin=dict(t=20, b=20), legend_title_text="Rythme")
st.plotly_chart(fig_type, use_container_width=True)

st.divider()

# ── Tableau détaillé ──────────────────────────────────────────────────────────
st.subheader("Tableau détaillé")

cols_display = [
    c for c in [
        "nom_etablissement", "commune", "departement_nom",
        "type_ecole", "rythme", "annee_scolaire",
        "mercredi_matin_debut", "mercredi_matin_fin",
        "samedi_matin_debut", "samedi_matin_fin",
    ]
    if c in df.columns
]

st.dataframe(
    df[cols_display].rename(
        columns={
            "nom_etablissement": "École",
            "commune": "Commune",
            "departement_nom": "Département",
            "type_ecole": "Type",
            "rythme": "Rythme",
            "annee_scolaire": "Année",
            "mercredi_matin_debut": "Mer. début",
            "mercredi_matin_fin": "Mer. fin",
            "samedi_matin_debut": "Sam. début",
            "samedi_matin_fin": "Sam. fin",
        }
    ).reset_index(drop=True),
    use_container_width=True,
    height=400,
)

csv = df[cols_display].to_csv(index=False).encode("utf-8")
st.download_button(
    label="Télécharger les données (CSV)",
    data=csv,
    file_name="rythmes_scolaires_franche_comte.csv",
    mime="text/csv",
)
