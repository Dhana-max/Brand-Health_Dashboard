import streamlit as st
import duckdb
import pandas as pd
import re
import altair as alt
from difflib import get_close_matches

st.set_page_config(layout="wide")

# ==========================================
# 🌌 PREMIUM CINEMATIC DARK UI OVERHAUL
# ==========================================
st.markdown("""
<style>
    /* Global Application Canvas */
    .stApp {
        background: linear-gradient(180deg, #0f0c1b 0%, #05030a 100%) !important;
        color: #e2e8f0 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Main Glowing Dashboard Header */
    h1 {
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 2.4rem !important;
        letter-spacing: -0.02em !important;
        margin-bottom: 1.5rem !important;
        text-shadow: 0 0 20px rgba(0, 242, 254, 0.15);
    }
    
    h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* Top Navigation Tab System Customization */
    div[data-testid="stTabBar"] {
        background-color: rgba(22, 19, 38, 0.8) !important;
        padding: 0px 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
        margin-bottom: 25px !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    button[data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-weight: 600 !important;
        padding: 14px 20px !important;
        background-color: transparent !important;
        border: none !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #00f2fe !important;
        border-bottom: 3px solid #00f2fe !important;
    }

    /* Structured Grid Container Cards (KPI Blocks) */
    div[data-testid="column"] {
        background: rgba(20, 17, 34, 0.75) !important;
        padding: 22px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5) !important;
        backdrop-filter: blur(10px);
    }

    /* Embedded Sparkline Metric Visual Structuring */
    .kpi-container {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        width: 100%;
    }
    .kpi-header {
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        color: #94a3b8 !important;
        font-weight: 600 !important;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 2.3rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        margin-bottom: 10px;
        line-height: 1;
    }

    /* Dropdown Component Labels */
    .filter-label {
        color: #cbd5e1 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        margin-bottom: 8px !important;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    /* Native Framework Control Adaptation */
    .stSelectbox div, .stMultiSelect div {
        background-color: #161326 !important;
        color: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
    }

    /* Multi-select filter tag customization preserving layout clarity */
    div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
        background-color: #2e2a47 !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 6px !important;
        color: #ffffff !important;
    }
    div[data-testid="stMultiSelect"] span[data-baseweb="tag"] button {
        color: #94a3b8 !important;
    }

    /* High-Contrast Cyberpunk Matrix Tables */
    .dark-matrix-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        color: #e2e8f0;
        font-family: inherit;
        background-color: rgba(16, 13, 28, 0.6);
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .dark-matrix-table th {
        background-color: #161326;
        color: #00f2fe;
        text-align: left;
        padding: 14px 18px;
        font-weight: 600;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .dark-matrix-table td {
        padding: 14px 18px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        font-size: 0.95rem;
    }
    .dark-matrix-table tr:last-child td {
        border-bottom: none;
    }
    .dark-matrix-table tr:hover {
        background-color: rgba(255, 255, 255, 0.03);
    }
</style>
""", unsafe_allow_html=True)

st.title("Brand Health Intelligence Platform")

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

def get_brands_by_country(selected_countries):
    return brand_map

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

def get_metric(col, metric_type="top2", where_clause="", weight_col="Global_weight_Stacked"):
    try:
        if metric_type == "yesno":
            q = f"""
            SELECT SUM(CASE WHEN LOWER(TRIM({col}))='yes' THEN {weight_col} ELSE 0 END)*100.0/SUM({weight_col})
            FROM df {where_clause}
            """
        else:
            q = f"""
            SELECT SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5) THEN {weight_col} ELSE 0 END)*100.0 /
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) BETWEEN 1 AND 5 THEN {weight_col} ELSE 0 END)
            FROM df {where_clause}
            """
        return round(con.execute(q).fetchone()[0] or 0, 1)
    except:
        return 0

