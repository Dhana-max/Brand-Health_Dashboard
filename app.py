import streamlit as st
import duckdb
import pandas as pd
import re
import altair as alt

st.set_page_config(layout="wide")
st.title("Brand Health Dashboard")

PARQUET_URL = "https://github.com/Dhana-max/Brand-Health_Dashboard/releases/download/v1/data.parquet"

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
months = df["Month"].dropna().unique().tolist()
countries = df["Country_New"].dropna().unique().tolist()

# ✅ SAFE DEFAULTS
selected_countries = []
selected_months = []
segment = "Total"
where_clause = ""

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
def get_metric(col):
    try:
        q = f"""
        SELECT AVG(
            CASE WHEN LOWER(TRIM({col}))='yes' THEN 1 ELSE 0 END
        ) * 100
        FROM df {where_clause}
        """
        return round(con.execute(q).fetchone()[0] or 0, 1)
    except:
        return 0

# -----------------------------
def local_chatbot(query):

    q = query.lower()

    if "linkedin" in q:

        if "trend" in q:
            trend = []

            for m in months[:8]:

                temp = build_where([m], selected_countries, segment)

                global where_clause
                old = where_clause
                where_clause = temp

                val = get_metric("Aided_Awareness_1_slice")

                where_clause = old

                trend.append(f"{m}: {val}%")

            return "Trend for LinkedIn:\n\n" + "\n".join(trend)

        if "awareness" in q:
            val = get_metric("Aided_Awareness_1_slice")
            return f"LinkedIn awareness is {val}%"

    return "Try: LinkedIn awareness or trend linkedin"

# -----------------------------
tab1, tab2, tab3 = st.tabs(["📊 Dashboard","📈 Graphs","🤖 Chatbot"])

# -----------------------------
with tab1:

    c1, c2, c3, c4 = st.columns(4)

    selected_countries = c1.multiselect("Country", countries)
    selected_months = c2.multiselect("Month", months)
    segment = c3.selectbox("Segment", ["Total", "Male", "Female"])

    where_clause = build_where(selected_months, selected_countries, segment)

    val = get_metric("Aided_Awareness_1_slice")

    st.metric("LinkedIn Awareness", f"{val}%")

# -----------------------------
with tab2:

    g_country = st.multiselect("Country", countries)
    g_months = st.multiselect("Month", months)

    where = build_where(g_months, g_country, "Total")

    query = f"""
    SELECT Month,
    AVG(CASE WHEN LOWER(TRIM(Aided_Awareness_1_slice))='yes' THEN 1 ELSE 0 END)*100 Value
    FROM df {where}
    GROUP BY Month
    """

    df_chart = con.execute(query).df()

    chart = alt.Chart(df_chart).mark_line(point=True).encode(
        x="Month", y="Value"
    )

    st.altair_chart(chart, use_container_width=True)

# -----------------------------
with tab3:

    q = st.text_input("Ask KPI Questions")

    if q:
        st.success(local_chatbot(q))
