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
        SELECT Month, ROW_NUMBER() OVER() rn 
        FROM df WHERE Month IS NOT NULL
    """).df()

    months = df_temp.drop_duplicates("Month").sort_values("rn")["Month"].tolist()

    countries = con.execute("""
        SELECT DISTINCT Country_New 
        FROM df WHERE Country_New IS NOT NULL
    """).df()["Country_New"].tolist()

    return months, countries

months, countries = load_filters()

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

# ✅ ATTRIBUTE MAP
attr_map = {i: f"Attribute {i}" for i in range(1,18)}

# -----------------------------
def build_where(months_sel, countries_sel, segment):
    f = []
    if months_sel:
        f.append("Month IN (" + ",".join(f"'{m}'" for m in months_sel) + ")")
    if countries_sel:
        f.append("Country_New IN (" + ",".join(f"'{c}'" for c in countries_sel) + ")")
    if segment == "Male":
        f.append("Sex=1")
    elif segment == "Female":
        f.append("Sex=2")
    return "WHERE " + " AND ".join(f) if f else ""

# -----------------------------
def get_metric(col):
    try:
        q = f"""
        SELECT SUM(CASE WHEN LOWER(TRIM({col}))='yes'
        THEN {weight_col} ELSE 0 END)*100.0 /
        SUM({weight_col})
        FROM df {where_clause}
        """
        return round(con.execute(q).fetchone()[0] or 0,1)
    except:
        return 0

# -----------------------------
# ✅ CHATBOT (extended)
def local_chatbot(q):

    q = q.lower()

    for b in brand_map:
        if b.lower() in q:

            code = brand_map[b]

            # ✅ ATTRIBUTE QUERY
            for i in range(1,18):
                if f"attribute {i}" in q:
                    val = get_metric(f"Attributes_New_DP_{code}_Q12a_{i}_slice")
                    return f"{b} Attribute {i} is {val}%"

            # ✅ TREND
            if "trend" in q:
                data = []

                for m in months:
                    global where_clause
                    old = where_clause
                    where_clause = build_where([m], selected_countries, segment)

                    val = get_metric(f"Aided_Awareness_{code}_slice")

                    where_clause = old
                    data.append(f"{m}: {val}%")

                return f"Trend for {b}:\n\n" + "\n".join(data[:8])

            # ✅ KPI
            if "awareness" in q:
                val = get_metric(f"Aided_Awareness_{code}_slice")
                return f"{b} awareness is {val}%"

    return "Try: LinkedIn awareness / trend linkedin / attribute 1 linkedin"

# -----------------------------
tab1, tab2, tab3 = st.tabs(["📊 Dashboard","📈 Graphs","🤖 Chatbot"])

# =============================
# ✅ DASHBOARD (ATTRIBUTES ADDED)
# =============================
with tab1:

    c1,c2,c3,c4 = st.columns(4)

    selected_countries = c1.multiselect("Country", countries)
    selected_months = c2.multiselect("Month", months)
    segment = c3.selectbox("Segment", ["Total","Male","Female"])
    selected_brand = c4.selectbox("Brand", list(brand_map.keys()))

    code = brand_map[selected_brand]

    where_clause = build_where(selected_months, selected_countries, segment)
    weight_col = "Weight_Post" if len(selected_countries)==1 else "Global_weight_Stacked"

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Awareness", f"{get_metric(f'Aided_Awareness_{code}_slice')}%")
    m2.metric("Favorability", f"{get_metric(f'Brand_Favorability_{code}_slice')}%")
    m3.metric("Consideration", f"{get_metric(f'Consideration_{code}_slice')}%")
    m4.metric("Effect", f"{get_metric(f'Consideration_Effect_{code}_slice')}%")

    # ✅ ATTRIBUTES TABLE
    st.subheader("Attributes")

    attr_data = [
        {
            "Attribute": attr_map[i],
            "Value (%)": get_metric(f"Attributes_New_DP_{code}_Q12a_{i}_slice")
        }
        for i in range(1,18)
    ]

    st.dataframe(pd.DataFrame(attr_data), use_container_width=True)

# =============================
# ✅ GRAPHS (ATTRIBUTE SUPPORT)
# =============================
with tab2:

    g1,g2,g3,g4,g5 = st.columns(5)

    g_country = g1.multiselect("Country", countries, key="g_country")
    g_months = g2.multiselect("Month", months, key="g_months")
    g_segment = g3.selectbox("Segment", ["Total","Male","Female"], key="g_segment")

    brands_sel = g4.multiselect(
        "Brands",
        list(brand_map.keys()),
        default=list(brand_map.keys())[:3]
    )

    kpi_choice = g5.selectbox(
        "Metric",
        ["Awareness","Favorability","Consideration","Effect"] +
        [f"Attribute {i}" for i in range(1,18)]
    )

    view = st.radio("View Type", ["Trended View","Brand Comparison"], horizontal=True)

    if not brands_sel:
        brands_sel = list(brand_map.keys())[:3]

    where = build_where(g_months, g_country, g_segment)

    queries = []

    for b in brands_sel:
        code = brand_map[b]

        if "Attribute" in kpi_choice:
            i = int(kpi_choice.split()[1])
            col_name = f"Attributes_New_DP_{code}_Q12a_{i}_slice"
        else:
            col_name = {
                "Awareness": f"Aided_Awareness_{code}_slice",
                "Favorability": f"Brand_Favorability_{code}_slice",
                "Consideration": f"Consideration_{code}_slice",
                "Effect": f"Consideration_Effect_{code}_slice"
            }[kpi_choice]

        queries.append(f"""
        SELECT Month AS Month, '{b}' AS Brand,
        SUM(CASE WHEN LOWER(TRIM({col_name}))='yes'
        THEN Global_weight_Stacked ELSE 0 END)*100.0 /
        SUM(Global_weight_Stacked) AS Value
        FROM df {where}
        GROUP BY Month
        """)

    if queries:
        df_chart = con.execute(" UNION ALL ".join(queries)).df()

        if view=="Trended View":
            chart = alt.Chart(df_chart).mark_line(point=True).encode(
                x="Month", y="Value", color="Brand"
            )
        else:
            chart = alt.Chart(df_chart).mark_line(point=True).encode(
                x="Brand", y="Value", color="Month"
            )

        st.altair_chart(chart, use_container_width=True)

# =============================
# ✅ CHATBOT
# =============================
with tab3:

    q = st.text_input("Ask KPI Questions")

    if q:
        st.success(local_chatbot(q))
