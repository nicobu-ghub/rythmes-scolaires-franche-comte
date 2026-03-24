import requests
import pandas as pd
import streamlit as st
from pathlib import Path

API_URL = (
    "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets"
    "/fr-en-organisation-du-temps-scolaire/records"
)
API_EXPORT_URL = (
    "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets"
    "/fr-en-organisation-du-temps-scolaire/exports/csv"
)
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StreamlitApp/1.0)"}

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

# Chemin du CSV bundlé dans le repo (fallback si l'API est inaccessible)
_BUNDLED_CSV = Path(__file__).parent / "data_fc.csv"


def _fetch_api() -> pd.DataFrame:
    """Fetch all records from the API with pagination."""
    records = []
    limit = 100
    offset = 0
    while True:
        resp = requests.get(
            API_URL,
            params={"where": DEPT_FILTER, "limit": limit, "offset": offset},
            headers=HEADERS,
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
    df = pd.DataFrame(records)
    df.columns = [c.lower() for c in df.columns]
    return df


def _load_bundled_csv() -> pd.DataFrame:
    """Load the bundled CSV (columns are uppercase, normalise to lowercase)."""
    df = pd.read_csv(_BUNDLED_CSV, low_memory=False)
    df.columns = [c.lower() for c in df.columns]
    return df


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Add rythme, departement_nom and type_ecole columns."""
    if df.empty:
        return df

    # Libellé de département lisible
    df["departement_nom"] = df["code_departement"].astype(str).map(
        FC_DEPARTMENTS
    ).fillna(df.get("departement", "Inconnu"))

    # Classification 4j / 4,5j
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
        "MATERNELLE": "École maternelle",
        "ELEMENTAIRE": "École élémentaire",
    }
    if "code_nature" in df.columns:
        df["type_ecole"] = (
            df["code_nature"].astype(str).map(nature_map).fillna(df["code_nature"])
        )
    else:
        df["type_ecole"] = "Non renseigné"

    # Coordonnées numériques
    for col in ("latitude", "longitude"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # code_departement normalisé sur 3 chiffres (au cas où le CSV envoie un int)
    df["code_departement"] = df["code_departement"].astype(str).str.zfill(3)

    return df


@st.cache_data(ttl=3600, show_spinner="Chargement des données…")
def load_data() -> pd.DataFrame:
    """Load data: try live API first, fall back to bundled CSV."""
    try:
        df = _fetch_api()
        if df.empty:
            raise ValueError("API returned empty dataset")
    except Exception as exc:
        if _BUNDLED_CSV.exists():
            st.warning(
                f"API inaccessible ({exc}). Données chargées depuis le fichier local "
                f"(dernière mise à jour : jan. 2026).",
                icon="⚠️",
            )
            df = _load_bundled_csv()
        else:
            st.error(f"Impossible de charger les données : {exc}")
            return pd.DataFrame()

    return _enrich(df)


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
