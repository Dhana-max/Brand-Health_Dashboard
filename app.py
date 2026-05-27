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
attr_map = {
    1:"Helps me move forward professionally",
    2:"Helps me find the right job for me",
    3:"Helps me navigate my professional life",
    4:"Is a place I feel I belong",
    5:"Cares about issues that matter to me",
    6:"Is a brand I love",
    7:"Is a brand I trust",
    8:"Makes me feel like I'm part of a community",
    9:"Helps me stay informed on professional topics",
    10:"Work related discussions happen",
    11:"Useful daily",
    12:"Create/share content",
    13:"Increased content usage",
    14:"Used for job",
    15:"Helps reach goals",
    16:"Local relevance",
    17:"Helps business growth"
}

# -----------------------------
@st.cache_data
def load_filters():
    df_temp = con.execute("""
        SELECT Month, ROW_NUMBER() OVER() rn
        FROM df WHERE Month IS NOT NULL
    """).df()

    months = df_temp.drop_duplicates("Month").sort_values("rn")["Month"].tolist()

    countries = con.execute("""
        SELECT DISTINCT Country_New FROM df WHERE Country_New IS NOT NULL
    """).df()["Country_New"].tolist()

    return months, countries

months, countries = load_filters()

# ✅ ✅ VERY IMPORTANT FIX (prevents blank screen)
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
def get_metric(col, metric_type="top2"):
    try:
        if metric_type == "yesno":
            q = f"""
            SELECT SUM(CASE WHEN LOWER(TRIM({col}))='yes'
            THEN {weight_col} ELSE 0 END)*100.0/SUM({weight_col})
            FROM df {where_clause}
            """
        else:
            q = f"""
            SELECT SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INT) IN (4,5)
            THEN {weight_col} ELSE 0 END)*100.0 /
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INT) BETWEEN 1 AND 5
            THEN {weight_col} ELSE 0 END)
            FROM df {where_clause}
            """
        return round(con.execute(q).fetchone()[0] or 0,1)
    except:
        return 0

# -----------------------------
def run_with_filters(m, c, s, func):
    global where_clause, weight_col

    old_where = where_clause
    old_weight = weight_col

    where_clause = build_where(m, c, s)
    weight_col = "Weight_Post" if c and len(c)==1 else "Global_weight_Stacked"

    result = func()

    where_clause = old_where
    weight_col = old_weight

    return result

# -----------------------------
# ✅ CHATBOT

