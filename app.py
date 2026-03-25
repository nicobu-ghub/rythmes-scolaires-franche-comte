import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

from data import load_data, filter_data, FC_DEPARTMENTS, DATA_LAST_UPDATED

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Rythmes scolaires — Franche-Comté",
    page_icon="🏫",
    layout="wide",
)

COULEURS = {"4 jours": "#58BEE9", "4,5 jours": "#A8DDD3"}

# ── CSS responsive ────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Réduction des marges globales sur mobile ── */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 1rem !important;
        }

        /* Titre principal plus compact */
        h1 { font-size: 1.4rem !important; }
        h2, h3 { font-size: 1.1rem !important; }

        /* Colonnes de métriques : empilées verticalement */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 0 !important;
        }

        /* Métriques : texte plus grand pour lisibilité */
        [data-testid="stMetricValue"] {
            font-size: 1.6rem !important;
        }
        [data-testid="stMetricDelta"] {
            font-size: 0.95rem !important;
        }

        /* Carte pleine largeur et hauteur réduite */
        iframe {
            height: 320px !important;
        }

        /* Graphiques Plotly : hauteur réduite */
        .js-plotly-plot {
            max-height: 300px;
        }

        /* Tableau : police plus petite */
        [data-testid="stDataFrame"] {
            font-size: 0.75rem !important;
        }

        /* Bouton téléchargement pleine largeur */
        [data-testid="stDownloadButton"] > button {
            width: 100% !important;
        }

        /* Divider moins d'espace */
        hr { margin: 0.5rem 0 !important; }
    }

    /* ── Badges de couleur rythme dans le tableau ── */
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Chargement ───────────────────────────────────────────────────────────────
df_all = load_data()

if df_all.empty:
    st.error("Impossible de charger les données.")
    st.stop()

# ── Sidebar — filtres ─────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Filtres")

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
        "Licence Ouverte v2.0 (Etalab)  \n"
        f"Données mises à jour : **{DATA_LAST_UPDATED}**"
    )

# ── Données filtrées ──────────────────────────────────────────────────────────
df = filter_data(df_all, dept_sel, type_sel)

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
col1.metric("Total écoles", f"{total:,}".replace(",", "\u202f"))
col2.metric(
    "4 jours",
    f"{n_4j:,}".replace(",", "\u202f"),
    delta=f"{pct_4j:.1f} %",
    delta_color="off",
)
col3.metric(
    "4,5 jours",
    f"{n_45j:,}".replace(",", "\u202f"),
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
    color = COULEURS.get(row["rythme"], "#999")
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
        fill_opacity=0.85,
        tooltip=folium.Tooltip(tooltip),
    ).add_to(m)

legend_html = f"""
<div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
     background: white; padding: 10px 15px; border-radius: 8px;
     box-shadow: 0 2px 6px rgba(0,0,0,.25); font-size: 13px; line-height: 1.8;">
  <b>Rythme scolaire</b><br>
  <span style="color:{COULEURS['4 jours']}; font-size:18px;">&#9679;</span>&nbsp;4 jours<br>
  <span style="color:{COULEURS['4,5 jours']}; font-size:18px;">&#9679;</span>&nbsp;4,5 jours
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, width="100%", height=480, returned_objects=[])

st.divider()

# ── Graphiques ────────────────────────────────────────────────────────────────
# Sur mobile les colonnes se réduisent automatiquement ; on utilise [1,1]
# pour que le camembert et le bar chart soient visuellement équilibrés
col_pie, col_bar = st.columns([1, 1])

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
    fig_pie.update_traces(textinfo="percent+value", textfont_size=13)
    fig_pie.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        showlegend=True,
        legend=dict(orientation="h", y=-0.15),
        height=300,
    )
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
    fig_bar.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        legend=dict(orientation="h", y=-0.25),
        legend_title_text="",
        xaxis_tickangle=-30,
        height=300,
    )
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
fig_type.update_layout(
    margin=dict(t=10, b=10, l=10, r=10),
    legend=dict(orientation="h", y=-0.25),
    legend_title_text="",
    xaxis_tickangle=-20,
    height=320,
)
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
    height=380,
)

csv = df[cols_display].to_csv(index=False).encode("utf-8")
st.download_button(
    label="Télécharger les données (CSV)",
    data=csv,
    file_name="rythmes_scolaires_franche_comte.csv",
    mime="text/csv",
    use_container_width=True,
)
