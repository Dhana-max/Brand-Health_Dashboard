import streamlit as st
import duckdb
import pandas as pd
import re
import altair as alt
import plotly.graph_objects as go
from difflib import get_close_matches

st.set_page_config(layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

* { font-family: 'DM Sans', sans-serif; }

.block-container { padding-top: 1.5rem; }

/* KPI Funnel Card */
.funnel-card {
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
}

/* Donut summary card */
.summary-card {
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
}

.summary-title {
    font-size: 15px;
    font-weight: 700;
    color: #1e1e2d;
    margin-bottom: 4px;
}

/* Attribute bar rows */
.attr-row {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
    gap: 10px;
}
.attr-label {
    font-size: 12px;
    color: #555;
    width: 260px;
    flex-shrink: 0;
}
.attr-bar-bg {
    flex: 1;
    background: #f0f0f5;
    border-radius: 6px;
    height: 10px;
    overflow: hidden;
}
.attr-bar-fill {
    height: 10px;
    border-radius: 6px;
    background: linear-gradient(90deg, #c084fc, #818cf8);
}
.attr-value {
    font-size: 12px;
    font-weight: 600;
    color: #1e1e2d;
    width: 40px;
    text-align: right;
}

.section-header {
    font-size: 16px;
    font-weight: 700;
    color: #1e1e2d;
    margin-bottom: 12px;
}

div[data-testid="column"] {
    background-color: transparent !important;
    padding: 6px;
}
</style>
""", unsafe_allow_html=True)

st.title("Brand Health Dashboard")

PARQUET_URL = "https://github.com/Dhana-max/Brand-Health_Dashboard/releases/download/v1/data.parquet"
MAP_FILE = "Map.xlsx"

@st.cache_resource
def get_connection():
    con = duckdb.connect()
    con.execute(f"""
        CREATE VIEW df AS 
        SELECT * FROM read_parquet('{PARQUET_URL}')
    """)
    return con

con = get_connection()

@st.cache_data
def load_map():
    df = pd.read_excel(MAP_FILE, header=1)
    df.columns = df.columns.astype(str).str.strip()
    return df

map_df = load_map()

attr_map = {
    1: "Helps me move forward professionally",
    2: "Helps me find the right job for me",
    3: "Helps me navigate my professional life",
    4: "Is a place I feel I belong",
    5: "Cares about issues that matter to me",
    6: "Is a brand I love",
    7: "Is a brand I trust",
    8: "Makes me feel like I'm part of a community",
    9: "Helps me stay informed on professional topics",
    10: "Is a place where work-life discussions happen",
    11: "Is useful for me to visit every day",
    12: "Is a platform where I create/share content",
    13: "I use this more to create/share than before",
    14: "Is a platform I would use as part of my job",
    15: "Helps me reach my goals",
    16: "Is a locally relevant professional network",
    17: "Helps me move forward in my career/business"
}

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

# ─── TABS ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 Graphs", "🤖 Chatbot"])

# ═══════════════════════════════════════════════════════════════════════════
with tab1:

    # ── FILTERS ──────────────────────────────────────────────────────────
    f1, f2, f3, f4 = st.columns([2, 2, 1, 2])

    with f1:
        st.markdown("**🌍 Country**")
        select_all_country = st.checkbox("All", key="country_all")
        if select_all_country:
            selected_countries = countries
            st.caption(f"All selected ({len(countries)})")
        else:
            selected_countries = st.multiselect("", countries)

    with f2:
        st.markdown("**📅 Month**")
        select_all_month = st.checkbox("All", key="month_all")
        if select_all_month:
            selected_months = months
            st.caption(f"All selected ({len(months)})")
        else:
            selected_months = st.multiselect("", months)

    with f3:
        st.markdown("**👤 Segment**")
        segment = st.selectbox("", ["Total", "Male", "Female"])

    with f4:
        st.markdown("**🏢 Brand**")
        filtered_brand_map = get_brands_by_country(selected_countries)
        selected_brand = st.selectbox("", list(filtered_brand_map.keys()))

    code = filtered_brand_map[selected_brand]
    where_clause = build_where(selected_months, selected_countries, segment)
    weight_col = "Weight_Post" if len(selected_countries) == 1 else "Global_weight_Stacked"

    # ── FETCH KPI VALUES ─────────────────────────────────────────────────
    awareness    = get_metric(f"Aided_Awareness_{code}_slice",      "yesno", where_clause, weight_col)
    favorability = get_metric(f"Brand_Favorability_{code}_slice",   "top2",  where_clause, weight_col)
    consideration= get_metric(f"Consideration_{code}_slice",        "top2",  where_clause, weight_col)
    effect       = get_metric(f"Consideration_Effect_{code}_slice", "top2",  where_clause, weight_col)

    kpis = [
        {"label": "Awareness",      "value": awareness,     "color": "#f472b6"},
        {"label": "Favorability",   "value": favorability,  "color": "#c084fc"},
        {"label": "Consideration",  "value": consideration, "color": "#818cf8"},
        {"label": "Effect",         "value": effect,        "color": "#60a5fa"},
    ]

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── ROW 1: Funnel  +  Donut Summary ──────────────────────────────────
    col_funnel, col_summary = st.columns([6, 4])

    with col_funnel:
        st.markdown('<div class="section-header">KPI Funnel</div>', unsafe_allow_html=True)

        # Build a horizontal funnel using Plotly
        funnel_fig = go.Figure(go.Funnel(
            y   = [k["label"] for k in kpis],
            x   = [k["value"] for k in kpis],
            textposition = "inside",
            textinfo     = "value+percent initial",
            opacity      = 0.92,
            marker       = dict(
                color     = [k["color"] for k in kpis],
                line      = dict(width=1, color="white")
            ),
            connector    = dict(line=dict(color="rgba(0,0,0,0.05)", width=1))
        ))
        funnel_fig.update_layout(
            margin       = dict(l=10, r=10, t=10, b=10),
            paper_bgcolor= "white",
            plot_bgcolor = "white",
            font         = dict(family="DM Sans", size=13),
            height       = 280,
        )
        st.plotly_chart(funnel_fig, use_container_width=True)

    with col_summary:
        st.markdown('<div class="section-header">KPI Summary</div>', unsafe_allow_html=True)

        donut_colors = ["#f472b6", "#c084fc", "#818cf8", "#60a5fa"]

        d1, d2 = st.columns(2)
        pairs = [(d1, kpis[0]), (d2, kpis[1]), (d1, kpis[2]), (d2, kpis[3])]

        for col_widget, kpi in pairs:
            with col_widget:
                ring_fig = go.Figure(go.Pie(
                    values    = [kpi["value"], max(100 - kpi["value"], 0)],
                    hole      = 0.72,
                    direction = "clockwise",
                    sort      = False,
                    marker    = dict(colors=[kpi["color"], "#f3f4f6"]),
                    textinfo  = "none",
                    hoverinfo = "none",
                ))
                ring_fig.add_annotation(
                    text      = f"<b>{kpi['value']}%</b>",
                    x=0.5, y=0.5,
                    font      = dict(size=18, color="#1e1e2d", family="DM Sans"),
                    showarrow = False,
                )
                ring_fig.update_layout(
                    showlegend   = False,
                    margin       = dict(l=4, r=4, t=4, b=4),
                    paper_bgcolor= "white",
                    height       = 130,
                )
                st.plotly_chart(ring_fig, use_container_width=True)
                st.markdown(
                    f"<div style='text-align:center;font-size:12px;font-weight:600;"
                    f"color:#555;margin-top:-18px;margin-bottom:8px'>{kpi['label']}</div>",
                    unsafe_allow_html=True
                )

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── ROW 2: Brand Attributes styled bar chart ──────────────────────────
    st.markdown('<div class="section-header">Brand Attributes</div>', unsafe_allow_html=True)

    attr_data = [
        {
            "Attribute": attr_map[i],
            "Value (%)": get_metric(
                f"Attributes_New_DP_{code}_Q12a_{i}_slice",
                "top2", where_clause, weight_col
            )
        }
        for i in range(1, 18)
    ]
    attr_df = pd.DataFrame(attr_data).sort_values("Value (%)", ascending=False)

    # Gradient colour palette cycling across 17 attributes
    palette = [
        "#f472b6","#e879f9","#c084fc","#a78bfa",
        "#818cf8","#60a5fa","#38bdf8","#34d399",
        "#4ade80","#a3e635","#facc15","#fb923c",
        "#f87171","#fb7185","#e879f9","#c084fc","#818cf8"
    ]

    html_rows = ""
    for idx, row in enumerate(attr_df.itertuples()):
        bar_color = palette[idx % len(palette)]
        html_rows += f"""
        <div class="attr-row">
            <div class="attr-label">{row.Attribute}</div>
            <div class="attr-bar-bg">
                <div class="attr-bar-fill"
                     style="width:{row._2}%;background:{bar_color}"></div>
            </div>
            <div class="attr-value">{row._2}%</div>
        </div>
        """

    st.markdown(f"""
    <div style="background:white;border-radius:16px;padding:20px;
                box-shadow:0 2px 12px rgba(0,0,0,0.07);">
        {html_rows}
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
with tab2:

    colg1, colg2, colg3, colg4 = st.columns(4)

    g_country  = colg1.multiselect("Country", countries, key="g_country")
    g_months   = colg2.multiselect("Month", months, key="g_months")
    g_segment  = colg3.selectbox("Segment", ["Total", "Male", "Female"], key="g_segment")

    brand_map_local  = get_brands_by_country(g_country)
    selected_brands  = colg4.multiselect(
        "Brands", list(brand_map_local.keys()),
        default=list(brand_map_local.keys())[:3], key="g_brands"
    )

    view_type   = st.radio("View Type", ["Trended View", "Brand Comparison"], horizontal=True)
    graph_where = build_where(g_months, g_country, g_segment)

    queries = []
    for brand in selected_brands:
        bcode = brand_map_local[brand]
        col   = f"Aided_Awareness_{bcode}_slice"
        queries.append(f"""
        SELECT Month,'{brand}' AS Brand,
        SUM(CASE WHEN LOWER(TRIM({col}))='yes'
        THEN Global_weight_Stacked ELSE 0 END)*100.0 /
        SUM(Global_weight_Stacked) AS Value
        FROM df {graph_where}
        GROUP BY Month
        """)

    if queries:
        df_chart = con.execute(" UNION ALL ".join(queries)).df()
        df_chart["Month_order"] = pd.Categorical(df_chart["Month"], categories=months, ordered=True)

        if view_type == "Trended View":
            chart = alt.Chart(df_chart).mark_line(point=True).encode(
                x="Month_order:O", y="Value:Q", color="Brand"
            )
        else:
            chart = alt.Chart(df_chart).mark_line(point=True).encode(
                x="Brand", y="Value:Q", color="Month"
            )
        st.altair_chart(chart, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("🤖 Chatbot (Insights Only)")
    user_query = st.text_input("Ask about KPIs")

    if user_query:
        st.markdown("✅ Insight response here (no chart)")
