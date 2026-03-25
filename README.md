# Rythmes scolaires — Franche-Comté

Dashboard Streamlit affichant la répartition des écoles primaires à **4 jours** ou **4,5 jours** dans les départements de Franche-Comté (Doubs, Jura, Haute-Saône, Territoire de Belfort).
Fait 100% avec cursor:
- plan pour acquisition des données
- mise en ligne avec github & streamlit (https://rythmes-scolaires-franche-comte.streamlit.app/)
- déboguage
- et analyse + filtrage des données source

## Source de données
[Organisation du temps scolaire — data.education.gouv.fr](https://data.education.gouv.fr/explore/dataset/fr-en-organisation-du-temps-scolaire/) — Licence Ouverte v2.0 (Etalab)

## Lancer en local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
