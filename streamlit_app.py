"""Drought propagation across the 21 river basins of South Korea: interactive results.

Run locally:  streamlit run streamlit_app.py
"""
import streamlit as st

st.set_page_config(page_title="Korea drought propagation", page_icon="💧", layout="wide",
                   initial_sidebar_state="expanded")

pages = {
    "Study": [
        st.Page("app_pages/overview.py", title="Overview", icon=":material/water_drop:", default=True),
        st.Page("app_pages/basin_explorer.py", title="Basin explorer", icon=":material/query_stats:"),
    ],
    "Results": [
        st.Page("app_pages/propagation.py", title="Propagation", icon=":material/timeline:"),
        st.Page("app_pages/reservoirs.py", title="Reservoirs", icon=":material/water:"),
        st.Page("app_pages/groundwater.py", title="Groundwater and human imprint", icon=":material/layers:"),
        st.Page("app_pages/projections.py", title="Future drought", icon=":material/thermostat:"),
    ],
    "About": [
        st.Page("app_pages/methods.py", title="Data and methods", icon=":material/menu_book:"),
    ],
}
st.navigation(pages).run()
