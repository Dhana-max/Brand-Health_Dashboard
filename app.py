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
    return con

con = get_connection()

# -----------------------------
@st.cache_data
def load_data():
    return con.execute(f"SELECT * FROM read_parquet('{PARQUET_URL}')").df()

df = load_data()

# -----------------------------
@st.cache_data
def load_map():
    df_map = pd.read_excel(MAP_FILE, header=1)
    df_map.columns = df_map.columns.astype(str).str.strip()
    return df_map

map_df = load_map()

# -----------------------------
months = df["Month"].dropna().unique().tolist()
countries = df["Country_New"].dropna().unique().tolist()

# ✅ SAFE DEFAULTS
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
    filters=[]
    if months_sel:
        filters.append(f"Month IN ({','.join([f'\"{m}\"' for m in months_sel])})")
    if countries_sel:
        filters.append(f"Country_New IN ({','.join([f'\"{c}\"' for c in countries_sel])})")
    if segment=="Male":
        filters.append("Sex=1")
    elif segment=="Female":
        filters.append("Sex=2")

    return "WHERE " + " AND ".join(filters) if filters else ""

# -----------------------------
def get_metric(col):
    try:
        q=f"""
        SELECT AVG(
            CASE WHEN LOWER(TRIM({col}))='yes' THEN 1 ELSE 0 END
        )*100
        FROM df {where_clause}
        """
        return round(con.execute(q).fetchone()[0] or 0,1)
    except:
        return 0

# -----------------------------
def local_chatbot(query):
    q=query.lower()

    for b in brand_map:
        if b.lower() in q:

            code=brand_map[b]

            # ✅ TREND
            if "trend" in q:

                trend=[]
                for m in months[:8]:

                    temp_where = build_where([m], selected_countries, segment)

                    global where_clause
                    old = where_clause
                    where_clause = temp_where

                    val=get_metric(f"Aided_Awareness_{code}_slice")

                    where_clause = old

                    trend.append(f"{m}: {val}%")

                return f"Trend for {b}:\n\n" + "\n".join(trend)

            # ✅ KPI
            if "awareness" in q:
                val=get_metric(f"Aided_Awareness_{code}_slice")
                return f"{b} awareness is {val}%"

    return "Try: LinkedIn awareness or trend linkedin"

# -----------------------------
tab1, tab2, tab3 = st.tabs(["📊 Dashboard","📈 Graphs","🤖 Chatbot"])

# -----------------------------
with tab1:

    c1,c2,c3,c4 = st.columns(4)

    selected_countries = c1.multiselect("Country", countries)
    selected_months = c2.multiselect("Month", months)
    segment = c3.selectbox("Segment", ["Total","Male","Female"])
    selected_brand = c4.selectbox("Brand", list(brand_map.keys()))

    code = brand_map[selected_brand]

    where_clause = build_where(selected_months, selected_countries, segment)

    m1 = st.metric("Awareness", f"{get_metric(f'Aided_Awareness_{code}_slice')}%")

# -----------------------------
with tab2:

    g1,g2,g3,g4=st.columns(4)

    g_country=g1.multiselect("Country",countries,key="g_country")
    g_months=g2.multiselect("Month",months,key="g_months")
    g_segment=g3.selectbox("Segment",["Total","Male","Female"],key="g_segment")

    brands_sel=g4.multiselect("Brands",list(brand_map.keys()),
                             default=list(brand_map.keys())[:2])

    where = build_where(g_months,g_country,g_segment)

    queries=[]

    for b in brands_sel:
        code=brand_map[b]
        queries.append(f"""
        SELECT Month,'{b}' Brand,
        AVG(CASE WHEN LOWER(TRIM(Aided_Awareness_{code}_slice))='yes' THEN 1 ELSE 0 END)*100 Value
        FROM df {where} GROUP BY Month
        """)

    if queries:
        df_chart = con.execute(" UNION ALL ".join(queries)).df()

        chart = alt.Chart(df_chart).mark_line(point=True).encode(
            x="Month", y="Value", color="Brand"
        )

        st.altair_chart(chart, use_container_width=True)

# -----------------------------
with tab3:

    q=st.text_input("Ask KPI Questions")

    if q:
        st.success(local_chatbot(q))
