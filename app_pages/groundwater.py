import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import lib

st.title("Groundwater and the human imprint")
st.caption("Observed groundwater levels at 422 national monitoring wells and GRACE storage are compared with the "
           "storage expected from climate alone; the residual trend is the non-climatic signal (Sen's slope, "
           "modified Mann–Kendall test, block bootstrap).")

A = lib.table("gw_attribution_basin.csv")
G = lib.table("gw_attribution_region.csv")
GS = lib.table("groundwater_summary.csv")
SR = lib.table("storage_regions.parquet")
SA = lib.table("storage_attribution.csv")
order = lib.basin_order()

c = st.columns(4)
nat = G.set_index("region").loc["National (excl. Jeju)"]
c[0].metric("Wells (excl. Jeju)", f"{int(nat.n_wells)}")
c[1].metric("Climate share of variance", f"{nat.climate_R2_median * 100:.0f} %", help="Median R² of the climate model")
c[2].metric("Wells with non-climatic decline", f"{nat.share_declining * 100:.0f} %")
c[3].metric("Median residual trend", f"{nat.trend_residual_cm_yr:+.2f} cm/yr")

tab1, tab2, tab3 = st.tabs(["Trends by basin", "Map", "GRACE and climate-only storage"])
with tab1:
    a = A.set_index("basin").reindex([b for b in order if b in set(A.basin)]).reset_index()
    y = a.basin.map(lib.nice)
    fig = go.Figure()
    for col, name, colr in (("trend_obs_cm_yr", "observed", "#8c8c8c"), ("trend_climate_cm_yr", "climate-expected", "#2a9d8f"),
                            ("trend_residual_cm_yr", "residual (non-climatic)", "#c8553d")):
        fig.add_trace(go.Bar(x=a[col], y=y, name=name, orientation="h", marker_color=colr,
                             hovertemplate="%{y}: %{x:+.2f} cm/yr<extra>" + name + "</extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="Median level trend, 2003–2025 (cm/yr)", zeroline=True, zerolinecolor="#444")
    l, r = st.columns([1.3, 1])
    l.plotly_chart(lib.layout(fig, 700, title="Observed, climate-expected and residual trends"), width="stretch")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=a.share_declining * 100, y=y, orientation="h", name="decline", marker_color="#c8553d"))
    fig.add_trace(go.Bar(x=-a.share_rising * 100, y=y, orientation="h", name="rise", marker_color="#4f86c6"))
    fig.update_layout(barmode="relative")
    fig.update_yaxes(autorange="reversed", showticklabels=False)
    fig.update_xaxes(title="Wells with significant non-climatic trend (%)")
    r.plotly_chart(lib.layout(fig, 700, title="Share of wells"), width="stretch")

with tab2:
    m = st.radio("Show", ["Wells with non-climatic decline (%)", "Residual trend (cm/yr)", "Climate share of variance (%)",
                          "Response time, median (months)"], horizontal=True)
    if m.startswith("Wells"):
        fig = lib.basin_map(A.assign(v=A.share_declining * 100), "v", m, "OrRd", fmt=".0f", unit=" %")
    elif m.startswith("Residual"):
        fig = lib.basin_map(A.rename(columns={"trend_residual_cm_yr": "v"}), "v", m, lib.DIVERGING, 0, ".2f", " cm/yr")
    elif m.startswith("Climate"):
        fig = lib.basin_map(A.assign(v=A.climate_R2_median * 100), "v", m, "Greens", fmt=".0f", unit=" %")
    else:
        fig = lib.basin_map(GS.rename(columns={"q_max_median": "v"}), "v", m, "YlGnBu", fmt=".0f", unit=" months")
    st.plotly_chart(fig, width="stretch")
    st.caption("Basin-level summaries only; individual well locations are not shown.")

with tab3:
    reg = st.radio("Region", ["Han", "South", "National"], horizontal=True, index=1)
    model = st.radio("Climate-only model", ["GLDAS-2.1 Noah", "GR2M"], horizontal=True)
    s = SR[SR.region == reg].pivot(index="date", columns="series", values="mm").sort_index()
    roll = lambda x: x.rolling(12, center=True, min_periods=9).mean()
    fig = go.Figure()
    for n, colr, w in (("GRACE", "#111", 2.4), (f"{model} expected", "#2a9d8f", 1.6), (model, "#e9a03b", 1.2),
                       ("GLDAS-2.2 (GRACE-DA)", "#9aa5b1", 1.2)):
        if n in s:
            fig.add_trace(go.Scatter(x=s.index, y=roll(s[n]), name=n, line=dict(color=colr, width=w)))
    if f"{model} residual" in s:
        fig.add_trace(go.Scatter(x=s.index, y=roll(s[f"{model} residual"]), name="observed minus climate-expected",
                                 line=dict(color="#c8553d", width=2, dash="dash")))
    fig.add_hline(y=0, line_color="#888", line_width=1)
    fig.update_yaxes(title="Storage anomaly, 12-month mean (mm)")
    st.plotly_chart(lib.layout(fig, 460), width="stretch")
    t = SA[(SA.region == reg) & (SA.climate_model == model)]
    if len(t):
        t = t.iloc[0]
        k = st.columns(4)
        k[0].metric("Observed trend", f"{t.trend_obs:+.2f} mm/yr", help=f"p = {t.p_obs:.3f}")
        k[1].metric("Climate-expected trend", f"{t.trend_expected:+.2f} mm/yr", help=f"p = {t.p_expected:.3f}")
        k[2].metric("Residual trend", f"{t.trend_residual:+.2f} mm/yr", help=f"p = {t.p_residual:.3f}")
        k[3].metric("95 % bootstrap interval", f"{t.ci_lo:+.1f} to {t.ci_hi:+.1f}")
lib.footer()
