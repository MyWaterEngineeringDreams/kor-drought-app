import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import lib

st.title("Future drought, 2015–2100")
st.caption("Ten NEX-GDDP-CMIP6 models selected by skill, bias-corrected by quantile delta mapping and run through "
           "the calibrated GR2M model. Changes relative to each model's 1981–2014 baseline.")

E = lib.table("proj_ensemble.csv")
N = lib.table("proj_national.parquet")
B = lib.table("proj_basin.parquet")
T = lib.table("proj_trends.csv")
RS = lib.table("proj_regulated_spei9.csv")
RK = lib.table("gcm_ranking.csv")
order = lib.basin_order()

with st.sidebar:
    st.header("Scenario")
    scen = st.radio("SSP", list(lib.SCEN), format_func=lib.SCEN.get, index=1)
    per = st.radio("Period", list(lib.PERIOD), format_func=lib.PERIOD.get, index=2)
    pets = sorted(B[B.scenario == scen].pet.unique(), key=list(lib.PET).index)
    pet = st.selectbox("PET formulation", pets, format_func=lib.PET.get)

e = E[(E.scenario == scen) & (E.period == per) & (E.pet == pet)]
if len(e):
    e = e.iloc[0]
    c = st.columns(5)
    for col, (v, lab, u) in zip(c, (("dP_pct", "Precipitation", "%"), ("dT_C", "Temperature", "°C"), ("dPET_pct", "PET", "%"),
                                     ("dQ_pct", "Runoff (GR2M)", "%"), ("dfreq_SPEI-9", "SPEI-9 drought", "pp"))):
        col.metric(f"{lab}", f"{e[v + '_p50']:+.1f} {u}", help=f"Ensemble median; 10th–90th percentile "
                   f"{e[v + '_p10']:+.1f} to {e[v + '_p90']:+.1f} {u}; sign agreement {e[v + '_agree_pct']:.0f} %")
    st.caption(f"{lib.SCEN[scen]}, {lib.PERIOD[per]}, {lib.PET[pet]} PET. Hover a number for the model range.")

tab1, tab2, tab3, tab4 = st.tabs(["National indices", "Map by basin", "PET sensitivity", "Models"])
with tab1:
    idx = st.radio("Index", sorted(N["index"].unique()), horizontal=True, index=1)
    fig = go.Figure()
    for s in lib.SCEN:
        g = N[(N["index"] == idx) & (N.scenario == s)].pivot(index="year", columns="model", values="z")
        if g.empty:
            continue
        g = g.rolling(10, center=True, min_periods=5).mean()
        fig.add_trace(go.Scatter(x=list(g.index) + list(g.index[::-1]),
                                 y=list(g.quantile(.9, axis=1)) + list(g.quantile(.1, axis=1)[::-1]),
                                 fill="toself", fillcolor=lib.SCEN_COL[s], opacity=0.15, line=dict(width=0),
                                 showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=g.index, y=g.median(axis=1), name=lib.SCEN[s], line=dict(color=lib.SCEN_COL[s], width=2.2),
                                 hovertemplate="%{x}: %{y:.2f}<extra>" + lib.SCEN[s] + "</extra>"))
    fig.add_hline(y=0, line_color="#888", line_width=1)
    fig.add_vline(x=2014.5, line_dash="dash", line_color="#888")
    fig.update_yaxes(title=f"{idx}, 21-basin mean (10-yr running mean)")
    st.plotly_chart(lib.layout(fig, 460), width="stretch")
    st.caption("Line: ensemble median; band: 10th–90th percentile of the ten models. Positive = wetter.")
    t = T[T["index"] == idx].groupby("scenario").agg(median=("sen_per_decade", "median"),
                                                     significant=("p", lambda p: int((p < 0.05).sum())), models=("p", "size"))
    t.index = t.index.map(lib.SCEN).rename("Scenario")
    st.dataframe(t.rename(columns={"median": "Median trend 2015–2100 (per decade)", "significant": "Models with p < 0.05",
                                   "models": "Models"}).round(3), width="stretch")

