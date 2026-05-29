import streamlit as st
import duckdb
import pandas as pd
import re
import altair as alt
from difflib import get_close_matches

st.set_page_config(layout="wide")

# ==========================================
# 🎨 CLEAN UI LIGHT THEME STYLING (TD CONNECT STYLE)
# ==========================================
st.markdown("""
<style>
    /* Global Background and Typography */
    .stApp {
        background-color: #f4f6f9 !important;
        color: #333333 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Main Dashboard Title */
    h1 {
        color: #1a202c !important;
        font-weight: 700 !important;
        font-size: 2.2rem !important;
        margin-bottom: 1.5rem !important;
    }
    
    h2, h3, h4, h5, h6 {
        color: #2d3748 !important;
        font-weight: 600 !important;
    }

    /* Top Horizontal Navigation Tabs Customization */
    div[data-testid="stTabBar"] {
        background-color: #ffffff !important;
        padding: 0px 20px !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
        margin-bottom: 25px !important;
        border: 1px solid #e2e8f0 !important;
    }
    button[data-baseweb="tab"] {
        color: #718096 !important;
        font-weight: 600 !important;
        padding: 14px 20px !important;
        background-color: transparent !important;
        border: none !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #3182ce !important;
        border-bottom: 3px solid #3182ce !important;
    }

    /* Grid Container Cards */
    div[data-testid="column"] {
        background-color: #ffffff !important;
        padding: 24px !important;
        border-radius: 10px !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
    }

    /* Custom Sparkline KPI Layout Blocks */
    .kpi-container {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
        width: 100%;
    }
    .kpi-header {
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #718096 !important;
        font-weight: 600 !important;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #1a202c !important;
        margin-bottom: 12px;
        line-height: 1;
    }
    .sparkline-wrapper {
        width: 100%;
        height: 35px;
        margin-top: auto;
    }

    /* Filter Headers Label Text */
    .filter-label {
        color: #4a5568 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        margin-bottom: 6px !important;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    /* Form controls (Selectboxes, Multiselects) Restored Native Framework */
    .stSelectbox div, .stMultiSelect div {
        background-color: #ffffff !important;
        color: #2d3748 !important;
    }

    /* Native Multi-select tag styles to keep text from being cut off */
    div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
        background-color: #edf2f7 !important;
        border: 1px solid #cbd5e0 !important;
        border-radius: 4px !important;
        color: #2d3748 !important;
        padding: 2px 6px !important;
    }
    div[data-testid="stMultiSelect"] span[data-baseweb="tag"] button {
        color: #4a5568 !important;
    }

    /* Crisp Light-Theme Matrix Data Tables */
    .light-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        color: #2d3748;
        font-family: inherit;
        background-color: #ffffff;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
    }
    .light-table th {
        background-color: #f7fafc;
        color: #4a5568;
        text-align: left;
        padding: 14px 16px;
        font-weight: 600;
        border-bottom: 2px solid #e2e8f0;
        font-size: 0.9rem;
    }
    .light-table td {
        padding: 12px 16px;
        border-bottom: 1px solid #edf2f7;
        font-size: 0.95rem;
    }
    .light-table tr:last-child td {
        border-bottom: none;
    }
    .light-table tr:hover {
        background-color: #f8fafc;
    }
</style>
""", unsafe_allow_html=True)

st.title("Brand Health Dashboard")

PARQUET_URL = "https://github.com/Dhana-max/Brand-Health_Dashboard/releases/download/v1/data.parquet"
MAP_FILE = "Map.xlsx"

# -----------------------------
@st.cache_resource
def get_connection():
    con = duckdb.connect()
    con.execute(f"""
        CREATE VIEW df AS 
        SELECT * FROM read_parquet('{PARQUET_URL}')
    """)
    return con

con = get_connection()

# -----------------------------
@st.cache_data
def load_map():
    df = pd.read_excel(MAP_FILE, header=1)
    df.columns = df.columns.astype(str).str.strip()
    return df

map_df = load_map()

# -----------------------------
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

