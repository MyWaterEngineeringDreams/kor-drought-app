import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

import lib

st.title("Basin explorer")
st.caption("Monthly drought indices of every layer for one basin. Values ≤ −1 mark drought (red); dashed line at −1.")

I = lib.table("indices.parquet")
W = lib.table("water_balance.parquet")
order = lib.basin_order()
available = [i for i in lib.INDEX_INFO if i in set(I["index"])]

with st.sidebar:
    st.header("Selection")
    basin = st.selectbox("Basin", order, format_func=lib.nice)
    have = I[I.basin == basin]["index"].unique()
    default = [i for i in ("SPEI-3", "SMDI", "SRI-3", "SRSI", "SGI", "GWDI") if i in have]
    idx = st.multiselect("Indices", [i for i in available if i in have], default=default)
    yr = st.slider("Years", 1981, 2025, (2003, 2025))
    thr = st.slider("Drought threshold", -2.0, -0.5, -1.0, 0.1)

if not idx:
    st.info("Choose at least one index in the sidebar.")
    st.stop()

d = I[(I.basin == basin) & I["index"].isin(idx) & (I.date.dt.year.between(*yr))]
fig = make_subplots(rows=len(idx), cols=1, shared_xaxes=True, vertical_spacing=0.025,
                    subplot_titles=[f"{i}: {lib.INDEX_INFO.get(i, '')}" for i in idx])
for r, i in enumerate(idx, 1):
    s = d[d["index"] == i].sort_values("date")
    col = np.where(s.value <= thr, "#c0392b", np.where(s.value < 0, "#f0a58f", "#5b8fc7"))
    fig.add_trace(go.Bar(x=s.date, y=s.value, marker_color=col, marker_line_width=0, name=i,
                         hovertemplate="%{x|%b %Y}: %{y:.2f}<extra>" + i + "</extra>"), row=r, col=1)
    fig.add_hline(y=thr, line_dash="dash", line_color="#555", line_width=1, row=r, col=1)
    fig.update_yaxes(range=[-3.2, 3.2], row=r, col=1, title_text="")
fig.update_annotations(font_size=12, x=0, xanchor="left")
st.plotly_chart(lib.layout(fig, 150 * len(idx) + 80, legend=False, bargap=0), width="stretch")

# drought statistics for the selection
st.subheader(f"Drought statistics, {lib.nice(basin)}, {yr[0]}–{yr[1]}")
rows = []
for i in idx:
    s = d[d["index"] == i].set_index("date").value.sort_index()
    dry = s <= thr
    runs = (dry != dry.shift()).cumsum()[dry]
    lengths = runs.value_counts()
    rows.append({"Index": i, "Months": len(s), "Drought months (%)": round(100 * dry.mean(), 1),
                 "Events": int(lengths.size), "Longest event (months)": int(lengths.max()) if lengths.size else 0,
                 "Minimum": round(s.min(), 2), "Date of minimum": s.idxmin().strftime("%Y-%m") if len(s) else ""})
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

# water balance
st.subheader("Water balance and reservoir fill")
w = W[(W.basin == basin) & (W.date.dt.year.between(*yr))]
fig = make_subplots(specs=[[{"secondary_y": True}]])
for n, c in (("P", "#2c7fb8"), ("PET", "#e6550d"), ("Q (GR2M)", "#31a354")):
    s = w[w["index"] == n].sort_values("date")
    fig.add_trace(go.Scatter(x=s.date, y=s.value, name=f"{n} (mm/month)", line=dict(color=c, width=1.3)))
f = w[w["index"] == "Fill (%)"].sort_values("date")
if len(f):
    fig.add_trace(go.Scatter(x=f.date, y=f.value, name="Reservoir fill (%)", line=dict(color="#6a51a3", width=1.6,
                             dash="dot")), secondary_y=True)
    fig.update_yaxes(title_text="Reservoir fill (%)", range=[0, 105], tickmode="linear", tick0=0, dtick=20,
                     showgrid=False, secondary_y=True)
fig.update_yaxes(title_text="mm/month", secondary_y=False)
st.plotly_chart(lib.layout(fig, 380), width="stretch")

c1, c2 = st.columns(2)
c1.download_button("Download indices (CSV)", d.pivot(index="date", columns="index", values="value").to_csv(),
                   file_name=f"indices_{basin}.csv", mime="text/csv")
c2.download_button("Download water balance (CSV)", w.pivot(index="date", columns="index", values="value").to_csv(),
                   file_name=f"water_balance_{basin}.csv", mime="text/csv")
lib.footer()