def local_chatbot(query):

    q = query.lower()
    brands = [b for b in brand_map if b.lower() in q]

    if not brands:
        return "Please mention a valid brand."

    # ✅ COMPARISON
    if ("compare" in q or "vs" in q) and len(brands)>=2:

        b1, b2 = brands[0], brands[1]

        v1 = get_metric(f"Aided_Awareness_{brand_map[b1]}_slice","yesno")
        v2 = get_metric(f"Aided_Awareness_{brand_map[b2]}_slice","yesno")

        diff = round(v1 - v2,1)
        leader = b1 if diff>=0 else b2

        return f"{b1}: {v1}% | {b2}: {v2}%\n✅ {leader} leads by {abs(diff)}%"

    brand = brands[0]

    # ✅ Month detection
    selected_month = None
    for m in months:
        if m.lower() in q or m.lower().replace(" ","") in q:
            selected_month = m
            break

    # ✅ TREND WITH MONTH ✅ (FIXED)
    if "trend" in q and selected_month:

        idx = months.index(selected_month)

        current = run_with_filters([selected_month], selected_countries, segment,
            lambda: get_metric(f"Aided_Awareness_{brand_map[brand]}_slice","yesno")
        )

        out = f"{brand} awareness in {selected_month} is {current}%\n\n📊 Insights:"

        # MoM
        if idx > 0:
            prev = months[idx-1]
            prev_val = run_with_filters([prev], selected_countries, segment,
                lambda: get_metric(f"Aided_Awareness_{brand_map[brand]}_slice","yesno")
            )
            d = round(current - prev_val,1)
            out += f"\n• vs {prev}: {d}% {'📈' if d>0 else '📉'}"

        # YoY
        parts = selected_month.split()
        if len(parts)==2:
            yoy = f"{parts[0]} {int(parts[1])-1}"
            if yoy in months:
                yoy_val = run_with_filters([yoy], selected_countries, segment,
                    lambda: get_metric(f"Aided_Awareness_{brand_map[brand]}_slice","yesno")
                )
                d = round(current - yoy_val,1)
                out += f"\n• vs {yoy}: {d}% {'📈' if d>0 else '📉'}"

        return out

    # ✅ FULL TREND
    if "trend" in q:

        data=[]
        for m in months:
            val = run_with_filters([m], selected_countries, segment,
                lambda:get_metric(f"Aided_Awareness_{brand_map[brand]}_slice","yesno")
            )
            data.append(f"{m}: {val}%")

        return f"Trend for {brand}:\n\n" + "\n".join(data[:8])

    # ✅ KPI
    if "awareness" in q:
        val = get_metric(f"Aided_Awareness_{brand_map[brand]}_slice","yesno")
        return f"{brand} awareness is {val}%"

    if "favor" in q:
        val = get_metric(f"Brand_Favorability_{brand_map[brand]}_slice")
        return f"{brand} favorability is {val}%"

    return "Try: LinkedIn awareness / trend linkedin / compare linkedin vs indeed"

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
    weight_col = "Weight_Post" if len(selected_countries)==1 else "Global_weight_Stacked"

    m1,m2,m3,m4 = st.columns(4)

    m1.metric("Awareness", f"{get_metric(f'Aided_Awareness_{code}_slice','yesno')}%")
    m2.metric("Favorability", f"{get_metric(f'Brand_Favorability_{code}_slice')}%")
    m3.metric("Consideration", f"{get_metric(f'Consideration_{code}_slice')}%")
    m4.metric("Effect", f"{get_metric(f'Consideration_Effect_{code}_slice')}%")

    st.subheader("Brand Attributes")

    attr_data = [{"Attribute":attr_map[i],
                  "Value (%)":get_metric(f"Attributes_New_DP_{code}_Q12a_{i}_slice")} 
                 for i in range(1,18)]

    st.dataframe(pd.DataFrame(attr_data), use_container_width=True)

# -----------------------------
with tab2:

    g1,g2,g3,g4 = st.columns(4)

    g_country = g1.multiselect("Country", countries, key="g_country")
    g_months = g2.multiselect("Month", months, key="g_months")
    g_segment = g3.selectbox("Segment", ["Total","Male","Female"], key="g_segment")

    brands_sel = g4.multiselect("Brands", list(brand_map.keys()),
                               default=list(brand_map.keys())[:3])

    view = st.radio("View Type", ["Trended View","Brand Comparison"], horizontal=True)

    where = build_where(g_months, g_country, g_segment)

    queries=[]

    for b in brands_sel:
        code = brand_map[b]
        queries.append(f"""
        SELECT Month,'{b}' Brand,
        SUM(CASE WHEN LOWER(TRIM(Aided_Awareness_{code}_slice))='yes'
        THEN Global_weight_Stacked ELSE 0 END)*100.0 /
        SUM(Global_weight_Stacked) Value
        FROM df {where} GROUP BY Month
        """)

    df_chart = con.execute(" UNION ALL ".join(queries)).df()

    if view=="Trended View":
        chart = alt.Chart(df_chart).mark_line(point=True).encode(
            x="Month", y="Value", color="Brand")
    else:
        chart = alt.Chart(df_chart).mark_line(point=True).encode(
            x="Brand", y="Value", color="Month")

    st.altair_chart(chart, use_container_width=True)

# -----------------------------
with tab3:

    q = st.text_input("Ask KPI Questions")

    if q:
        st.success(local_chatbot(q))