# -----------------------------
@st.cache_data
def load_filters():
    df_temp = con.execute("""
        SELECT Month, ROW_NUMBER() OVER() AS rn
        FROM df WHERE Month IS NOT NULL
    """).df()

    months = (
        df_temp.drop_duplicates("Month")
        .sort_values("rn")["Month"]
        .tolist()
    )

    countries = con.execute("""
        SELECT DISTINCT Country_New FROM df WHERE Country_New IS NOT NULL
    """).df()["Country_New"].tolist()

    return months, countries

months, countries = load_filters()

# -----------------------------
brand_rows = map_df[
    map_df["Variable"].astype(str).str.contains("Aided_Awareness_", na=False)
]

brand_map = {
    str(r["Label"]).split(" - ")[-1].strip():
    int(re.findall(r"\d+", str(r["Variable"]))[0])
    for _, r in brand_rows.iterrows()
}

# -----------------------------
def get_brands_by_country(selected_countries):
    return brand_map

# -----------------------------
def build_where(months_sel, countries_sel, segment):
    filters = []
    if months_sel:
        filters.append("Month IN (" + ",".join(f"'{m}'" for m in months_sel) + ")")
    if countries_sel:
        filters.append("Country_New IN (" + ",".join(f"'{c}'" for c in countries_sel) + ")")
    if segment == "Male":
        filters.append("Sex = 1")
    elif segment == "Female":
        filters.append("Sex = 2")

    return "WHERE " + " AND ".join(filters) if filters else ""

# -----------------------------
def get_metric(col, metric_type="top2", where_clause="", weight_col="Global_weight_Stacked"):
    try:
        if metric_type == "yesno":
            q = f"""
            SELECT SUM(CASE WHEN LOWER(TRIM({col}))='yes'
            THEN {weight_col} ELSE 0 END)*100.0/SUM({weight_col})
            FROM df {where_clause}
            """
        else:
            q = f"""
            SELECT SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5)
            THEN {weight_col} ELSE 0 END)*100.0 /
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) BETWEEN 1 AND 5
            THEN {weight_col} ELSE 0 END)
            FROM df {where_clause}
            """
        return round(con.execute(q).fetchone()[0] or 0, 1)
    except:
        return 0

# -----------------------------
# 📈 Helper function to generate inline trend sparklines for each KPI card
# -----------------------------
def get_sparkline_data(col, metric_type, where_clause, weight_col):
    try:
        # Reconstruct timeline trend data bypassing main selections to show the line curve
        # But respect other filters like Segment/Country if populated
        base_where = where_clause
        q = f"""
        SELECT Month, 
               SUM(CASE WHEN LOWER(TRIM({col}))='yes' THEN {weight_col} ELSE 0 END)*100.0/SUM({weight_col}) as val
        FROM df {base_where} GROUP BY Month
        """ if metric_type == "yesno" else f"""
        SELECT Month,
               SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5) THEN {weight_col} ELSE 0 END)*100.0 /
               SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) BETWEEN 1 AND 5 THEN {weight_col} ELSE 0 END) as val
        FROM df {base_where} GROUP BY Month
        """
        spark_df = con.execute(q).df()
        if not spark_df.empty:
            spark_df["Month_order"] = pd.Categorical(spark_df["Month"], categories=months, ordered=True)
            spark_df = spark_df.sort_values("Month_order")
            return spark_df[["Month", "val"]]
    except:
        pass
    return pd.DataFrame({"Month": months, "val": [0]*len(months)})

def create_sparkline_chart(df, color_line):
    chart = alt.Chart(df).mark_line(interpolate='monotone', strokeWidth=2.5, color=color_line).encode(
        x=alt.X('Month:O', title=None, axis=None),
        y=alt.Y('val:Q', title=None, axis=None, scale=alt.Scale(zero=False))
    ).properties(width=220, height=35)
    return chart.configure(background='transparent').configure_view(strokeOpacity=0)

# -----------------------------
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 Graphs", "🤖 Chatbot"])

