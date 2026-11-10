import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import lib

st.title("Reservoirs carry the most persistent deficits")
st.caption("Storage of K-water dams reconstructed from daily water balances; SRSI is the standardized storage "
           "index. A reservoir index is used where effective storage exceeds 2 % of mean annual runoff.")

R = lib.table("regulation.csv")
I = lib.table("indices.parquet")
W = lib.table("water_balance.parquet")
order = lib.basin_order()

c1, c2 = st.columns([1, 1.25])
with c1:
    r = R.set_index("basin").reindex(order).reset_index()
    r["DOR"] = r.DOR_SRSI_pct
    col = ["#1f5fa8" if m else "#b8c4d6" for m in r.SRSI_main_text.fillna(False)]
    fig = go.Figure(go.Bar(x=r.DOR, y=r.basin.map(lib.nice), orientation="h", marker_color=col,
                           customdata=r[["n_dams_SRSI", "eff_storage_SRSI_MCM", "runoff_mm_yr"]].values,
                           hovertemplate="%{y}<br>Regulation: %{x:.1f} %<br>Dams: %{customdata[0]:.0f}<br>"
                                         "Effective storage: %{customdata[1]:,.0f} 10⁶ m³<br>Runoff: %{customdata[2]:.0f} mm/yr<extra></extra>"))
    fig.add_vline(x=2, line_dash="dash", line_color="#c0392b")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="Degree of regulation (% of mean annual runoff)", type="log",
                     tickvals=[0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100], ticktext=["0.1", "0.2", "0.5", "1", "2", "5", "10", "20", "50", "100"])
    st.plotly_chart(lib.layout(fig, 600, legend=False, title="Degree of regulation (dark: reservoir index used)"),
                    width="stretch")
with c2:
    s = I[I["index"] == "SRSI"].pivot(index="date", columns="basin", values="value")
    s = s[[b for b in order if b in s.columns]]
    fig = go.Figure(go.Heatmap(z=s.T.values, x=s.index, y=[lib.nice(b) for b in s.columns], colorscale=lib.INDEX_SCALE,
                               zmin=-2.5, zmax=2.5, colorbar=dict(title="SRSI"),
                               hovertemplate="%{y}<br>%{x|%b %Y}: %{z:.2f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(lib.layout(fig, 600, legend=False, title="SRSI by basin"), width="stretch")

st.subheader("Reservoir fill")
have = sorted(W[W["index"] == "Fill (%)"].basin.unique(), key=order.index)
sel = st.multiselect("Basins", have, default=[b for b in ("Han", "Nakdong", "Geum", "Seomjin") if b in have],
                     format_func=lib.nice)
smooth = st.toggle("3-month running mean", True)
fig = go.Figure()
for b in sel:
    f = W[(W.basin == b) & (W["index"] == "Fill (%)")].set_index("date").value.sort_index()
    if smooth:
        f = f.rolling(3, center=True, min_periods=2).mean()
    fig.add_trace(go.Scatter(x=f.index, y=f, name=lib.nice(b), mode="lines"))
for a, z in (("2008-09", "2009-06"), ("2014-06", "2016-03"), ("2017-03", "2017-08"), ("2022-03", "2023-06")):  # as in 03d
    fig.add_vrect(x0=a, x1=z, fillcolor="#999", opacity=0.15, line_width=0)
fig.update_yaxes(title="Effective storage filled (%)", range=[0, 105])
st.plotly_chart(lib.layout(fig, 420), width="stretch")
st.caption("Grey bands: major drought periods. Fill falls furthest in the 2008–09, 2014–16 and 2022–23 droughts, "
           "and recovers more slowly than runoff in the southern systems.")
lib.footer()