with tab2:
    var = st.selectbox("Variable", ["dfreq_SPEI-9", "dfreq_SPEI-3", "dfreq_SPEI-12", "dfreq_SRI-3", "dP_pct", "dPET_pct", "dQ_pct", "dT_C"],
                       format_func=lambda v: {"dfreq_SPEI-9": "Δ SPEI-9 drought frequency (pp)", "dfreq_SPEI-3": "Δ SPEI-3 drought frequency (pp)",
                                              "dfreq_SPEI-12": "Δ SPEI-12 drought frequency (pp)", "dfreq_SRI-3": "Δ SRI-3 drought frequency (pp)",
                                              "dP_pct": "Δ precipitation (%)", "dPET_pct": "Δ PET (%)", "dQ_pct": "Δ runoff (%)",
                                              "dT_C": "Δ temperature (°C)"}[v])
    g = B[(B.scenario == scen) & (B.period == per) & (B.pet == pet)].groupby("basin")[var]
    d = pd.DataFrame({"v": g.median(), "agree": g.agg(lambda s: max((s > 0).mean(), (s < 0).mean()) * 100)}).reset_index()
    if var.startswith("dfreq"):
        fig = lib.basin_map(d, "v", f"Ensemble median, {lib.SCEN[scen]}, {lib.PERIOD[per]}", lib.DRYWET, 0, ".1f", " pp")
    elif var == "dT_C":
        fig = lib.basin_map(d, "v", f"Ensemble median, {lib.SCEN[scen]}, {lib.PERIOD[per]}", "OrRd", fmt=".1f", unit=" °C")
    else:
        fig = lib.basin_map(d, "v", f"Ensemble median, {lib.SCEN[scen]}, {lib.PERIOD[per]}",
                            "BrBG" if var != "dPET_pct" else "OrRd", 0 if var != "dPET_pct" else None, ".1f", " %")
    l, r = st.columns([1.3, 1])
    l.plotly_chart(fig, width="stretch")
    d["basin"] = d.basin.map(lib.nice)
    r.dataframe(d.rename(columns={"basin": "Basin", "v": "Median", "agree": "Sign agreement (%)"}).round(1),
                hide_index=True, width="stretch", height=520)

with tab3:
    st.markdown("Change in SPEI-9 drought frequency by PET formulation (sensitivity runs for SSP2-4.5 and SSP5-8.5).")
    fig = go.Figure()
    for s in ("ssp245", "ssp585"):
        x, y, lo, hi = [], [], [], []
        for p in lib.PET:
            v = B[(B.scenario == s) & (B.pet == p) & (B.period == per)]
            if v.empty:
                continue
            nat = v.groupby("model").apply(lambda q: np.nansum(q["dfreq_SPEI-9"] * q.w) / q.w.sum(), include_groups=False)
            x.append(lib.PET[p]); y.append(nat.median()); lo.append(nat.median() - nat.min()); hi.append(nat.max() - nat.median())
        fig.add_trace(go.Bar(x=x, y=y, name=lib.SCEN[s], marker_color=lib.SCEN_COL[s],
                             error_y=dict(type="data", symmetric=False, array=hi, arrayminus=lo, color="#333")))
    fig.add_hline(y=0, line_color="#444", line_width=1)
    fig.update_yaxes(title=f"Δ SPEI-9 drought frequency, {lib.PERIOD[per]} (pp)")
    st.plotly_chart(lib.layout(fig, 440, barmode="group"), width="stretch")
    st.info("Temperature-only Thornthwaite PET rises much faster than Penman–Monteith and turns the signal "
            "towards drying; the CO₂-adjusted formulation strengthens the wetting.")
    st.subheader("Regulated basins, SPEI-9")
    rs = RS[(RS.scenario == scen) & (RS.period == per)].copy()
    rs["basin"] = rs.basin.map(lib.nice)
    st.dataframe(rs.drop(columns=["scenario", "period"]).rename(columns={"basin": "Basin", "dP_pct": "ΔP (%)", "dPET_pct": "ΔPET (%)",
                 "dQ_pct": "ΔQ (%)", "dfreq_SPEI-9": "Δ SPEI-9 drought (pp)", "SPEI-9_agree_pct": "Sign agreement (%)"}),
                 hide_index=True, width="stretch")

with tab4:
    st.markdown("Raw-model skill against 92 ASOS stations, 1981–2014. Ten models were selected; BCC-CSM2-MR lacks "
                "relative humidity and was not eligible. CanESM5 and INM-CM5-0 were added to keep the ensemble envelope.")
    rk = RK.copy()
    st.dataframe(rk, hide_index=True, width="stretch")
lib.footer()
