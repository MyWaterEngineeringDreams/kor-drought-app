import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import lib

st.title("Drought from the atmosphere to the aquifer")
st.markdown("##### Observation-constrained hydrological modelling of drought propagation across the 21 river "
            "basins of South Korea, 2003–2025, with projections to 2100")

c = st.columns(5)
c[0].metric("River basins", "21", help="All major basins of South Korea, 99,361 km²")
c[1].metric("Gauges / dams", "5 / 32", help="GR2M calibrated at 5 main-stem gauges, validated at 32 dam inflows")
c[2].metric("Monitoring wells", "422", help="144 alluvial and 278 bedrock wells (GIMS)")
c[3].metric("Reservoir memory", "9 months", help="Median integration time of reservoir storage (SRSI)")
c[4].metric("GCMs", "10 of 20", help="NEX-GDDP-CMIP6 models selected by skill; SSP1-2.6, SSP2-4.5, SSP5-8.5")

st.subheader("Key findings")
k = st.columns(4)
k[0].info("**Fast natural response.** Runoff, soil moisture and groundwater integrate only 2–4 months of "
          "climatic deficit and respond in the same month.")
k[1].info("**Persistent reservoir deficits.** Reservoirs integrate about 9 months of deficit and lag runoff "
          "by about one month.")
k[2].warning("**Non-climatic groundwater decline.** 36 % of wells decline beyond what climate explains, "
             "most in the agricultural south-west.")
k[3].error("**Little relief under warming.** More rain by 2071–2100, but rising evaporative demand cancels it "
           "at the reservoir time scale under SSP5-8.5.")

left, right = st.columns([1.15, 1])
with left:
    st.subheader("Basin map")
    reg = lib.table("regulation.csv")
    att = lib.table("gw_attribution_basin.csv")
    it = lib.table("integration_time.csv")
    pb = lib.table("proj_basin.parquet")
    opt = st.selectbox("Show", ["Degree of regulation (%)", "Groundwater residual trend (cm/yr)",
                                "Wells with non-climatic decline (%)", "Groundwater integration time (months)",
                                "Projected change in SPEI-9 drought frequency (pp)", "Mean annual runoff, GR2M (mm/yr)"])
    if opt.startswith("Degree"):
        fig = lib.basin_map(reg.rename(columns={"DOR_SRSI_pct": "v"}).fillna({"v": 0}), "v", opt, "Blues", unit=" %")
    elif opt.startswith("Groundwater residual"):
        fig = lib.basin_map(att.rename(columns={"trend_residual_cm_yr": "v"}), "v", opt, lib.DIVERGING, 0, ".2f", " cm/yr")
    elif opt.startswith("Wells"):
        d = att.assign(v=att.share_declining * 100)
        fig = lib.basin_map(d, "v", opt, "OrRd", unit=" %", fmt=".0f")
    elif opt.startswith("Groundwater integration"):
        d = it[it.layer == "SGI"].rename(columns={"best_scale": "v"})
        fig = lib.basin_map(d, "v", opt, "YlGnBu", fmt=".0f", unit=" months")
    elif opt.startswith("Projected"):
        s = st.radio("Scenario", list(lib.SCEN), format_func=lib.SCEN.get, horizontal=True, index=2)
        d = pb[(pb.pet == "PM") & (pb.period == "far") & (pb.scenario == s)].groupby("basin")["dfreq_SPEI-9"].median()
        fig = lib.basin_map(d.rename("v").reset_index(), "v", f"{opt}, {lib.SCEN[s]}, 2071–2100",
                            lib.DRYWET, 0, ".1f", " pp")
    else:
        fig = lib.basin_map(reg.rename(columns={"runoff_mm_yr": "v"}), "v", opt, "Teal", fmt=".0f", unit=" mm/yr")
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("Integration time by layer")
    st.caption("SPEI accumulation period (months) that best explains each layer, across basins.")
    order = ["SRI-1", "SMDI", "SGI (alluvial)", "SGI (bedrock)", "SGI", "GWDI", "WSDI", "SRSI"]
    fig = go.Figure()
    for l in [o for o in order if (it.layer == o).any()]:
        v = it[it.layer == l].best_scale
        fig.add_trace(go.Box(x=v, name=f"{l} ({len(v)})", marker_color=lib.LAYER_COL.get(l, "#888"),
                             boxpoints="all", jitter=0.4, pointpos=0, orientation="h",
                             hovertemplate="%{x} months<extra></extra>"))
    fig.update_xaxes(title="Best-matching SPEI accumulation (months)")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(lib.layout(fig, 470, legend=False), width="stretch")
    st.caption("SRI-1: runoff; SMDI: soil; SGI: groundwater wells; GWDI, WSDI: GLDAS-2.2 storage; SRSI: reservoirs.")

lib.footer()
