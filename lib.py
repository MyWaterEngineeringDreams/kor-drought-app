"""Shared data loaders, labels and plotting helpers for the app."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.colors as pc
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data"

SCEN = {"ssp126": "SSP1-2.6", "ssp245": "SSP2-4.5", "ssp585": "SSP5-8.5"}
SCEN_COL = {"ssp126": "#1d7a4c", "ssp245": "#e6a532", "ssp585": "#b2252a"}
PERIOD = {"near": "2021–2050", "mid": "2041–2070", "far": "2071–2100"}
PET = {"PM": "Penman–Monteith", "PMco2": "Penman–Monteith (CO₂)", "HS": "Hargreaves–Samani", "TH": "Thornthwaite"}
INDEX_INFO = {
    "SPEI-1": "Atmosphere, 1-month climatic water balance (P − PET)",
    "SPEI-3": "Atmosphere, 3-month climatic water balance",
    "SPEI-6": "Atmosphere, 6-month climatic water balance",
    "SPEI-9": "Atmosphere, 9-month climatic water balance (reservoir time scale)",
    "SPEI-12": "Atmosphere, 12-month climatic water balance",
    "SMDI": "Soil moisture, 0–100 cm (GLDAS-2.1 Noah)",
    "SRI-1": "Runoff, 1 month (GR2M)",
    "SRI-3": "Runoff, 3 months (GR2M)",
    "SRI-6": "Runoff, 6 months (GR2M)",
    "SRI-12": "Runoff, 12 months (GR2M)",
    "SRSI": "Reservoir storage (K-water dams, regulated basins)",
    "SGI": "Groundwater level (GIMS monitoring wells)",
    "GWDI": "Groundwater storage (GLDAS-2.2, GRACE data assimilation)",
    "WSDI": "Total water storage (GLDAS-2.2, GRACE data assimilation)",
}
LAYER_COL = {"SMDI": "#a6611a", "SRI-1": "#80cdc1", "SRSI": "#1f78b4", "SGI (alluvial)": "#e9c46a",
             "SGI (bedrock)": "#2a9d8f", "SGI": "#018571", "GWDI": "#9e9ac8", "WSDI": "#6a51a3"}
DIVERGING = [[0, "#8c2d04"], [0.25, "#e6550d"], [0.45, "#fdd0a2"], [0.5, "#f7f7f7"],
             [0.55, "#c6dbef"], [0.75, "#3182bd"], [1, "#08306b"]]


# change in drought frequency: fewer droughts blue, more droughts red
DRYWET = [[0, "#08306b"], [0.25, "#4292c6"], [0.5, "#f7f7f7"], [0.75, "#ef6548"], [1, "#99000d"]]
# standardized index: dry red, wet blue
INDEX_SCALE = [[0, "#99000d"], [0.25, "#ef6548"], [0.5, "#f7f7f7"], [0.75, "#4292c6"], [1, "#08306b"]]


def nice(b):
    return b.replace("JejuIsland", "Jeju")


def _clockwise(ring):
    """Plotly's geo maps (d3-geo) need clockwise exterior rings; GeoJSON files are usually counter-clockwise."""
    a = sum((x2 - x1) * (y2 + y1) for (x1, y1), (x2, y2) in zip(ring[:-1], ring[1:]))
    return ring if a > 0 else ring[::-1]


def _rewind(geom):
    if geom["type"] == "Polygon":
        polys = [geom["coordinates"]]
    else:
        polys = geom["coordinates"]
    out = [[_clockwise(p[0])] + [_clockwise(h)[::-1] for h in p[1:]] for p in polys]
    return {"type": "MultiPolygon", "coordinates": out}


@st.cache_data
def geojson():
    gj = json.loads((DATA / "basins.geojson").read_text(encoding="utf-8"))
    for f in gj["features"]:
        f["geometry"] = _rewind(f["geometry"])
    return gj


@st.cache_data
def basins():
    gj = geojson()
    rows = [f["properties"] for f in gj["features"]]
    return pd.DataFrame(rows)


@st.cache_data
def table(name):
    f = DATA / name
    d = pd.read_parquet(f) if f.suffix == ".parquet" else pd.read_csv(f)
    if "date" in d.columns:
        d["date"] = pd.to_datetime(d["date"])
    return d


def basin_order():
    return basins().basin.tolist()


def layout(fig, h=420, legend=True, **kw):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=40, b=10), template="plotly_white",
                      font=dict(size=13), showlegend=legend, legend=dict(orientation="h", y=-0.15),
                      hoverlabel=dict(font_size=12), **kw)
    return fig


def basin_map(df, value, title, colorscale="Viridis", midpoint=None, fmt=".1f", unit=""):
    """Basin map drawn as filled polygons: no tile server, map library or internet access needed."""
    gj = geojson()
    d = basins()[["basin", "area_km2"]].merge(df[["basin", value]], on="basin", how="left").set_index("basin")
    z = d[value].astype(float)
    if midpoint is not None:
        lim = np.nanmax(np.abs(z - midpoint)) if np.isfinite(z).any() else 1
        zmin, zmax = midpoint - lim, midpoint + lim
    else:
        zmin, zmax = (np.nanmin(z), np.nanmax(z)) if np.isfinite(z).any() else (0, 1)
    if zmax == zmin:
        zmax = zmin + 1
    scale = pc.get_colorscale(colorscale) if isinstance(colorscale, str) else colorscale
    fig = go.Figure()
    for f in gj["features"]:
        b = f["properties"]["basin"]
        v = z.get(b, np.nan)
        col = "#e6e6e6" if not np.isfinite(v) else pc.sample_colorscale(scale, [(v - zmin) / (zmax - zmin)])[0]
        txt = (f"<b>{nice(b)}</b><br>{title}: " + (f"{v:{fmt}}{unit}" if np.isfinite(v) else "no data") +
               f"<br>Area: {d.area_km2.get(b, np.nan):,.0f} km²")
        xs, ys = [], []
        for poly in f["geometry"]["coordinates"]:            # all parts of a basin in one trace, split by None
            ring = poly[0]
            xs += [p[0] for p in ring] + [None]
            ys += [p[1] for p in ring] + [None]
        fig.add_trace(go.Scatter(x=xs, y=ys, fill="toself", fillcolor=col, mode="lines",
                                 line=dict(color="#555", width=0.6), hoveron="fills", text=txt,
                                 hoverinfo="text", showlegend=False, name=nice(b)))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", showlegend=False, hoverinfo="skip",
                             marker=dict(colorscale=scale, cmin=zmin, cmax=zmax, color=[zmin], showscale=True,
                                         colorbar=dict(title=dict(text=unit.strip(), side="right"), thickness=14,
                                                       len=0.8))))
    fig.update_xaxes(visible=False, range=[125.0, 130.0])
    fig.update_yaxes(visible=False, range=[33.0, 38.7], scaleanchor="x", scaleratio=1 / np.cos(np.deg2rad(36)))
    fig.update_layout(height=600, margin=dict(l=0, r=0, t=36, b=0), template="plotly_white", hovermode="closest",
                      title=dict(text=title, x=0.01, font=dict(size=15)), plot_bgcolor="white")
    return fig


def footer():
    st.divider()
    st.caption("Results are part of a manuscript under review. Please do not cite or redistribute without "
               "permission. Derived basin-level results only; raw K-water, GIMS, ERA5, GLDAS and CMIP6 data are "
               "not included.")
