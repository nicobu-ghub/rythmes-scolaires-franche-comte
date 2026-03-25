import pandas as pd
import streamlit as st
from pathlib import Path

# Départements historiques de Franche-Comté
FC_DEPARTMENTS = {
    "025": "Doubs",
    "039": "Jura",
    "070": "Haute-Saône",
    "090": "Territoire de Belfort",
}

# Date de la dernière mise à jour du fichier statique
DATA_LAST_UPDATED = "janvier 2026"

_BUNDLED_CSV = Path(__file__).parent / "data_fc.csv"


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


@st.cache_data(ttl=None, show_spinner="Chargement des données…")
def load_data() -> pd.DataFrame:
    """Load data from the bundled static CSV."""
    if not _BUNDLED_CSV.exists():
        st.error("Fichier de données introuvable.")
        return pd.DataFrame()
    return _enrich(_load_bundled_csv())


def filter_data(
    df: pd.DataFrame,
    departements: list[str],
    types: list[str],
) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)

    if departements:
        mask &= df["departement_nom"].isin(departements)

    if types:
        mask &= df["type_ecole"].isin(types)

    return df[mask].copy()