def get_sparkline_data(col, metric_type, where_clause, weight_col):
    try:
        q = f"""
        SELECT Month, SUM(CASE WHEN LOWER(TRIM({col}))='yes' THEN {weight_col} ELSE 0 END)*100.0/SUM({weight_col}) as val
        FROM df {where_clause} GROUP BY Month
        """ if metric_type == "yesno" else f"""
        SELECT Month, SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5) THEN {weight_col} ELSE 0 END)*100.0 /
        SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) BETWEEN 1 AND 5 THEN {weight_col} ELSE 0 END) as val
        FROM df {where_clause} GROUP BY Month
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
tab1, tab2, tab3 = st.tabs(["📊 Executive View", "📈 Deep-Dive Graphs", "🤖 AI Analytics Chatbot"])

# -----------------------------
with tab1:
    f1, f2, f3, f4 = st.columns([3, 3, 2, 3])

    with f1:
        st.markdown('<div class="filter-label">🌍 Region / Country</div>', unsafe_allow_html=True)
        selected_countries = st.multiselect("", countries, label_visibility="collapsed")
    with f2:
        st.markdown('<div class="filter-label">📅 Historical Phase</div>', unsafe_allow_html=True)
        selected_months = st.multiselect("", months, label_visibility="collapsed")
    with f3:
        st.markdown('<div class="filter-label">👤 Demographic Segment</div>', unsafe_allow_html=True)
        segment = st.selectbox("", ["Total", "Male", "Female"], label_visibility="collapsed")
    with f4:
        st.markdown('<div class="filter-label">🏢 Target Enterprise Brand</div>', unsafe_allow_html=True)
        filtered_brand_map = get_brands_by_country(selected_countries)
        selected_brand = st.selectbox("", list(filtered_brand_map.keys()), label_visibility="collapsed")

    code = filtered_brand_map[selected_brand]
    where_clause = build_where(selected_months, selected_countries, segment)
    weight_col = "Weight_Post" if len(selected_countries) == 1 else "Global_weight_Stacked"

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 📈 KPI Cards Grid featuring Glowing Sparklines
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        val1 = f"{get_metric(f'Aided_Awareness_{code}_slice', 'yesno', where_clause, weight_col)}%"
        st.markdown(f'<div class="kpi-container"><div class="kpi-header">Total Awareness</div><div class="kpi-value" style="color: #00f2fe;">{val1}</div></div>', unsafe_allow_html=True)
        df_sp1 = get_sparkline_data(f'Aided_Awareness_{code}_slice', 'yesno', where_clause, weight_col)
        st.altair_chart(create_sparkline_chart(df_sp1, '#00f2fe'), use_container_width=True)

    with col2:
        val2 = f"{get_metric(f'Brand_Favorability_{code}_slice', 'top2', where_clause, weight_col)}%"
        st.markdown(f'<div class="kpi-container"><div class="kpi-header">Brand Favorability</div><div class="kpi-value" style="color: #38ef7d;">{val2}</div></div>', unsafe_allow_html=True)
        df_sp2 = get_sparkline_data(f'Brand_Favorability_{code}_slice', 'top2', where_clause, weight_col)
        st.altair_chart(create_sparkline_chart(df_sp2, '#38ef7d'), use_container_width=True)

    with col3:
        val3 = f"{get_metric(f'Consideration_{code}_slice', 'top2', where_clause, weight_col)}%"
        st.markdown(f'<div class="kpi-container"><div class="kpi-header">Consideration Rate</div><div class="kpi-value" style="color: #ff007f;">{val3}</div></div>', unsafe_allow_html=True)
        df_sp3 = get_sparkline_data(f'Consideration_{code}_slice', 'top2', where_clause, weight_col)
        st.altair_chart(create_sparkline_chart(df_sp3, '#ff007f'), use_container_width=True)

    with col4:
        val4 = f"{get_metric(f'Consideration_Effect_{code}_slice', 'top2', where_clause, weight_col)}%"
        st.markdown(f'<div class="kpi-container"><div class="kpi-header">Conversion Effect</div><div class="kpi-value" style="color: #ff9f43;">{val4}</div></div>', unsafe_allow_html=True)
        df_sp4 = get_sparkline_data(f'Consideration_Effect_{code}_slice', 'top2', where_clause, weight_col)
        st.altair_chart(create_sparkline_chart(df_sp4, '#ff9f43'), use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Brand Attribute Matrix Performance")

    attr_data = [
        {"Attribute": attr_map[i], "Value (%)": f"{get_metric(f'Attributes_New_DP_{code}_Q12a_{i}_slice', 'top2', where_clause, weight_col)}%"}
        for i in range(1, 18)
    ]
    
    df_matrix = pd.DataFrame(attr_data)
    
    html_table = "<table class='dark-matrix-table'><thead><tr><th>Attribute Statement</th><th>Performance Level</th></tr></thead><tbody>"
    for _, row in df_matrix.iterrows():
        html_table += f"<tr><td>{row['Attribute']}</td><td><strong style='color: #00f2fe;'>{row['Value (%)']}</strong></td></tr>"
    html_table += "</tbody></table>"
    
    st.markdown(html_table, unsafe_allow_html=True)

# -----------------------------
with tab2:
    colg1, colg2, colg3, colg4 = st.columns(4)

    with colg1:
        st.markdown('<div class="filter-label">🌍 Filter Country</div>', unsafe_allow_html=True)
        g_country = st.multiselect("Country", countries, key="g_country", label_visibility="collapsed")
    with colg2:
        st.markdown('<div class="filter-label">📅 Filter Month</div>', unsafe_allow_html=True)
        g_months = st.multiselect("Month", months, key="g_months", label_visibility="collapsed")
    with colg3:
        st.markdown('<div class="filter-label">👤 Segment Select</div>', unsafe_allow_html=True)
        g_segment = st.selectbox("Segment", ["Total", "Male", "Female"], key="g_segment", label_visibility="collapsed")
    with colg4:
        st.markdown('<div class="filter-label">🏢 Select Target Brand</div>', unsafe_allow_html=True)
        brand_map_local = get_brands_by_country(g_country)
        g_brand_sel = st.selectbox("Target Brand", list(brand_map_local.keys()), key="g_brand_single", label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Attractive Features Addition: Multi-metric Cross Analysis Line Visualization
    st.subheader("📊 Brand Health Funnel Trends & Cross-Attribute Analytics")
    
    graph_where = build_where(g_months, g_country, g_segment)
    g_code = brand_map_local[g_brand_sel]
    
    # Multi-Query Compilation to draw full structural trend lines inside a single view
    metrics_to_plot = [
        {"label": "Total Awareness", "col": f"Aided_Awareness_{g_code}_slice", "type": "yesno"},
        {"label": "Brand Favorability", "col": f"Brand_Favorability_{g_code}_slice", "type": "top2"},
        {"label": "Consideration Rate", "col": f"Consideration_{g_code}_slice", "type": "top2"},
        {"label": "Conversion Effect", "col": f"Consideration_Effect_{g_code}_slice", "type": "top2"},
    ]
    
    trend_queries = []
    for m_info in metrics_to_plot:
        c_name = m_info["col"]
        lbl = m_info["label"]
        if m_info["type"] == "yesno":
            trend_queries.append(f"""
                SELECT Month, '{lbl}' AS Metric, 
                SUM(CASE WHEN LOWER(TRIM({c_name}))='yes' THEN Global_weight_Stacked ELSE 0 END)*100.0/SUM(Global_weight_Stacked) AS Value 
                FROM df {graph_where} GROUP BY Month
            """)
        else:
            trend_queries.append(f"""
                SELECT Month, '{lbl}' AS Metric, 
                SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({c_name}), '\\d+') AS INTEGER) IN (4,5) THEN Global_weight_Stacked ELSE 0 END)*100.0 /
                SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({c_name}), '\\d+') AS INTEGER) BETWEEN 1 AND 5 THEN Global_weight_Stacked ELSE 0 END) AS Value 
                FROM df {graph_where} GROUP BY Month
            """)
            
    df_trends = con.execute(" UNION ALL ".join(trend_queries)).df()
    
    if not df_trends.empty:
        df_trends["Month_order"] = pd.Categorical(df_trends["Month"], categories=months, ordered=True)
        
        # Cyberpunk Neon Visual Palette Configuration
        neon_colors = ["#00f2fe", "#38ef7d", "#ff007f", "#ff9f43"]
        
        multi_line_chart = alt.Chart(df_trends).mark_line(point=True, size=3.5).encode(
            x=alt.X("Month_order:O", title="Timeline Phase", axis=alt.Axis(labelColor="#cbd5e1", titleColor="#ffffff", gridOpacity=0.1)),
            y=alt.Y("Value:Q", title="Percentage Share Score (%)", axis=alt.Axis(labelColor="#cbd5e1", titleColor="#ffffff", gridOpacity=0.1), scale=alt.Scale(zero=False)),
            color=alt.Color("Metric:N", scale=alt.Scale(range=neon_colors), legend=alt.Legend(title="Brand Funnel Layer", labelColor="#ffffff", titleColor="#00f2fe")),
            tooltip=["Month", "Metric", "Value"]
        ).properties(height=450).interactive()
        
        multi_line_chart = multi_line_chart.configure(background='transparent').configure_view(strokeOpacity=0)
        st.altair_chart(multi_line_chart, use_container_width=True)
    else:
        st.warning("⚠️ No tracking information matches the selected filter configuration parameters.")

# -----------------------------
with tab3:
    st.subheader("🤖 AI Analytics Chatbot (Insights Only)")
    user_query = st.text_input("Interrogate your analytical KPIs:")

    if user_query:
        st.markdown("✅ Insight response compiled (no chart visualization needed)")
