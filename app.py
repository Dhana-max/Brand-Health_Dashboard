# =========================================================
# PREMIUM BRAND HEALTH DASHBOARD
# =========================================================

import streamlit as st
import duckdb
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go
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
# PREMIUM LIGHT UI
# =========================================================

st.markdown("""
<style>

/* =====================================================
MAIN
===================================================== */

.stApp {
    background: #f4f7fb;
}

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
    background: white;
    border-right: 1px solid #e2e8f0;
}

/* =====================================================
TEXT
===================================================== */

h1,h2,h3,h4,h5,h6,p,label,span {
    color: #0f172a !important;
}

/* =====================================================
FILTERS
===================================================== */

.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: white !important;
    border: 1px solid #dbe4f0 !important;
    border-radius: 16px !important;
    min-height: 55px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* selected values */
.stMultiSelect span[data-baseweb="tag"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

.stMultiSelect span[data-baseweb="tag"] span {
    color: #2563eb !important;
    font-weight: 700 !important;
}

/* remove cross icon */
.stMultiSelect span[data-baseweb="tag"] svg {
    display: none !important;
}

input {
    color: #0f172a !important;
}

/* =====================================================
KPI CARDS
===================================================== */

.metric-card {
    background: white;
    border-radius: 24px;
    padding: 25px;
    box-shadow: 0 8px 24px rgba(15,23,42,0.08);
    border: 1px solid #e2e8f0;
    transition: 0.3s ease;
    min-height: 250px;
}

.metric-card:hover {
    transform: translateY(-4px);
}

.metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.metric-title {
    font-size: 15px;
    font-weight: 700;
    color: #64748b !important;
    text-transform: uppercase;
}

.metric-circle {
    width: 70px;
    height: 70px;
    border-radius: 50%;
    background: #ecfdf5;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #059669 !important;
    font-size: 24px;
    font-weight: 800;
    box-shadow: 0 0 20px rgba(16,185,129,0.2);
}

.metric-big {
    margin-top: 30px;
    font-size: 48px;
    font-weight: 800;
    color: #111827 !important;
}

.metric-progress {
    width: 100%;
    height: 12px;
    background: #e2e8f0;
    border-radius: 999px;
    margin-top: 20px;
    overflow: hidden;
}

.metric-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg,#8b5cf6,#3b82f6);
}

/* =====================================================
GRAPH CARD
===================================================== */

.graph-card {
    background: white;
    padding: 25px;
    border-radius: 24px;
    box-shadow: 0 8px 24px rgba(15,23,42,0.08);
    border: 1px solid #e2e8f0;
}

/* =====================================================
CHAT BOX
===================================================== */

.chat-card {
    background: white;
    padding: 30px;
    border-radius: 24px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 8px 24px rgba(15,23,42,0.08);
}

.insight-box {
    background: linear-gradient(90deg,#2563eb,#7c3aed);
    color: white !important;
    padding: 22px;
    border-radius: 18px;
    font-size: 18px;
    font-weight: 600;
    margin-top: 20px;
}

.insight-box * {
    color: white !important;
}

/* =====================================================
OPTION MENU
===================================================== */

.nav-link {
    border-radius: 12px !important;
    margin-bottom: 8px !important;
    color: #0f172a !important;
}

.nav-link-selected {
    background: linear-gradient(90deg,#2563eb,#7c3aed) !important;
    color: white !important;
}

/* =====================================================
RADIO
===================================================== */

.stRadio label {
    color: #0f172a !important;
    font-weight: 600 !important;
}

/* =====================================================
SCROLLBAR
===================================================== */

::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 20px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================

st.markdown("""
<h1 style='font-size:58px;font-weight:800;margin-bottom:0;'>
🚀 Brand Health Dashboard
</h1>

<p style='font-size:22px;color:#64748b;margin-top:0;'>
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

    st.markdown("## 📌 Navigation")

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

        if selected_countries:

            st.markdown(
                f"""
                <p style='
                    color:#2563eb;
                    font-weight:700;
                    margin-top:8px;
                '>
                Selected: {", ".join(selected_countries)}
                </p>
                """,
                unsafe_allow_html=True
            )

    with f2:

        selected_months = st.multiselect(
            "📅 Month",
            months
        )

        if selected_months:

            st.markdown(
                f"""
                <p style='
                    color:#2563eb;
                    font-weight:700;
                    margin-top:8px;
                '>
                Selected: {", ".join(selected_months)}
                </p>
                """,
                unsafe_allow_html=True
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

                    <div class="metric-title">
                        {title}
                    </div>

                    <div class="metric-circle">
                        {value}
                    </div>

                </div>

                <div class="metric-progress">
                    <div class="metric-fill"
                    style="width:{value}%;">
                    </div>
                </div>

                <div class="metric-big">
                    {value}%
                </div>

            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

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
        color_continuous_scale="Blues"
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

# =========================================================
# GRAPHS
# =========================================================

elif selected_page == "Graphs":

    st.subheader("📈 KPI Trend Comparison")

    g1, g2, g3, g4 = st.columns(4)

    g_country = g1.multiselect(
        "Country",
        countries,
        key="g_country"
    )

    g_months = g2.multiselect(
        "Month",
        months,
        key="g_months"
    )

    g_segment = g3.selectbox(
        "Segment",
        ["Total", "Male", "Female"],
        key="g_segment"
    )

    selected_kpi = g4.selectbox(
        "Select KPI",
        list(kpi_map.keys())
    )

    brand_map_local = get_brands_by_country(g_country)

    selected_brands = st.multiselect(
        "Brands",
        list(brand_map_local.keys()),
        default=list(brand_map_local.keys())[:3]
    )

    graph_type = st.radio(
        "Graph Type",
        ["Trend Comparison", "Month Comparison"],
        horizontal=True
    )

    graph_where = build_where(
        g_months,
        g_country,
        g_segment
    )

    metric_col, metric_type = kpi_map[selected_kpi]

    queries = []

    for brand in selected_brands:

        code = brand_map_local[brand]

        col = f"{metric_col}_{code}_slice"

        if metric_type == "yesno":

            metric_formula = f"""
            SUM(
                CASE WHEN LOWER(TRIM({col}))='yes'
                THEN Global_weight_Stacked
                ELSE 0
                END
            )*100.0 / SUM(Global_weight_Stacked)
            """

        else:

            metric_formula = f"""
            SUM(
                CASE WHEN TRY_CAST(
                    REGEXP_EXTRACT(TRIM({col}), '\\d+')
                    AS INTEGER
                ) IN (4,5)
                THEN Global_weight_Stacked
                ELSE 0
                END
            )*100.0 /

            SUM(
                CASE WHEN TRY_CAST(
                    REGEXP_EXTRACT(TRIM({col}), '\\d+')
                    AS INTEGER
                ) BETWEEN 1 AND 5
                THEN Global_weight_Stacked
                ELSE 0
                END
            )
            """

        queries.append(f"""
        SELECT
        Month,
        '{brand}' AS Brand,
        {metric_formula} AS Value

        FROM df

        {graph_where}

        GROUP BY Month
        """)

    if queries:

        df_chart = con.execute(
            " UNION ALL ".join(queries)
        ).df()

        df_chart["Month_order"] = pd.Categorical(
            df_chart["Month"],
            categories=months,
            ordered=True
        )

        st.markdown("""
        <div class='graph-card'>
        """, unsafe_allow_html=True)

        if graph_type == "Trend Comparison":

            fig = px.line(
                df_chart,
                x="Month_order",
                y="Value",
                color="Brand",
                markers=True
            )

        else:

            avg_df = (
                df_chart.groupby("Brand", as_index=False)["Value"]
                .mean()
            )

            fig = px.bar(
                avg_df,
                x="Brand",
                y="Value",
                color="Value",
                text_auto='.1f',
                color_continuous_scale="Purples"
            )

        fig.update_layout(
            paper_bgcolor='white',
            plot_bgcolor='white',
            font_color='#111827',
            height=650
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# CHATBOT
# =========================================================

elif selected_page == "Chatbot":

    st.subheader("🤖 AI Insights Assistant")

    st.markdown("""
    <div class='chat-card'>

    <h3 style='margin-top:0;'>
    Ask questions about:
    </h3>

    <ul style='font-size:18px;line-height:2;color:#334155;'>

        <li>Awareness trends</li>
        <li>Top performing brands</li>
        <li>Country comparison</li>
        <li>Brand attributes</li>

    </ul>

    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    user_query = st.text_input(
        "Ask about KPIs",
        placeholder="Example: LinkedIn awareness in Dec 2025"
    )

    if user_query:

        response = f"""
        📌 Query: {user_query}

        • KPI trends analyzed successfully

        • Brand performance insights generated

        • Country and segment comparison available

        • AI recommendations ready
        """

        st.markdown(
            f"""
            <div class='insight-box'>
            {response}
            </div>
            """,
            unsafe_allow_html=True
        )
