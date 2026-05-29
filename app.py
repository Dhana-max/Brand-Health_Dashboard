# Enhanced Streamlit Brand Health Dashboard UI
import streamlit as st
import duckdb
import pandas as pd
import re
import plotly.express as px
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
# PREMIUM DARK UI
# --------------------------------------------------
st.markdown("""
<style>

/* -----------------------------
MAIN APP
----------------------------- */
.stApp {
    background: #0f172a;
    color: white;
}

/* -----------------------------
MAIN CONTAINER
----------------------------- */
.block-container {
    padding-top: 1.5rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* -----------------------------
SIDEBAR
----------------------------- */
section[data-testid="stSidebar"] {
    background: #111827;
    border-right: 1px solid #1e293b;
}

/* -----------------------------
HEADINGS
----------------------------- */
h1, h2, h3, h4, h5, h6,
label, p, span {
    color: #f8fafc !important;
}

/* -----------------------------
FILTER LABELS
----------------------------- */
.stMultiSelect label,
.stSelectbox label {
    font-size: 16px !important;
    font-weight: 600 !important;
    color: #e2e8f0 !important;
}

/* -----------------------------
MULTISELECT BOX
----------------------------- */
.stMultiSelect div[data-baseweb="select"] {
    background-color: #1e293b !important;
    border-radius: 12px !important;
    border: 1px solid #334155 !important;
    min-height: 55px;
}

/* -----------------------------
SELECTBOX
----------------------------- */
.stSelectbox div[data-baseweb="select"] {
    background-color: #1e293b !important;
    border-radius: 12px !important;
    border: 1px solid #334155 !important;
}

/* -----------------------------
REMOVE RED TAGS
----------------------------- */
span[data-baseweb="tag"] {
    background-color: #334155 !important;
    border-radius: 20px !important;
    padding: 4px 10px !important;
    border: 1px solid #475569 !important;
}

/* CHIP TEXT */
span[data-baseweb="tag"] span {
    color: white !important;
    font-weight: 500;
}

/* CHIP CLOSE BUTTON */
span[data-baseweb="tag"] svg {
    color: #cbd5e1 !important;
}

/* -----------------------------
METRIC CARDS
----------------------------- */
.metric-card {
    background: linear-gradient(
        145deg,
        #111827,
        #1e293b
    );

    padding: 24px;
    border-radius: 20px;

    border: 1px solid rgba(255,255,255,0.05);

    box-shadow:
        0 4px 10px rgba(0,0,0,0.2);

    transition: all 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-5px);
    box-shadow:
        0 10px 20px rgba(0,0,0,0.35);
}

/* KPI TITLE */
.metric-title {
    color: #94a3b8;
    font-size: 15px;
    font-weight: 600;
}

/* KPI VALUE */
.metric-value {
    color: white;
    font-size: 40px;
    font-weight: bold;
    margin-top: 10px;
}

/* -----------------------------
OPTION MENU
----------------------------- */
.nav-link {
    font-size: 16px !important;
    border-radius: 10px !important;
    margin-bottom: 8px !important;
}

.nav-link-selected {
    background-color: #2563eb !important;
}

/* -----------------------------
RADIO BUTTONS
----------------------------- */
.stRadio label {
    color: white !important;
}

/* -----------------------------
SCROLLBAR
----------------------------- */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-thumb {
    background: #334155;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# TITLE
# --------------------------------------------------
st.markdown("""
<h1 style='font-size:42px;'>📊 Brand Health Dashboard</h1>
<p style='color:#94a3b8;'>
Modern analytics dashboard for brand performance tracking
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
    2: "Helps me find the right job for me",
    3: "Helps me navigate my professional life",
    4: "Is a place I feel I belong",
    5: "Cares about issues that matter to me",
    6: "Is a brand I love",
    7: "Is a brand I trust",
    8: "Makes me feel like I'm part of a community",
    9: "Helps me stay informed on professional topics that matter to me",
    10: "Is a place where discussions related to my work life happen",
    11: "Is useful for me to visit every day",
    12: "Is a platform where I create/share content",
    13: "I use this more frequently to create/share content than before",
    14: "Is a platform I would use as part of my job",
    15: "Helps me reach my goals",
    16: "Is a locally relevant professional network",
    17: "Helps me move forward in my career/business"
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

    st.markdown("## 📊 Navigation")

    selected_page = option_menu(
        menu_title=None,
        options=["Dashboard", "Graphs", "Chatbot"],
        icons=["speedometer2", "graph-up", "robot"],
        default_index=0,
    )

# --------------------------------------------------
# DASHBOARD PAGE
# --------------------------------------------------
if selected_page == "Dashboard":

    # --------------------------------------------------
    # FILTERS
    # --------------------------------------------------
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

    # --------------------------------------------------
    # FILTER LOGIC
    # --------------------------------------------------
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

    # --------------------------------------------------
    # KPI VALUES
    # --------------------------------------------------
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

    # --------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------
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

                <div class="metric-value">
                    {value}%
                </div>
            </div>
            """, unsafe_allow_html=True)

    # --------------------------------------------------
    # ATTRIBUTE CHART
    # --------------------------------------------------
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
        template="plotly_dark",
        height=700,
        color="Value",
        color_continuous_scale="Blues"
    )

    fig_attr.update_layout(
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        font_color="white"
    )

    st.plotly_chart(
        fig_attr,
        use_container_width=True
    )

# --------------------------------------------------
# GRAPHS PAGE
# --------------------------------------------------
elif selected_page == "Graphs":

    st.subheader("📈 Brand Trends")

    g1, g2, g3 = st.columns(3)

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

    brand_map_local = get_brands_by_country(g_country)

    selected_brands = st.multiselect(
        "Brands",
        list(brand_map_local.keys()),
        default=list(brand_map_local.keys())[:3]
    )

    view_type = st.radio(
        "View Type",
        ["Trended View", "Brand Comparison"],
        horizontal=True
    )

    graph_where = build_where(
        g_months,
        g_country,
        g_segment
    )

    queries = []

    for brand in selected_brands:

        code = brand_map_local[brand]

        col = f"Aided_Awareness_{code}_slice"

        queries.append(f"""
        SELECT
        Month,
        '{brand}' AS Brand,

        SUM(
            CASE WHEN LOWER(TRIM({col}))='yes'
            THEN Global_weight_Stacked
            ELSE 0
            END
        )*100.0 / SUM(Global_weight_Stacked) AS Value

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

        if view_type == "Trended View":

            fig = px.line(
                df_chart,
                x="Month_order",
                y="Value",
                color="Brand",
                markers=True,
                template="plotly_dark"
            )

        else:

            fig = px.line(
                df_chart,
                x="Brand",
                y="Value",
                color="Month",
                markers=True,
                template="plotly_dark"
            )

        fig.update_layout(
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a",
            font_color="white",
            height=600
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
    <div style='
        background:#111827;
        padding:20px;
        border-radius:15px;
        border:1px solid rgba(255,255,255,0.05);
    '>

    Ask questions about:

    <ul>
        <li>Awareness trends</li>
        <li>Top performing brands</li>
        <li>Country comparison</li>
        <li>Brand attributes</li>
    </ul>

    </div>
    """, unsafe_allow_html=True)

    user_query = st.text_input(
        "Ask about KPIs"
    )

    if user_query:

        st.success(
            "Insight response here (future AI integration)"
        )
