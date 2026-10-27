# Joseph AI V3 — Free-data automatic matchup prototype

Select league, date, game, team, player. App attempts to fetch public ESPN schedules, team results, rosters and game logs. No manual projections required.

**Important limitations:** ESPN endpoints are unofficial, undocumented and can fail or change structure. Live endpoints were not testable from the build environment. NBA/NFL season schedules may have different schemas. Team projections are simple historical scoring baselines, not calibrated models. Injury adjustments, automated Hard Rock odds and automatic screenshot OCR are NOT included. App never fabricates missing data.

## Replace existing Streamlit app

Upload `app.py`, `data_sources.py`, `requirements.txt`, and `README.md` to the **root** of the existing GitHub repository. Choose replace/overwrite existing files where prompted; do not delete `app.py` first. Leave `matchups.py` in place (unused). Streamlit should redeploy `app.py` automatically.

## Run locally

`pip install -r requirements.txt`

`streamlit run app.py`
