import streamlit as st
import duckdb
import pandas as pd
import re
import altair as alt

st.set_page_config(layout="wide")
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

    months = df_temp.drop_duplicates("Month").sort_values("rn")["Month"].tolist()

    countries = con.execute("""
        SELECT DISTINCT Country_New FROM df WHERE Country_New IS NOT NULL
    """).df()["Country_New"].tolist()

    return months, countries

months, countries = load_filters()

# ✅ SAFE DEFAULTS (very important)
selected_countries = []
selected_months = []
segment = "Total"
where_clause = ""
weight_col = "Global_weight_Stacked"

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
def get_metric(col, metric_type="yesno"):
    try:
        if metric_type == "yesno":
            q = f"""
            SELECT SUM(CASE WHEN LOWER(TRIM({col}))='yes'
            THEN {weight_col} ELSE 0 END)*100.0 / SUM({weight_col})
            FROM df {where_clause}
            """
        return round(con.execute(q).fetchone()[0] or 0, 1)
    except:
        return 0

# -----------------------------
# ✅ CHATBOT (SAFE VERSION)

def local_chatbot(query):

    q = query.lower()

    for b in brand_map:
        if b.lower() in q:

            code = brand_map[b]

            # ✅ TREND (simple, safe)
            if "trend" in q:

                trend_data = []

                for m in months:

                    global where_clause
                    old_where = where_clause
                    where_clause = build_where([m], selected_countries, segment)

                    val = get_metric(f"Aided_Awareness_{code}_slice")

                    where_clause = old_where

                    trend_data.append(f"{m}: {val}%")

                return f"Trend for {b} (Awareness):\n\n" + "\n".join(trend_data[:8])

            # ✅ SINGLE KPI
            if "awareness" in q:
                val = get_metric(f"Aided_Awareness_{code}_slice")
                return f"{b} awareness is {val}%"

    return "Try: LinkedIn awareness or trend linkedin"

# -----------------------------
tab1, tab2, tab3 = st.tabs(["📊 Dashboard","📈 Graphs","🤖 Chatbot"])

# -----------------------------
with tab1:

    c1, c2, c3, c4 = st.columns(4)

    selected_countries = c1.multiselect("Country", countries)
    selected_months = c2.multiselect("Month", months)
    segment = c3.selectbox("Segment", ["Total", "Male", "Female"])
    selected_brand = c4.selectbox("Brand", list(brand_map.keys()))

    code = brand_map[selected_brand]

    where_clause = build_where(selected_months, selected_countries, segment)
    weight_col = "Weight_Post" if len(selected_countries) == 1 else "Global_weight_Stacked"

    m1 = st.metric("Awareness", f"{get_metric(f'Aided_Awareness_{code}_slice')}%")

# -----------------------------
with tab2:

    g1, g2, g3, g4 = st.columns(4)

    g_country = g1.multiselect("Country", countries, key="g_country")
    g_months = g2.multiselect("Month", months, key="g_months")
    g_segment = g3.selectbox("Segment", ["Total", "Male", "Female"], key="g_segment")

    brands_sel = g4.multiselect("Brands", list(brand_map.keys()),
                               default=list(brand_map.keys())[:3])

    where = build_where(g_months, g_country, g_segment)

    queries = []

    for b in brands_sel:
        code = brand_map[b]
        queries.append(f"""
        SELECT Month,'{b}' Brand,
        SUM(CASE WHEN LOWER(TRIM(Aided_Awareness_{code}_slice))='yes'
        THEN Global_weight_Stacked ELSE 0 END)*100.0 /
        SUM(Global_weight_Stacked) Value
        FROM df {where}
        GROUP BY Month
        """)

    if queries:
        df_chart = con.execute(" UNION ALL ".join(queries)).df()

        chart = alt.Chart(df_chart).mark_line(point=True).encode(
            x="Month", y="Value", color="Brand"
        )

        st.altair_chart(chart, use_container_width=True)

# -----------------------------
with tab3:

    user_query = st.text_input("Ask KPI Questions")

    if user_query:
        st.success(local_chatbot(user_query))
