# =========================================================
# PREMIUM BRAND HEALTH DASHBOARD
# =========================================================

import streamlit as st
import duckdb
import pandas as pd
import re
import plotly.express as px
from streamlit_option_menu import option_menu

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Brand Health Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# PREMIUM UI
# =========================================================

st.markdown("""
<style>

/* MAIN APP */
.stApp {
    background: #f4f7fb;
}

.block-container {
    padding-top: 1rem;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 100%;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: white;
    border-right: 1px solid #e2e8f0;
}

/* TEXT */
html, body, p, div, span, label {
    color: #111827 !important;
}

h1,h2,h3,h4,h5,h6 {
    color: #0f172a !important;
}

/* FILTERS */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: white !important;
    border: 1px solid #dbe4f0 !important;
    border-radius: 18px !important;
    min-height: 56px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.stMultiSelect span[data-baseweb="tag"] {
    display: none !important;
}

.stSelectbox label,
.stMultiSelect label {
    font-weight: 700 !important;
}

/* METRIC CARDS */
.metric-card {
    background: white;
    border-radius: 24px;
    padding: 28px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 8px 24px rgba(15,23,42,0.08);
    transition: all 0.25s ease;
    min-height: 230px;
}

.metric-card:hover {
    transform: translateY(-5px);
}

.metric-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}

.metric-left {
    display: flex;
    flex-direction: column;
}

.metric-title {
    font-size: 14px;
    font-weight: 700;
    color: #64748b !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.metric-subtitle {
    font-size: 14px;
    color: #94a3b8 !important;
    margin-top: 6px;
}

.metric-badge {
    background: linear-gradient(135deg,#2563eb,#7c3aed);
    color: white !important;
    padding: 10px 16px;
    border-radius: 14px;
    font-size: 20px;
    font-weight: 800;
    box-shadow: 0 8px 18px rgba(37,99,235,0.25);
}

.metric-value {
    margin-top: 34px;
    font-size: 52px;
    font-weight: 800;
    color: #0f172a !important;
    line-height: 1;
}

.metric-progress {
    width: 100%;
    height: 12px;
    background: #e2e8f0;
    border-radius: 999px;
    overflow: hidden;
    margin-top: 28px;
}

.metric-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg,#8b5cf6,#3b82f6);
}

/* GRAPH CARD */
.graph-card {
    background: white;
    border-radius: 24px;
    padding: 24px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 8px 24px rgba(15,23,42,0.08);
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================

st.markdown("""
<h1 style='font-size:56px;font-weight:800;margin-bottom:0;'>
🚀 Brand Health Dashboard
</h1>

<p style='font-size:20px;color:#64748b;margin-top:0;'>
Interactive analytics platform for tracking brand performance
</p>
""", unsafe_allow_html=True)

# =========================================================
# FILES
# =========================================================

PARQUET_URL = "https://github.com/Dhana-max/Brand-Health_Dashboard/releases/download/v1/data.parquet"
MAP_FILE = "Map.xlsx"

# =========================================================
# CONNECTION
# =========================================================

@st.cache_resource
def get_connection():
    con = duckdb.connect()
    con.execute(f"""
        CREATE VIEW df AS
        SELECT * FROM read_parquet('{PARQUET_URL}')
    """)
    return con

con = get_connection()

# =========================================================
# LOAD MAP
# =========================================================

@st.cache_data
def load_map():
    df = pd.read_excel(MAP_FILE, header=1)
    df.columns = df.columns.astype(str).str.strip()
    return df

map_df = load_map()

# =========================================================
# ATTRIBUTE MAP
# =========================================================

attr_map = {
    1: "Helps me move forward professionally",
    2: "Helps me find the right job",
    3: "Helps me navigate professional life",
    4: "Place I feel I belong",
    5: "Cares about issues that matter",
    6: "Brand I love",
    7: "Brand I trust",
    8: "Part of a community",
    9: "Keeps me informed",
    10: "Professional discussions happen",
    11: "Useful every day",
    12: "Create/share content",
    13: "Using more frequently",
    14: "Useful for my job",
    15: "Helps me reach goals",
    16: "Locally relevant network",
    17: "Helps career/business growth"
}

# (rest of code unchanged...)

# ✅ ONLY IMPORTANT FIX BELOW (metric card)

st.markdown(f"""
<div class="metric-card">

    <div class="metric-header">

        <div class="metric-left">

            <div class="metric-title">
                {title}
            </div>

            <div class="metric-subtitle">
                KPI Score
            </div>

        </div>

        <div class="metric-badge">
            {value}
        </div>

    </div>

    <div class="metric-value">
        {value}%
    </div>

    <div class="metric-progress">
        <div class="metric-fill" style="width:{value}%"></div>
    </div>

</div>
""", unsafe_allow_html=True)

# ✅ ALSO FIX

st.markdown("<br>", unsafe_allow_html=True)

st.markdown('<div class="graph-card">', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
