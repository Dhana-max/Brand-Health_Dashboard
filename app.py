# Updated Streamlit Brand Health Dashboard
import streamlit as st
import duckdb
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Brand Health Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# MODERN GLASSMORPHIC UI
# --------------------------------------------------
st.markdown("""
<style>

/* ---------------- MAIN ---------------- */
.stApp {
    background: linear-gradient(135deg, #06142e 0%, #0b1f44 100%);
    color: white;
}

.block-container {
    padding-top: 1rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* ---------------- SIDEBAR ---------------- */
section[data-testid="stSidebar"] {
    background: rgba(10,20,45,0.95);
    border-right: 1px solid rgba(255,255,255,0.08);
}

/* ---------------- TEXT ---------------- */
h1,h2,h3,h4,h5,h6,p,label,span,div {
    color: #f8fafc !important;
}

/* ---------------- FILTERS ---------------- */
.stMultiSelect div[data-baseweb="select"],
.stSelectbox div[data-baseweb="select"] {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 16px !important;
    min-height: 55px;
    backdrop-filter: blur(10px);
}

.stMultiSelect label,
.stSelectbox label {
    font-weight: 600 !important;
    font-size: 15px !important;
}

/* ---------------- MULTISELECT TAGS ---------------- */
span[data-baseweb="tag"] {
    background: transparent !important;
    border: none !important;
    padding: 0px !important;
    margin-right: 6px !important;
}

span[data-baseweb="tag"] span {
    color: #cbd5e1 !important;
    font-weight: 600;
    font-size: 14px !important;
}

/* REMOVE TAG BACKGROUND CLOSE ICON */
span[data-baseweb="tag"] svg {
    display: none !important;
}

/* INPUT TEXT */
input, textarea {
    color: #0f172a !important;
    font-weight: 600 !important;
}

/* PLACEHOLDER */
input::placeholder {
    color: #64748b !important;
}

/* SELECTED VALUE */
.stSelectbox div[data-baseweb="select"] * {
    color: #0f172a !important;
    font-weight: 600 !important;
}

/* MULTISELECT VALUE */
.stMultiSelect div[data-baseweb="select"] * {
    color: #0f172a !important;
    font-weight: 600 !important;
}

/* ---------------- KPI CARDS ---------------- */
.metric-card {
    background: #ffffff;
    border-radius: 28px;
    padding: 28px;
    border: 1px solid #dbe4f0;
    box-shadow: 0 8px 24px rgba(15,23,42,0.12);
    transition: 0.3s ease;
    position: relative;
    overflow: hidden;
    text-align: left;
    min-height: 240px;
}

.metric-card:hover {
    transform: translateY(-5px);
}

.metric-title {
    color: #334155;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.5px;
    margin-bottom: 20px;
    text-transform: uppercase;
}

.metric-value {
    font-size: 44px;
    font-weight: 800;
    color: #0f172a;
    margin-top: 30px;
}

.metric-progress {
    width: 100%;
    height: 14px;
    border-radius: 20px;
    background: #e2e8f0;
    overflow: hidden;
    margin-top: 20px;
}

.metric-fill {
    height: 100%;
    border-radius: 20px;
    background: linear-gradient(90deg,#22c55e,#3b82f6);
}

/* ---------------- NAVIGATION ---------------- */
.nav-link {
    border-radius: 12px !important;
    margin-bottom: 8px !important;
    font-size: 16px !important;
}

.nav-link-selected {
    background: linear-gradient(90deg,#2563eb,#7c3aed) !important;
}

/* ---------------- CHAT BOX ---------------- */
.chat-card {
    background: rgba(255,255,255,0.06);
    padding: 25px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.1);
}

.insight-box {
    background: linear-gradient(90deg,#0ea5e9,#2563eb);
    padding: 20px;
    border-radius: 16px;
    color: white !important;
    font-size: 18px;
    font-weight: 600;
}

/* ---------------- RADIO ---------------- */
.stRadio label {
    color: white !important;
    font-weight: 600;
}

/* ---------------- SCROLL ---------------- */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-thumb {
    background: #3b82f6;
    border-radius: 20px;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# TITLE
# --------------------------------------------------
st.markdown("""
<h1 style='font-size:48px;font-weight:800;'>🚀 Brand Health Dashboard</h1>
<p style='font-size:18px;color:#cbd5e1;'>
Interactive analytics platform for tracking brand performance
</p>
""", unsafe_allow_html=True)

# --------------------------------------------------
# FILES
# --------------------------------------------------
PARQUET_URL = "https://github.com/Dhana-max/Brand-Health_Dashboard/releases/download/v1/data.parquet"
MAP_FILE = "Map.xlsx"

# --------------------------------------------------
# CONNECTION
# --------------------------------------------------
@st.cache_resource
def get_connection():
    con = duckdb.connect()

    con.execute(f"""
        CREATE VIEW df AS
        SELECT * FROM read_parquet('{PARQUET_URL}')
    """)

    return con

con = get_connection()

# --------------------------------------------------
# LOAD MAP
# --------------------------------------------------
@st.cache_data
def load_map():
    df = pd.read_excel(MAP_FILE, header=1)
    df.columns = df.columns.astype(str).str.strip()
    return df

map_df = load_map()

# --------------------------------------------------
# ATTRIBUTE MAP
# --------------------------------------------------
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

# --------------------------------------------------
# KPI MAP
# --------------------------------------------------
kpi_map = {
    "Awareness": ("Aided_Awareness", "yesno"),
    "Favorability": ("Brand_Favorability", "top2"),
    "Consideration": ("Consideration", "top2"),
    "Effect": ("Consideration_Effect", "top2")
}

# --------------------------------------------------
# LOAD FILTERS
# --------------------------------------------------
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

# --------------------------------------------------
# BRAND MAP
# --------------------------------------------------
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

# --------------------------------------------------
# FUNCTIONS
# --------------------------------------------------
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

# --------------------------------------------------
# METRIC FUNCTION
# --------------------------------------------------
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

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:

    st.markdown("## 📌 Navigation")

    selected_page = option_menu(
        menu_title=None,
        options=["Dashboard", "Graphs", "Chatbot"],
        icons=["speedometer2", "graph-up-arrow", "robot"],
        default_index=0,
    )

# --------------------------------------------------
# DASHBOARD PAGE
# --------------------------------------------------
if selected_page == "Dashboard":

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        selected_countries = st.multiselect(
            "🌍 Country",
            countries,
            placeholder="Select countries"
        )

        if selected_countries:
            st.markdown(f"<p style='color:#cbd5e1;font-size:15px;font-weight:600;'>Selected: {', '.join(selected_countries)}</p>", unsafe_allow_html=True)

    with f2:
        selected_months = st.multiselect(
            "📅 Month",
            months,
            placeholder="Select months"
        )

        if selected_months:
            st.markdown(f"<p style='color:#cbd5e1;font-size:15px;font-weight:600;'>Selected: {', '.join(selected_months)}</p>", unsafe_allow_html=True)

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

    impact = get_metric(
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
        (c4, "Effect", impact)
    ]

    for col, title, value in cards:

        with col:

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">
                    {title}
                </div>

                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="font-size:14px;color:#64748b;font-weight:600;">
                        KPI SCORE
                    </div>

                    <div style="
                        width:70px;
                        height:70px;
                        border-radius:50%;
                        background:#dcfce7;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        color:#166534;
                        font-weight:800;
                        font-size:24px;
                        box-shadow:0 0 18px rgba(34,197,94,0.35);
                    ">
                        {value}
                    </div>
                </div>

                <div class="metric-progress">
                    <div class="metric-fill" style="width:{value}%;"></div>
                </div>

                <div class="metric-value">
                    {value}%
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    st.subheader("📌 Brand Attributes")

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
        color_continuous_scale="Bluered"
    )

    fig_attr.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='white'
    )

    st.plotly_chart(
        fig_attr,
        use_container_width=True
    )

# --------------------------------------------------
# GRAPHS PAGE
# --------------------------------------------------
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

        fig = go.Figure()

        if graph_type == "Trend Comparison":

            for brand in selected_brands:

                temp_df = df_chart[df_chart["Brand"] == brand]

                fig.add_trace(go.Scatter(
                    x=temp_df["Month_order"],
                    y=temp_df["Value"],
                    mode='lines+markers',
                    name=brand,
                    line=dict(shape='spline', width=4),
                    marker=dict(size=8)
                ))

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
                color_continuous_scale='Turbo'
            )

        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(255,255,255,0.03)',
            font_color='white',
            height=650,
            xaxis_title='',
            yaxis_title=selected_kpi,
            legend_title='Brand',
            hovermode='x unified'
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# --------------------------------------------------
# CHATBOT PAGE
# --------------------------------------------------
elif selected_page == "Chatbot":

    st.subheader("🤖 AI Insights Assistant")

    st.markdown("""
    <div class='chat-card'>

    <h3>Ask questions about:</h3>

    <ul>
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
        Based on your query:

        👉 {user_query}

        The dashboard AI assistant will provide KPI insights,
        trend analysis, and market comparisons here.
        """

        st.markdown(
            f"""
            <div class='insight-box'>
            {response}
            </div>
            """,
            unsafe_allow_html=True
        )
