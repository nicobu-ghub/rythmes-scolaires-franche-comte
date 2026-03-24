import requests
import pandas as pd
import streamlit as st

API_URL = (
    "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets"
    "/fr-en-organisation-du-temps-scolaire/records"
)

# Départements historiques de Franche-Comté
FC_DEPARTMENTS = {
    "025": "Doubs",
    "039": "Jura",
    "070": "Haute-Saône",
    "090": "Territoire de Belfort",
}

DEPT_FILTER = " OR ".join(
    f'code_departement="{code}"' for code in FC_DEPARTMENTS.keys()
)


def _fetch_all(where: str) -> list[dict]:
    """Paginated fetch of all records matching a ODSQL where clause."""
    records = []
    limit = 100
    offset = 0
    while True:
        resp = requests.get(
            API_URL,
            params={"where": where, "limit": limit, "offset": offset},
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        batch = payload.get("results", [])
        records.extend(batch)
        total = payload.get("total_count", 0)
        offset += limit
        if offset >= total:
            break
    return records


@st.cache_data(ttl=3600, show_spinner="Chargement des données depuis l'API…")
def load_data() -> pd.DataFrame:
    records = _fetch_all(DEPT_FILTER)
    df = pd.DataFrame(records)

    if df.empty:
        return df

    # Normalise les colonnes en minuscules (l'API retourne parfois des majuscules)
    df.columns = [c.lower() for c in df.columns]

    # Libellé de département lisible
    df["departement_nom"] = df["code_departement"].map(FC_DEPARTMENTS).fillna(
        df.get("departement", "Inconnu")
    )

    # Classification 4j / 4,5j
    # Un créneau renseigné = une chaîne non vide / non nulle
    def has_slot(col: str) -> pd.Series:
        if col not in df.columns:
            return pd.Series(False, index=df.index)
        return df[col].notna() & (df[col].astype(str).str.strip() != "")

    df["rythme"] = "4 jours"
    mask_45 = has_slot("mercredi_matin_debut") | has_slot("samedi_matin_debut")
    df.loc[mask_45, "rythme"] = "4,5 jours"

    # Type d'école lisible
    nature_map = {
        "101": "École maternelle",
        "151": "École maternelle publique",
        "152": "École maternelle privée",
        "201": "École élémentaire",
        "251": "École élémentaire publique",
        "252": "École élémentaire privée",
        "300": "École primaire",
        "351": "École primaire publique",
        "352": "École primaire privée",
    }
    if "code_nature" in df.columns:
        df["type_ecole"] = df["code_nature"].map(nature_map).fillna(df["code_nature"])
    else:
        df["type_ecole"] = "Non renseigné"

    # Coordonnées
    for col in ("latitude", "longitude"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def filter_data(
    df: pd.DataFrame,
    annee: str | None,
    departements: list[str],
    types: list[str],
) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)

    if annee and annee != "Toutes" and "annee_scolaire" in df.columns:
        mask &= df["annee_scolaire"] == annee

    if departements:
        mask &= df["departement_nom"].isin(departements)

    if types:
        mask &= df["type_ecole"].isin(types)

    return df[mask].copy()
