# =========================================================
# PREMIUM BRAND HEALTH DASHBOARD
# SAME UI STYLE AS REFERENCE IMAGE
# LOGIC NOT CHANGED
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
# SOFT MODERN UI
# =========================================================

st.markdown("""
<style>

/* =====================================================
APP BACKGROUND
===================================================== */

.stApp {
    background: linear-gradient(135deg,#f8efef,#f5f7fb);
}

/* =====================================================
MAIN LAYOUT
===================================================== */

.block-container {
    padding-top: 1rem;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 100%;
}

/* =====================================================
SIDEBAR
===================================================== */

section[data-testid="stSidebar"] {
    background: #4b4d77;
    border-right: none;
    width: 280px !important;
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

section[data-testid="stSidebar"] .nav-link {
    border-radius: 12px !important;
    margin-bottom: 8px !important;
    font-size: 18px !important;
    padding: 12px !important;
}

section[data-testid="stSidebar"] .nav-link-selected {
    background: rgba(255,255,255,0.15) !important;
}

/* =====================================================
TITLE
===================================================== */

.main-title {
    font-size: 48px;
    font-weight: 800;
    color: #1f2937;
    margin-bottom: 0;
}

.main-subtitle {
    color: #64748b;
    font-size: 18px;
    margin-top: 0;
}

/* =====================================================
FILTERS
===================================================== */

.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: white !important;
    border: 1px solid #ececec !important;
    border-radius: 14px !important;
    min-height: 52px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.04);
}

.stMultiSelect span[data-baseweb="tag"] {
    display: none !important;
}

/* =====================================================
MAIN CARDS
===================================================== */

.metric-card {
    background: white;
    border-radius: 22px;
    padding: 24px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.06);
    min-height: 220px;
    border: 1px solid #f1f1f1;
    transition: 0.3s;
}

.metric-card:hover {
    transform: translateY(-4px);
}

.metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.metric-left {
    display: flex;
    flex-direction: column;
}

.metric-title {
    font-size: 14px;
    font-weight: 700;
    color: #7c8196 !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.metric-subtitle {
    font-size: 13px;
    color: #a1a1aa !important;
    margin-top: 4px;
}

.metric-badge {
    background: linear-gradient(135deg,#7c3aed,#2563eb);
    color: white !important;
    padding: 14px 18px;
    border-radius: 16px;
    font-size: 20px;
    font-weight: 800;
}

.metric-value {
    font-size: 52px;
    font-weight: 800;
    margin-top: 30px;
    color: #1f2937 !important;
}

.metric-progress {
    width: 100%;
    height: 10px;
    background: #ececec;
    border-radius: 999px;
    margin-top: 24px;
    overflow: hidden;
}

.metric-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg,#7c3aed,#2563eb);
}

/* =====================================================
GRAPH CARD
===================================================== */

.graph-card {
    background: white;
    border-radius: 24px;
    padding: 26px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.06);
    border: 1px solid #f1f1f1;
}

/* =====================================================
CHAT CARD
===================================================== */

.chat-card {
    background: white;
    border-radius: 24px;
    padding: 28px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.06);
}

.insight-box {
    background: linear-gradient(135deg,#7c3aed,#2563eb);
    border-radius: 18px;
    padding: 22px;
    color: white !important;
    font-size: 17px;
    font-weight: 600;
}

.insight-box * {
    color: white !important;
}

/* =====================================================
SCROLLBAR
===================================================== */

::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 999px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================

st.markdown("""
<div class="main-title">
🚀 Brand Health Dashboard
</div>

<div class="main-subtitle">
Interactive analytics platform for tracking brand performance
</div>
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

# =========================================================
# KPI MAP
# =========================================================

kpi_map = {
    "Awareness": ("Aided_Awareness", "yesno"),
    "Favorability": ("Brand_Favorability", "top2"),
    "Consideration": ("Consideration", "top2"),
    "Effect": ("Consideration_Effect", "top2")
}

# =========================================================
# FILTERS
# =========================================================

@st.cache_data
def load_filters():

    df_temp = con.execute("""
        SELECT Month, ROW_NUMBER() OVER() AS rn
        FROM df
        WHERE Month IS NOT NULL
    """).df()

    months = (
        df_temp.drop_duplicates("Month")
        .sort_values("rn")["Month"]
        .tolist()
    )

    countries = con.execute("""
        SELECT DISTINCT Country_New
        FROM df
        WHERE Country_New IS NOT NULL
    """).df()["Country_New"].tolist()

    return months, countries

months, countries = load_filters()

# =========================================================
# BRAND MAP
# =========================================================

brand_rows = map_df[
    map_df["Variable"].astype(str).str.contains(
        "Aided_Awareness_",
        na=False
    )
]

brand_map = {
    str(r["Label"]).split(" - ")[-1].strip():
    int(re.findall(r"\d+", str(r["Variable"]))[0])
    for _, r in brand_rows.iterrows()
}

# =========================================================
# FUNCTIONS
# =========================================================

def get_brands_by_country(selected_countries):
    return brand_map


def build_where(months_sel, countries_sel, segment):

    filters = []

    if months_sel:
        filters.append(
            "Month IN (" +
            ",".join(f"'{m}'" for m in months_sel)
            + ")"
        )

    if countries_sel:
        filters.append(
            "Country_New IN (" +
            ",".join(f"'{c}'" for c in countries_sel)
            + ")"
        )

    if segment == "Male":
        filters.append("Sex = 1")

    elif segment == "Female":
        filters.append("Sex = 2")

    return "WHERE " + " AND ".join(filters) if filters else ""


# =========================================================
# METRIC FUNCTION
# =========================================================

def get_metric(
    col,
    metric_type="top2",
    where_clause="",
    weight_col="Global_weight_Stacked"
):

    try:

        if metric_type == "yesno":

            q = f"""
            SELECT
            SUM(
                CASE WHEN LOWER(TRIM({col}))='yes'
                THEN {weight_col}
                ELSE 0
                END
            ) * 100.0 / SUM({weight_col})
            FROM df
            {where_clause}
            """

        else:

            q = f"""
            SELECT
            SUM(
                CASE WHEN TRY_CAST(
                    REGEXP_EXTRACT(TRIM({col}), '\\d+')
                    AS INTEGER
                ) IN (4,5)
                THEN {weight_col}
                ELSE 0
                END
            ) * 100.0 /

            SUM(
                CASE WHEN TRY_CAST(
                    REGEXP_EXTRACT(TRIM({col}), '\\d+')
                    AS INTEGER
                ) BETWEEN 1 AND 5
                THEN {weight_col}
                ELSE 0
                END
            )

            FROM df
            {where_clause}
            """

        return round(
            con.execute(q).fetchone()[0] or 0,
            1
        )

    except:
        return 0

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 📊 Navigation")

    selected_page = option_menu(
        menu_title=None,
        options=["Dashboard", "Graphs", "Chatbot"],
        icons=["speedometer2", "graph-up-arrow", "robot"],
        default_index=0,
    )

# =========================================================
# DASHBOARD
# =========================================================

if selected_page == "Dashboard":

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        selected_countries = st.multiselect(
            "🌍 Country",
            countries
        )

    with f2:
        selected_months = st.multiselect(
            "📅 Month",
            months
        )

    with f3:
        segment = st.selectbox(
            "👤 Segment",
            ["Total", "Male", "Female"]
        )

    with f4:

        filtered_brand_map = get_brands_by_country(
            selected_countries
        )

        selected_brand = st.selectbox(
            "🏢 Brand",
            list(filtered_brand_map.keys())
        )

    code = filtered_brand_map[selected_brand]

    where_clause = build_where(
        selected_months,
        selected_countries,
        segment
    )

    weight_col = (
        "Weight_Post"
        if len(selected_countries) == 1
        else "Global_weight_Stacked"
    )

    awareness = get_metric(
        f'Aided_Awareness_{code}_slice',
        'yesno',
        where_clause,
        weight_col
    )

    favorability = get_metric(
        f'Brand_Favorability_{code}_slice',
        'top2',
        where_clause,
        weight_col
    )

    consideration = get_metric(
        f'Consideration_{code}_slice',
        'top2',
        where_clause,
        weight_col
    )

    effect = get_metric(
        f'Consideration_Effect_{code}_slice',
        'top2',
        where_clause,
        weight_col
    )

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    cards = [
        (c1, "Awareness", awareness),
        (c2, "Favorability", favorability),
        (c3, "Consideration", consideration),
        (c4, "Effect", effect)
    ]

    for col, title, value in cards:

        with col:

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

                    <div class="metric-fill"
                    style="width:{value}%"></div>

                </div>

            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # =====================================================
    # ATTRIBUTES
    # =====================================================

    st.markdown("""
    <div class='graph-card'>
    """, unsafe_allow_html=True)

    st.subheader("📊 Brand Attributes")

    attr_data = [

        {
            "Attribute": attr_map[i],

            "Value": get_metric(
                f"Attributes_New_DP_{code}_Q12a_{i}_slice",
                "top2",
                where_clause,
                weight_col
            )
        }

        for i in range(1, 18)
    ]

    attr_df = pd.DataFrame(attr_data)

    attr_df = attr_df.sort_values(
        "Value",
        ascending=True
    )

    fig_attr = px.bar(
        attr_df,
        x="Value",
        y="Attribute",
        orientation='h',
        text="Value",
        height=700,
        color="Value",
        color_continuous_scale="Purples"
    )

    fig_attr.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='white',
        font_color='#111827',
        xaxis_title='',
        yaxis_title=''
    )

    st.plotly_chart(
        fig_attr,
        use_container_width=True
    )

    st.markdown("</div>", unsafe_allow_html=True)
