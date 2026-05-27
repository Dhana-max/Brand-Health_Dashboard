import streamlit as st
import duckdb
import pandas as pd
import re
import altair as alt
from difflib import get_close_matches

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
            SELECT SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5)
            THEN {weight_col} ELSE 0 END)*100.0 /
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) BETWEEN 1 AND 5
            THEN {weight_col} ELSE 0 END)
            FROM df {where_clause}
            """
        return round(con.execute(q).fetchone()[0] or 0,1)
    except:
        return 0

# -----------------------------
# ✅ ✅ TYPO-FRIENDLY CHATBOT

def find_metric_word(query):
    words = ["awareness", "favorability", "favourability", "consideration", "effect"]

    matches = get_close_matches(query, words, n=1, cutoff=0.6)

    if matches:
        m = matches[0]
        if m in ["favorability", "favourability"]:
            return "favorability"
        return m
    return None

def extract_brand(query):
    matches = get_close_matches(query, list(brand_map.keys()), n=1, cutoff=0.6)
    return matches[0] if matches else None

def local_chatbot(query):

    q = query.lower()

    brand = extract_brand(q)
    metric = find_metric_word(q)

    if not brand:
        return "Please mention a brand."

    code = brand_map[brand]

    if not metric:
        return "Ask about awareness, favorability, consideration or effect."

    if metric == "awareness":
        col = f"Aided_Awareness_{code}_slice"
        val = get_metric(col, "yesno")
    else:
        col_map = {
            "favorability": "Brand_Favorability",
            "consideration": "Consideration",
            "effect": "Consideration_Effect"
        }
        col = f"{col_map[metric]}_{code}_slice"
        val = get_metric(col)

    return f"{brand} {metric} is {val}%"

# -----------------------------
tab1, tab2, tab3 = st.tabs(["📊 Dashboard","📈 Graphs","🤖 Chatbot"])

# -----------------------------
with tab1:
    colf1, colf2, colf3, colf4 = st.columns(4)

    selected_countries = colf1.multiselect("Country", countries)
    selected_months = colf2.multiselect("Month", months)
    segment = colf3.selectbox("Segment", ["Total","Male","Female"])

    filtered_brand_map = get_brands_by_country(selected_countries)
    selected_brand = colf4.selectbox("Brand", list(filtered_brand_map.keys()))

    code = filtered_brand_map[selected_brand]

    where_clause = build_where(selected_months, selected_countries, segment)
    weight_col = "Weight_Post" if len(selected_countries)==1 else "Global_weight_Stacked"

# -----------------------------
with tab3:
    st.subheader("🤖 Ask KPI Questions")

    user_query = st.text_input("Ask about KPIs")

    if user_query:
        response = local_chatbot(user_query)
        st.success(response)
