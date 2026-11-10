# Drought propagation in 21 Korean river basins: interactive results

Interactive companion to the manuscript *Atmosphere-to-aquifer drought propagation reveals persistent reservoir
deficits, non-climatic groundwater decline and little relief under future warming in South Korea* (under review).

The app shows derived, basin-level results only: drought indices for every hydrological layer, propagation
statistics, reservoir regulation and storage, groundwater attribution, and CMIP6 projections. Raw K-water, GIMS,
ERA5, GLDAS and NEX-GDDP-CMIP6 data are not included.

| Page | Content |
|---|---|
| Overview | Key findings, basin maps of the main metrics, integration time by layer |
| Basin explorer | Monthly indices, drought statistics and GR2M water balance for any basin; CSV download |
| Propagation | Lagged correlation, coupling by basin, integration time, spatial representativeness |
| Reservoirs | Degree of regulation, SRSI by basin, reservoir fill through the major droughts |
| Groundwater and human imprint | Observed, climate-expected and residual well trends; GRACE against climate-only storage |
| Future drought | Ensemble changes by SSP, period and PET formulation; basin maps; model ranking |
| Data and methods | Data sources, GR2M performance, reproducibility |

## Run locally

```bash
cd App
python -m venv .venv
.venv\Scripts\activate            # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The app opens at http://localhost:8501.

## Refresh the data

After rerunning the workflow, regenerate `App/data` from the project root:

```bash
cd Code
python 15_export_app_data.py
```

`run_all.py` runs this step automatically at the end of the processing chain.

## Publish to GitHub (private repository)

1. Create a new **private** repository on GitHub, for example `kor-drought-app`, without a README.
2. From the `App` folder:

   ```bash
   git init
   git add .
   git commit -m "Interactive results app"
   git branch -M main
   git remote add origin https://github.com/MyWaterEngineeringDreams/kor-drought-app.git
   git push -u origin main
   ```

   GitHub Desktop works as well: *File → Add local repository → App*, then *Publish repository* with
   "Keep this code private" ticked.

Only the `App` folder goes into this repository. The processing code, inputs and manuscript stay local.

## Deploy on Streamlit Community Cloud

1. Sign in at https://share.streamlit.io with the same GitHub account and authorise access to private repositories.
2. *Create app → Deploy a public app from GitHub*: repository `MyWaterEngineeringDreams/kor-drought-app`, branch `main`,
   main file `streamlit_app.py`. Choose a custom subdomain if wanted.
3. In the app's *Settings → Sharing*, keep the app **private** and invite reviewers or co-authors by email.
   Only invited accounts can open it.
4. Every push to `main` redeploys the app.

After acceptance, make the repository public, set sharing to public, add the article DOI to the
*Data and methods* page and archive a release on Zenodo for a citable DOI.

## Structure

```
App/
├── streamlit_app.py        navigation and page setup
├── lib.py                  data loaders, labels, colour scales, basin map
├── app_pages/              one script per page
├── data/                   derived tables written by 15_export_app_data.py
├── .streamlit/config.toml  theme
└── requirements.txt
```

## Citation

Manuscript under review. Please contact the authors before citing or reusing these results.
