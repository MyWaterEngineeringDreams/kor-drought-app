import streamlit as st

import lib

st.title("Data and methods")

st.markdown("""
**Study design.** One observed or observation-constrained drought index per hydrological layer, tested for
spatial representativeness, linked by lagged correlation, and separated into climatic and non-climatic change.

| Layer | Data | Processing | Index |
|---|---|---|---|
| Climate | ERA5 monthly 0.25°, 1981–2025; 92 KMA-ASOS stations | Linear scaling to ASOS; FAO-56 Penman–Monteith PET | SPEI-k |
| Soil moisture | GLDAS-2.1 Noah, 0–100 cm | — | SMDI |
| Streamflow | 5 main-stem gauges, 2006–2025 | GR2M water balance: calibration 2011–17, validation 2018–25, check at 32 dam inflows | SRI-k |
| Reservoirs | K-water dams: daily inflow, release, level | Stage–storage reconstruction; degree of regulation | SRSI |
| Groundwater | GIMS national wells | Screening: 422 wells (144 alluvial, 278 bedrock) | SGI |
| Storage | GLDAS-2.2 CLSM (GRACE-DA); GRACE/GRACE-FO mascons | — | GWDI, WSDI, TWSA |
| Projections | NEX-GDDP-CMIP6, 20 GCMs, 3 SSPs | Skill ranking → 10 GCMs; quantile delta mapping; PET sensitivity | Projected SPEI, SRI |

**Statistics.** Lag correlation 0–12 months with effective-sample-size significance; integration time as the
best-matching SPEI accumulation; Sen's slope, modified Mann–Kendall test and block bootstrap for residual trends.
""")

st.subheader("GR2M calibration and validation")
p = lib.table("gr2m_performance.csv")
st.dataframe(p[["gauge", "area_km2", "X1", "X2", "KGE_cal", "NSE_cal", "PBIAS_cal", "KGE_val", "NSE_val", "PBIAS_val"]]
             .rename(columns={"gauge": "Gauge", "area_km2": "Area (km²)", "X1": "X1 (mm)", "X2": "X2",
                              "KGE_cal": "KGE cal", "NSE_cal": "NSE cal", "PBIAS_cal": "PBIAS cal (%)",
                              "KGE_val": "KGE val", "NSE_val": "NSE val", "PBIAS_val": "PBIAS val (%)"}),
             hide_index=True, width="stretch")

st.subheader("Reproducibility")
st.markdown("""
All results come from a scripted workflow (scripts 01–15, run in order by `run_all.py`). This app reads only the
derived, basin-level tables exported by `15_export_app_data.py`.

**Citation.** Manuscript under review. Please contact the authors before citing or reusing these results.
""")
lib.footer()
