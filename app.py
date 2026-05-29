import streamlit as st
import duckdb
import pandas as pd
import re
import altair as alt
from difflib import get_close_matches

st.set_page_config(layout="wide")

# ==========================================
# 🎨 POWER BI INITIATED DARK THEME STYLING
# ==========================================
st.markdown("""
<style>
    /* Global Background and Text Color */
    .stApp {
        background: linear-gradient(180deg, #1f1b2c 0%, #12101a 100%);
        color: #e5e7eb;
    }
    
    /* Header / Subheader Customization */
    h1, h2, h3, h4, h5, h6, .stSubheader p {
        color: #ffffff !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 600;
    }
    
    /* Grid Container Cards matching Dashboard Boxes */
    div[data-testid="column"] {
        background-color: rgba(30, 27, 46, 0.7) !important;
        padding: 20px !important;
        border-radius: 6px !important;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    
    /* Custom Styling for Streamlit Metrics */
    div[data-testid="stMetricValue"] {
        font-size: 2.4rem !important;
        font-weight: 300 !important;
        color: #ffffff !important;
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 0.9rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #9ca3af !important;
    }
    
    /* Form controls (Selectboxes, Multiselects, Checkboxes) formatting */
    .stSelectbox div, .stMultiSelect div {
        background-color: #2a243d !important;
        color: #ffffff !important;
    }
    
    /* ⚡ FIX: Force Native Markdown/HTML Tables to be legible in Dark Theme */
    .dark-table {
        width: 100%;
        border-collapse: collapse;
        color: #ffffff;
        font-family: sans-serif;
        background-color: #1e1b2e;
        border-radius: 6px;
        overflow: hidden;
    }
    .dark-table th {
        background-color: #2a243d;
        color: #00f2fe;
        text-align: left;
        padding: 12px;
        font-weight: 600;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
    }
    .dark-table td {
        padding: 10px 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    .dark-table tr:hover {
        background-color: rgba(255, 255, 255, 0.03);
    }
    
    /* Tab Styling styling */
    button[data-baseweb="tab"] {
        color: #9ca3af !important;
        font-weight: 500;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #00f2fe !important;
        border-bottom-color: #00f2fe !important;
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
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 Graphs", "🤖 Chatbot"])

# -----------------------------
with tab1:
    # Filter Bar Container
    f1, f2, f3, f4 = st.columns([2,2,1,2])

    with f1:
        st.markdown("**🌍 Country**")
        select_all_country = st.checkbox("All", key="country_all")
        if select_all_country:
            selected_countries = countries
            st.caption(f"All selected ({len(countries)})")
        else:
            selected_countries = st.multiselect("", countries, label_visibility="collapsed")

    with f2:
        st.markdown("**📅 Month**")
        select_all_month = st.checkbox("All", key="month_all")
        if select_all_month:
            selected_months = months
            st.caption(f"All selected ({len(months)})")
        else:
            selected_months = st.multiselect("", months, label_visibility="collapsed")

    with f3:
        st.markdown("**👤 Segment**")
        segment = st.selectbox("", ["Total", "Male", "Female"], label_visibility="collapsed")

    with f4:
        st.markdown("**🏢 Brand**")
        filtered_brand_map = get_brands_by_country(selected_countries)
        selected_brand = st.selectbox("", list(filtered_brand_map.keys()), label_visibility="collapsed")

    code = filtered_brand_map[selected_brand]
    where_clause = build_where(selected_months, selected_countries, segment)
    weight_col = "Weight_Post" if len(selected_countries) == 1 else "Global_weight_Stacked"

    st.markdown("<br>", unsafe_allow_html=True)
    
    # KPIs Layout Row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Awareness", f"{get_metric(f'Aided_Awareness_{code}_slice', 'yesno', where_clause, weight_col)}%")
    col2.metric("Brand Favorability", f"{get_metric(f'Brand_Favorability_{code}_slice', 'top2', where_clause, weight_col)}%")
    col3.metric("Consideration Rate", f"{get_metric(f'Consideration_{code}_slice', 'top2', where_clause, weight_col)}%")
    col4.metric("Conversion Effect", f"{get_metric(f'Consideration_Effect_{code}_slice', 'top2', where_clause, weight_col)}%")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Brand Attribute Matrix Breakdown")

    attr_data = [
        {"Attribute": attr_map[i], "Value (%)": f"{get_metric(f'Attributes_New_DP_{code}_Q12a_{i}_slice', 'top2', where_clause, weight_col)}%"}
        for i in range(1, 18)
    ]
    
    # ✅ FIXED: Render table using raw HTML with styles injected to resolve the blank dark-screen issue
    df_matrix = pd.DataFrame(attr_data)
    
    html_table = "<table class='dark-table'><thead><tr><th>Attribute</th><th>Value (%)</th></tr></thead><tbody>"
    for _, row in df_matrix.iterrows():
        html_table += f"<tr><td>{row['Attribute']}</td><td><strong>{row['Value (%)']}</strong></td></tr>"
    html_table += "</tbody></table>"
    
    st.markdown(html_table, unsafe_allow_html=True)

# -----------------------------
with tab2:
    colg1, colg2, colg3, colg4 = st.columns(4)

    g_country = colg1.multiselect("Country", countries, key="g_country")
    g_months = colg2.multiselect("Month", months, key="g_months")
    g_segment = colg3.selectbox("Segment", ["Total", "Male", "Female"], key="g_segment")

    brand_map_local = get_brands_by_country(g_country)
    selected_brands = colg4.multiselect("Brands", list(brand_map_local.keys()),
                                        default=list(brand_map_local.keys())[:3], key="g_brands")

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

            # 📊 Altair Dashboard Theme Configuration
            chart_color_palette = ["#4ef2d2", "#ff4a68", "#e0b3ff", "#f5d061", "#4ca5ff"]

            if view_type == "Trended View":
                chart = alt.Chart(df_chart).mark_line(point=True, size=3).encode(
                    x=alt.X("Month_order:O", title="Timeline Phase", axis=alt.Axis(labelColor="#9ca3af", titleColor="#ffffff")),
                    y=alt.Y("Value:Q", title="Percentage Share (%)", axis=alt.Axis(labelColor="#9ca3af", titleColor="#ffffff"), scale=alt.Scale(zero=False)),
                    color=alt.Color("Brand:N", scale=alt.Scale(range=chart_color_palette))
                ).properties(height=400)
            else:
                chart = alt.Chart(df_chart).mark_line(point=True, size=3).encode(
                    x=alt.X("Brand:N", title="Competitor Space", axis=alt.Axis(labelColor="#9ca3af", titleColor="#ffffff")),
                    y=alt.Y("Value:Q", title="Percentage Share (%)", axis=alt.Axis(labelColor="#9ca3af", titleColor="#ffffff"), scale=alt.Scale(zero=False)),
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