# -----------------------------
with tab1:
    # Filter Bar Container Grid
    f1, f2, f3, f4 = st.columns([3, 3, 2, 3])

    with f1:
        st.markdown('<div class="filter-label">🌍 Country</div>', unsafe_allow_html=True)
        selected_countries = st.multiselect("", countries, label_visibility="collapsed")

    with f2:
        st.markdown('<div class="filter-label">📅 Month</div>', unsafe_allow_html=True)
        selected_months = st.multiselect("", months, label_visibility="collapsed")

    with f3:
        st.markdown('<div class="filter-label">👤 Segment</div>', unsafe_allow_html=True)
        segment = st.selectbox("", ["Total", "Male", "Female"], label_visibility="collapsed")

    with f4:
        st.markdown('<div class="filter-label">🏢 Brand</div>', unsafe_allow_html=True)
        filtered_brand_map = get_brands_by_country(selected_countries)
        selected_brand = st.selectbox("", list(filtered_brand_map.keys()), label_visibility="collapsed")

    code = filtered_brand_map[selected_brand]
    where_clause = build_where(selected_months, selected_countries, segment)
    weight_col = "Weight_Post" if len(selected_countries) == 1 else "Global_weight_Stacked"

    st.markdown("<br>", unsafe_allow_html=True)
    
    # KPIs Cards Layout Row with Embedded Sparkline Line Graphs
    col1, col2, col3, col4 = st.columns(4)
    
    # KPI 1: Total Awareness
    with col1:
        val1 = f"{get_metric(f'Aided_Awareness_{code}_slice', 'yesno', where_clause, weight_col)}%"
        st.markdown(f'<div class="kpi-container"><div class="kpi-header">Total Awareness</div><div class="kpi-value">{val1}</div></div>', unsafe_allow_html=True)
        df_sp1 = get_sparkline_data(f'Aided_Awareness_{code}_slice', 'yesno', where_clause, weight_col)
        st.altair_chart(create_sparkline_chart(df_sp1, '#48bb78'), use_container_width=True)

    # KPI 2: Brand Favorability
    with col2:
        val2 = f"{get_metric(f'Brand_Favorability_{code}_slice', 'top2', where_clause, weight_col)}%"
        st.markdown(f'<div class="kpi-container"><div class="kpi-header">Brand Favorability</div><div class="kpi-value">{val2}</div></div>', unsafe_allow_html=True)
        df_sp2 = get_sparkline_data(f'Brand_Favorability_{code}_slice', 'top2', where_clause, weight_col)
        st.altair_chart(create_sparkline_chart(df_sp2, '#3182ce'), use_container_width=True)

    # KPI 3: Consideration Rate
    with col3:
        val3 = f"{get_metric(f'Consideration_{code}_slice', 'top2', where_clause, weight_col)}%"
        st.markdown(f'<div class="kpi-container"><div class="kpi-header">Consideration Rate</div><div class="kpi-value">{val3}</div></div>', unsafe_allow_html=True)
        df_sp3 = get_sparkline_data(f'Consideration_{code}_slice', 'top2', where_clause, weight_col)
        st.altair_chart(create_sparkline_chart(df_sp3, '#805ad5'), use_container_width=True)

    # KPI 4: Conversion Effect
    with col4:
        val4 = f"{get_metric(f'Consideration_Effect_{code}_slice', 'top2', where_clause, weight_col)}%"
        st.markdown(f'<div class="kpi-container"><div class="kpi-header">Conversion Effect</div><div class="kpi-value">{val4}</div></div>', unsafe_allow_html=True)
        df_sp4 = get_sparkline_data(f'Consideration_Effect_{code}_slice', 'top2', where_clause, weight_col)
        st.altair_chart(create_sparkline_chart(df_sp4, '#e53e3e'), use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Brand Attribute Matrix Breakdown")

    attr_data = [
        {"Attribute": attr_map[i], "Value (%)": f"{get_metric(f'Attributes_New_DP_{code}_Q12a_{i}_slice', 'top2', where_clause, weight_col)}%"}
        for i in range(1, 18)
    ]
    
    df_matrix = pd.DataFrame(attr_data)
    
    html_table = "<table class='light-table'><thead><tr><th>Attribute</th><th>Value (%)</th></tr></thead><tbody>"
    for _, row in df_matrix.iterrows():
        html_table += f"<tr><td>{row['Attribute']}</td><td><strong>{row['Value (%)']}</strong></td></tr>"
    html_table += "</tbody></table>"
    
    st.markdown(html_table, unsafe_allow_html=True)

# -----------------------------
with tab2:
    colg1, colg2, colg3, colg4 = st.columns(4)

    with colg1:
        st.markdown('<div class="filter-label">🌍 Country</div>', unsafe_allow_html=True)
        g_country = st.multiselect("Country", countries, key="g_country", label_visibility="collapsed")
    with colg2:
        st.markdown('<div class="filter-label">📅 Month</div>', unsafe_allow_html=True)
        g_months = st.multiselect("Month", months, key="g_months", label_visibility="collapsed")
    with colg3:
        st.markdown('<div class="filter-label">👤 Segment</div>', unsafe_allow_html=True)
        g_segment = st.selectbox("Segment", ["Total", "Male", "Female"], key="g_segment", label_visibility="collapsed")
    with colg4:
        st.markdown('<div class="filter-label">🏢 Brands</div>', unsafe_allow_html=True)
        brand_map_local = get_brands_by_country(g_country)
        selected_brands = st.multiselect("Brands", list(brand_map_local.keys()),
                                            default=list(brand_map_local.keys())[:3], key="g_brands", label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    view_type = st.radio("View Type", ["Trended View", "Brand Comparison"], horizontal=True)
    graph_where = build_where(g_months, g_country, g_segment)

    if selected_brands:
        queries = []
        for brand in selected_brands:
            code = brand_map_local[brand]
            col = f"Aided_Awareness_{code}_slice"

            queries.append(f"""
            SELECT Month, '{brand}' AS Brand,
            SUM(CASE WHEN LOWER(TRIM({col}))='yes'
            THEN Global_weight_Stacked ELSE 0 END)*100.0 /
            SUM(Global_weight_Stacked) AS Value
            FROM df {graph_where}
            GROUP BY Month
            """)

        df_chart = con.execute(" UNION ALL ".join(queries)).df()

        if not df_chart.empty and "Month" in df_chart.columns:
            df_chart["Month_order"] = pd.Categorical(df_chart["Month"], categories=months, ordered=True)

            # 📊 Light Theme Clean Color Palette 
            chart_color_palette = ["#3182ce", "#e53e3e", "#319795", "#d69e2e", "#805ad5"]

            if view_type == "Trended View":
                chart = alt.Chart(df_chart).mark_line(point=True, size=3).encode(
                    x=alt.X("Month_order:O", title="Timeline Phase", axis=alt.Axis(labelColor="#4a5568", titleColor="#2d3748")),
                    y=alt.Y("Value:Q", title="Percentage Share (%)", axis=alt.Axis(labelColor="#4a5568", titleColor="#2d3748"), scale=alt.Scale(zero=False)),
                    color=alt.Color("Brand:N", scale=alt.Scale(range=chart_color_palette))
                ).properties(height=400)
            else:
                chart = alt.Chart(df_chart).mark_line(point=True, size=3).encode(
                    x=alt.X("Brand:N", title="Competitor Space", axis=alt.Axis(labelColor="#4a5568", titleColor="#2d3748")),
                    y=alt.Y("Value:Q", title="Percentage Share (%)", axis=alt.Axis(labelColor="#4a5568", titleColor="#2d3748"), scale=alt.Scale(zero=False)),
                    color=alt.Color("Month:O", scale=alt.Scale(range=chart_color_palette))
                ).properties(height=400)

            chart = chart.configure(background='transparent').configure_view(strokeOpacity=0)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.warning("⚠️ No data available matching the selected filter variations.")
    else:
        st.info("Please pick at least one brand configuration view.")

# -----------------------------
with tab3:
    st.subheader("🤖 Chatbot (Insights Only)")
    user_query = st.text_input("Ask about KPIs")

    if user_query:
        st.markdown("✅ Insight response here (no chart)")
