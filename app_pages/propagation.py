import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import lib

st.title("Drought propagation through the layers")
st.caption("Lagged correlation between a driver and a response layer, 2003–2025, with significance from the "
           "effective sample size. Integration time is the SPEI accumulation period that best matches a layer.")

L = lib.table("propagation_lags.parquet")
S = lib.table("propagation_summary.csv")
IT = lib.table("integration_time.csv")
order = lib.basin_order()
pairs = S.pair.tolist()

tab1, tab2, tab3 = st.tabs(["Lagged correlation", "Coupling by basin", "Integration time"])
with tab1:
    sel = st.multiselect("Driver → response", pairs, default=["SPEI-3 → SRI-3", "SRI-3 → SRSI", "SRI-3 → SGI", "SMDI → SGI"])
    band = st.toggle("Show interquartile range across basins", True)
    fig = go.Figure()
    cols = px.colors.qualitative.D3
    for k, p in enumerate(sel):
        g = L[L.pair == p].groupby("lag").r
        med, q1, q3 = g.median(), g.quantile(0.25), g.quantile(0.75)
        c = cols[k % len(cols)]
        if band:
            fig.add_trace(go.Scatter(x=list(med.index) + list(med.index[::-1]), y=list(q3) + list(q1[::-1]),
                                     fill="toself", fillcolor=c, opacity=0.15, line=dict(width=0), showlegend=False,
                                     hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=med.index, y=med, name=p, mode="lines+markers", line=dict(color=c, width=2.2),
                                 hovertemplate="lag %{x} months: r = %{y:.2f}<extra>" + p + "</extra>"))
    fig.add_hline(y=0, line_color="#888", line_width=1)
    fig.update_xaxes(title="Lag (months)", dtick=1)
    fig.update_yaxes(title="Median r across basins", range=[-0.15, 1])
    st.plotly_chart(lib.layout(fig, 460), width="stretch")
    st.dataframe(S.rename(columns={"pair": "Driver → response", "median_r": "Median r (best lag)",
                                   "median_lag": "Median best lag (months)", "sig_basins": "Significant basins",
                                   "n": "Basins", "median_r_lag0": "Median r at lag 0"}),
                 hide_index=True, width="stretch")

with tab2:
    best = L.loc[L.groupby(["basin", "pair"]).r.idxmax()]
    what = st.radio("Show", ["r at best lag", "Best lag (months)"], horizontal=True)
    v = "r" if what.startswith("r") else "lag"
    H = best.pivot(index="basin", columns="pair", values=v).reindex(index=order, columns=pairs)
    fig = go.Figure(go.Heatmap(z=H.values, x=H.columns, y=[lib.nice(b) for b in H.index],
                               colorscale="Viridis" if v == "r" else "Magma_r", zmin=0, zmax=1 if v == "r" else 6,
                               colorbar=dict(title=what), hovertemplate="%{y}<br>%{x}<br>" + what + ": %{z}<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(lib.layout(fig, 640, legend=False), width="stretch")
    st.caption("Blank cells: basins without a reservoir index (SRSI pairs).")

with tab3:
    lay = [l for l in ["SRI-1", "SMDI", "SGI (alluvial)", "SGI (bedrock)", "SGI", "GWDI", "WSDI", "SRSI"] if (IT.layer == l).any()]
    fig = go.Figure()
    for l in lay:
        g = IT[IT.layer == l]
        fig.add_trace(go.Box(y=g.best_scale, name=l, marker_color=lib.LAYER_COL.get(l), boxpoints="all", jitter=0.5,
                             customdata=np.stack([g.basin.map(lib.nice), g.r], axis=1),
                             hovertemplate="%{customdata[0]}: %{y} months (r = %{customdata[1]:.2f})<extra></extra>"))
    fig.update_yaxes(title="Integration time (months)")
    st.plotly_chart(lib.layout(fig, 460, legend=False), width="stretch")
    M = IT.pivot(index="basin", columns="layer", values="best_scale").reindex(index=order, columns=lay)
    M.index = [lib.nice(b) for b in M.index]
    st.dataframe(M, width="stretch")

st.subheader("Are basin means representative?")
dl = lib.table("decorrelation_length.csv")
c1, c2 = st.columns([1.5, 1])
c1.dataframe(dl.rename(columns={"scale": "SPEI/SPI scale (months)", "L_km": "L, ERA5 (km)", "n_pairs": "Cell pairs",
                                "L_km_ASOS_SPI": "L, ASOS stations (km)"}), hide_index=True, width="stretch")
c2.markdown("Drought is organised over **295–610 km**, larger than any basin (equivalent diameters **25–181 km**), "
            "so basin-mean indices represent the drought felt across each basin.")
lib.footer()
