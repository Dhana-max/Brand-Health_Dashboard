import streamlit as st
import duckdb
import pandas as pd
import re
import altair as alt

st.set_page_config(layout="wide")

# ✅ Light UI styling
st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
}
div[data-testid="column"] {
    background-color: #f9fafb;
    padding: 12px;
    border-radius: 8px;
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
def get_brands_by_country(_):
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

    f1, f2, f3, f4 = st.columns([2,2,1,2])

    # ✅ COUNTRY (multiselect)
    with f1:
        st.markdown("**🌍 Country**")
        selected_countries = st.multiselect("", countries, default=countries)

    # ✅ MONTH (multiselect)
    with f2:
        st.markdown("**📅 Month**")
        selected_months = st.multiselect("", months, default=months)

    # ✅ SEGMENT
    with f3:
        st.markdown("**👤 Segment**")
        segment = st.selectbox("", ["Total", "Male", "Female"])

    # ✅ BRAND
    with f4:
        st.markdown("**🏢 Brand**")
        filtered_brand_map = get_brands_by_country(selected_countries)
        selected_brand = st.selectbox("", list(filtered_brand_map.keys()))

    code = filtered_brand_map[selected_brand]

    where_clause = build_where(selected_months, selected_countries, segment)
    weight_col = "Weight_Post" if len(selected_countries) == 1 else "Global_weight_Stacked"

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Awareness", f"{get_metric(f'Aided_Awareness_{code}_slice', 'yesno', where_clause, weight_col)}%")
    col2.metric("Favorability", f"{get_metric(f'Brand_Favorability_{code}_slice', 'top2', where_clause, weight_col)}%")
    col3.metric("Consideration", f"{get_metric(f'Consideration_{code}_slice', 'top2', where_clause, weight_col)}%")
    col4.metric("Effect", f"{get_metric(f'Consideration_Effect_{code}_slice', 'top2', where_clause, weight_col)}%")

# -----------------------------
with tab2:

    colg1, colg2, colg3, colg4 = st.columns(4)

    # ✅ COUNTRY multiselect
    g_country = colg1.multiselect("Country", countries, default=countries)

    # ✅ MONTH multiselect
    g_months = colg2.multiselect("Month", months, default=months)

    g_segment = colg3.selectbox("Segment", ["Total", "Male", "Female"])

    brand_map_local = get_brands_by_country(g_country)

    selected_brands = colg4.multiselect("Brands", list(brand_map_local.keys()),
                                        default=list(brand_map_local.keys())[:3])

    view_type = st.radio("View Type", ["Trended View", "Brand Comparison"], horizontal=True)

    graph_where = build_where(g_months, g_country, g_segment)

    queries = []
    for brand in selected_brands:
        code = brand_map_local[brand]
        col = f"Aided_Awareness_{code}_slice"

        queries.append(f"""
        SELECT Month,'{brand}' AS Brand,
        SUM(CASE WHEN LOWER(TRIM({col}))='yes'
        THEN Global_weight_Stacked ELSE 0 END)*100.0 /
        SUM(Global_weight_Stacked) AS Value
        FROM df {graph_where}
        GROUP BY Month
        """)

    df_chart = con.execute(" UNION ALL ".join(queries)).df()

    chart = alt.Chart(df_chart).mark_line(point=True).encode(
        x="Month",
        y="Value",
        color="Brand"
    )

    st.altair_chart(chart, use_container_width=True)

# -----------------------------
with tab3:
    st.subheader("🤖 Chatbot (Insights Only)")
    user_query = st.text_input("Ask about KPIs")

    if user_query:
        st.markdown("✅ Insight response here")
