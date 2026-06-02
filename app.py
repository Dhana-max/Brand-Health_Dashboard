import streamlit as st
import duckdb
import pandas as pd
import re
import altair as alt

# 1. Initialize native wide parameters
st.set_page_config(layout="wide")

# 2. Premium Clean White Executive Theme Custom CSS Injector
st.markdown("""
<style>

/* ===== FULL DARK BACKGROUND ===== */
.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: #e5e7eb;
}

/* ===== GLASS CONTAINER ===== */
div[data-testid="stContainer"] {
    background: rgba(30, 41, 59, 0.6);
    backdrop-filter: blur(14px);
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 10px 40px rgba(0,0,0,0.4);
    padding: 16px;
}

/* ===== TITLE ===== */
h1 {
    color: #f8fafc;
    font-weight: 800;
}

/* ===== KPI CARDS ===== */
.kpi-card {
    padding: 18px;
    border-radius: 16px;
    color: white;
    backdrop-filter: blur(8px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.4);
}

/* ===== NEON KPI COLORS ===== */
.kpi-pink {
    background: linear-gradient(135deg, #ff4d79, #ff2a6d);
}
.kpi-purple {
    background: linear-gradient(135deg, #7c3aed, #4f46e5);
}
.kpi-blue {
    background: linear-gradient(135deg, #0ea5e9, #2563eb);
}
.kpi-orange {
    background: linear-gradient(135deg, #f59e0b, #fb923c);
}

/* KPI TEXT */
.kpi-title {
    font-size: 12px;
    text-transform: uppercase;
    opacity: 0.75;
}
.kpi-value {
    font-size: 36px;
    font-weight: 900;
}

/* Hover glow */
.kpi-card:hover {
    transform: translateY(-4px);
    transition: 0.3s ease;
    box-shadow: 0 15px 50px rgba(0,0,0,0.6);
}

/* Inputs (dark) */
.stSelectbox, .stMultiSelect, .stTextInput {
    background: #1e293b !important;
    color: white !important;
    border-radius: 10px;
}
/* ===== FIX TEXT VISIBILITY ===== */

label, .stMarkdown, .stText, .stCaption {
    color: #e5e7eb !important;
}

/* Radio button text */
div[role="radiogroup"] label {
    color: #e5e7eb !important;
    font-size: 14px;
}

/* Dropdown text */
div[data-baseweb="select"] {
    color: #e5e7eb !important;
}

/* Vega charts (axis text) */
.vega-embed text {
    fill: #e5e7eb !important;
}

/* Titles & headers */
h1, h2, h3 {
    color: #f8fafc !important;
}

/* Small text */
small, span {
    color: #9ca3af !important;
}
/* ===== PILL SELECTOR (RADIO TRANSFORM) ===== */

div[role="radiogroup"] {
    display: flex;
    gap: 10px;
    background: rgba(255,255,255,0.04);
    padding: 6px;
    border-radius: 12px;
}

/* ✅ FIX: Unselected pills visible */
div[role="radiogroup"] label {
    background: rgba(255,255,255,0.10);  /* brighter */
    padding: 10px 16px;
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.15);

    color: #e5e7eb !important;   /* brighter text */
    opacity: 1 !important;       /* remove fade completely */

    cursor: pointer;
    transition: all 0.25s ease;
}
/* ✅ Force all inner text/icons visible */
div[role="radiogroup"] label * {
    color: #e5e7eb !important;
}


/* Hover effect */
div[role="radiogroup"] label:hover {
    background: rgba(124, 58, 237, 0.2);
    color: #ffffff !important;
    opacity: 1;
}

/* ✅ Selected radio pill FIX */
div[role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
    border: none;
    color: #ffffff !important;
    opacity: 1 !important;
    box-shadow: 0 0 12px rgba(124,58,237,0.7);
}
div[role="radiogroup"] label:has(input:checked) * {
    color: #ffffff !important;
}
/* Hide default radio circle */
div[role="radiogroup"] input {
    display: none;
}

/* Label text spacing fix */
div[role="radiogroup"] div {
    padding: 4px 10px;
}

/* Section label */
.pillar-label {
    color: #9ca3af;
    font-size: 13px;
    margin-bottom: 6px;
}
/* ✅ FIX: Streamlit Tabs Text Visibility */

/* Tab container */
div[data-baseweb="tab-list"] {
    gap: 20px;
}

/* All tabs (default state) */
button[data-baseweb="tab"] {
    color: #9ca3af !important;   /* brighter gray */
    font-weight: 600;
    opacity: 1 !important;       /* remove fading */
    transition: all 0.25s ease;
}

/* Hover effect */
button[data-baseweb="tab"]:hover {
    color: #ffffff !important;
}

/* ✅ ACTIVE tab */
button[aria-selected="true"] {
    color: #ff4d79 !important;   /* matches your pink highlight */
}

/* Optional: make underline stronger */
button[aria-selected="true"]::after {
    background-color: #ff4d79 !important;
    height: 3px;
}
</style>
""", unsafe_allow_html=True)
# Clean, corporate title matching your specification
st.title("Consumer Brand Tracker Dashboard")

PARQUET_URL = "https://github.com/Dhana-max/Brand-Health_Dashboard/releases/download/v1/data.parquet"
MAP_FILE = "Map.xlsx"

# -----------------------------
# Safe Analytical Database Engine Setup
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
# Robust Clean Configuration Loading
# -----------------------------
@st.cache_data
def load_map():
    df = pd.read_excel(MAP_FILE, header=1)
    df.columns = df.columns.astype(str).str.strip()
    return df

map_df = load_map()

# Strategic Dimensions Matrix Mapping
brand_pillars = {
    "🎯 Professional Career Growth": [1, 2, 3, 15, 17],
    "🛡️ Trust & Brand Affinity": [6, 7, 11, 16],
    "🤝 Community & Engagement": [4, 5, 8, 10],
    "⚡ Content Innovation & Utility": [9, 12, 13, 14]
}

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

@st.cache_data
def load_filters():
    df_temp = con.execute("""
        SELECT DISTINCT Month 
        FROM df 
        WHERE Month IS NOT NULL
    """).df()

    # Convert to list
    months_raw = df_temp["Month"].astype(str).tolist()

    # ✅ Parse full date (handles multiple years correctly)
    temp_df = pd.DataFrame({"Month": months_raw})
    temp_df["parsed"] = pd.to_datetime(temp_df["Month"], errors="coerce")

    # ✅ Sort chronologically (year + month)
    temp_df = temp_df.sort_values("parsed")

    months_list = temp_df["Month"].tolist()

    # Country remains same
    df_country = con.execute("""
        SELECT DISTINCT Country_New 
        FROM df 
        WHERE Country_New IS NOT NULL
    """).df()

    countries_list = df_country["Country_New"].dropna().astype(str).tolist()

    return months_list, countries_list

months, countries = load_filters()
    
# -----------------------------
# Secure Extraction of Brands Map
# -----------------------------
# ✅ Global allowed brands (for "Select All")
GLOBAL_BRANDS = ["LinkedIn", "Indeed", "Google", "TikTok", "twitter", "Facebook"]
brand_rows = map_df[map_df["Variable"].astype(str).str.contains("Aided_Awareness_", na=False)]
brand_map = {}
for _, r in brand_rows.iterrows():
    lbl = str(r["Label"]).split(" - ")[-1].strip()
    match = re.findall(r"\d+", str(r["Variable"]))
    if match:
        brand_map[lbl] = int(match[0])

if not brand_map:
    brand_map = {"Default Brand": 1}

# -----------------------------
# Secure Safe Parameter Builders
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

def get_metric(col, metric_type="top2", where_clause="", weight_col="Global_weight_Stacked"):
    try:
        chk = con.execute(f"SELECT * FROM df LIMIT 0").df()
        if col not in chk.columns:
            return 0.0
            
        if metric_type == "yesno":
            q = f"SELECT {col}, {weight_col} FROM df {where_clause}"
            local_df = con.execute(q).df()
            if local_df.empty: return 0.0
            local_df.columns = ['target_col', 'weight_col']
            yes_mask = local_df['target_col'].astype(str).str.lower().str.strip() == 'yes'
            total_w = local_df['weight_col'].sum()
            return round((local_df.loc[yes_mask, 'weight_col'].sum() * 100.0) / total_w, 1) if total_w > 0 else 0.0
        else:
            q = f"SELECT {col}, {weight_col} FROM df {where_clause}"
            local_df = con.execute(q).df()
            if local_df.empty: return 0.0
            local_df.columns = ['target_col', 'weight_col']
            
            def extract_num(val):
                digits = re.findall(r'\d+', str(val))
                return int(digits[0]) if digits else None
                
            local_df['parsed_val'] = local_df['target_col'].apply(extract_num)
            valid_mask = local_df['parsed_val'].between(1, 5)
            top2_mask = local_df['parsed_val'].isin([4, 5])
            
            denom = local_df.loc[valid_mask, 'weight_col'].sum()
            num = local_df.loc[top2_mask, 'weight_col'].sum()
            return round((num * 100.0) / denom, 1) if denom > 0 else 0.0
    except:
        return 0.0

def get_sparkline_data(col, metric_type, where_clause, weight_col):
    dummy_df = pd.DataFrame({"Month": months, "val": [0.0]*len(months)})
    try:
        chk = con.execute(f"SELECT * FROM df LIMIT 0").df()
        if col not in chk.columns:
            return dummy_df

        q = f"SELECT Month, {col}, {weight_col} FROM df {where_clause}"
        local_df = con.execute(q).df()
        if local_df.empty: return dummy_df
        local_df.columns = ['Month', 'target_col', 'weight_col']
        
        def extract_num(val):
            digits = re.findall(r'\d+', str(val))
            return int(digits[0]) if digits else None

        if metric_type == "yesno":
            local_df['is_match'] = local_df['target_col'].astype(str).str.lower().str.strip() == 'yes'
            agg = local_df.groupby('Month').apply(lambda g: (g.loc[g['is_match'], 'weight_col'].sum() * 100.0) / g['weight_col'].sum() if g['weight_col'].sum() > 0 else 0.0)
        else:
            local_df['parsed_val'] = local_df['target_col'].apply(extract_num)
            local_df['is_valid'] = local_df['parsed_val'].between(1, 5)
            local_df['is_top2'] = local_df['parsed_val'].isin([4, 5])
            agg = local_df.groupby('Month').apply(lambda g: (g.loc[g['is_top2'], 'weight_col'].sum() * 100.0) / g.loc[g['is_valid'], 'weight_col'].sum() if g.loc[g['is_valid'], 'weight_col'].sum() > 0 else 0.0)
            
        res_df = agg.reset_index()
        res_df.columns = ['Month', 'val']
        res_df["Month_order"] = pd.Categorical(res_df["Month"], categories=months, ordered=True)
        return res_df.sort_values("Month_order").fillna(0.0)
    except:
        return dummy_df

def create_sparkline_chart(df, color_line):
    chart = alt.Chart(df).mark_line(interpolate='monotone', strokeWidth=3, color=color_line).encode(
        x=alt.X('Month:O', title=None, axis=None, sort=months),
        y=alt.Y('val:Q', title=None, axis=None, scale=alt.Scale(zero=False))
    ).properties(height=50)
    return chart.configure(background='transparent').configure_view(strokeOpacity=0)

# -----------------------------
# Dynamic Navigation Tab Structure
# -----------------------------
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 Graphs", "🤖 Chatbot"])

# -----------------------------
# TAB 1: EXECUTIVE DASHBOARD
# -----------------------------
with tab1:

    # ---------------- FILTERS ----------------
    with st.container():
     f1, f2, f3, f4 = st.columns(4)

     selected_countries = f1.multiselect("🌍 Country", countries)
     selected_months = f2.multiselect("📅 Month", months)
     segment = f3.selectbox("👤 Segment", ["Total", "Male", "Female"])

    # ✅ Brand filtering logic
     if len(selected_countries) == 0 or len(selected_countries) > 1:
    # ✅ Robust matching (fix Twitter issue + future-proof)
        filtered_brand_map = {
            k: v for k, v in brand_map.items() 
            if any(g.lower() in k.lower() for g in GLOBAL_BRANDS)
    }
     else:
       filtered_brand_map = brand_map


    # Safety fallback
     if not filtered_brand_map:
        filtered_brand_map = brand_map

     selected_brand = f4.selectbox(
        "🏢 Brand",
        list(filtered_brand_map.keys())
    )

     code = filtered_brand_map.get(selected_brand, 1)

     where_clause = build_where(selected_months, selected_countries, segment)
     weight_col = "Weight_Post" if len(selected_countries) == 1 else "Global_weight_Stacked"

     st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

    # ---------------- KPI ----------------
    col1, col2, col3, col4 = st.columns(4)

    val1 = f"{get_metric(f'Aided_Awareness_{code}_slice','yesno',where_clause,weight_col)}%"
    val2 = f"{get_metric(f'Brand_Favorability_{code}_slice','top2',where_clause,weight_col)}%"
    val3 = f"{get_metric(f'Consideration_{code}_slice','top2',where_clause,weight_col)}%"
    val4 = f"{get_metric(f'Consideration_Effect_{code}_slice','top2',where_clause,weight_col)}%"

    with col1:
        st.markdown(f'<div class="kpi-card kpi-pink"><div class="kpi-title">Awareness</div><div class="kpi-value">{val1}</div></div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f'<div class="kpi-card kpi-purple"><div class="kpi-title">Favorability</div><div class="kpi-value">{val2}</div></div>', unsafe_allow_html=True)

    with col3:
        st.markdown(f'<div class="kpi-card kpi-blue"><div class="kpi-title">Consideration</div><div class="kpi-value">{val3}</div></div>', unsafe_allow_html=True)

    with col4:
        st.markdown(f'<div class="kpi-card kpi-orange"><div class="kpi-title">Conversion</div><div class="kpi-value">{val4}</div></div>', unsafe_allow_html=True)

    # ---------------- SPACE ----------------
    st.markdown("<div style='margin-bottom:30px;'></div>", unsafe_allow_html=True)

    # ---------------- DONUT ----------------
    col_left, col_mid, col_right = st.columns([1, 2, 1])

    with col_mid:
        with st.container(border=True):

            st.subheader("🧩 Funnel Composition")

            awareness = get_metric(f"Aided_Awareness_{code}_slice","yesno",where_clause,weight_col)
            favorability = get_metric(f"Brand_Favorability_{code}_slice","top2",where_clause,weight_col)
            consideration = get_metric(f"Consideration_{code}_slice","top2",where_clause,weight_col)
            conversion = get_metric(f"Consideration_Effect_{code}_slice","top2",where_clause,weight_col)

            donut_df = pd.DataFrame({
                "metric": ["Awareness","Favorability","Consideration","Conversion"],
                "value": [awareness,favorability,consideration,conversion]
            })

            donut_chart = alt.Chart(donut_df).mark_arc(innerRadius=75).encode(
                theta=alt.Theta("value:Q"),
                color=alt.Color("metric:N",
                    scale=alt.Scale(range=["#ff4d79","#7c3aed","#0ea5e9","#f59e0b"])
                ),
                tooltip=["metric","value"]
            ).properties(height=340)

            st.altair_chart(
                donut_chart
                .configure_view(strokeOpacity=0, fill="transparent")
                .configure(background='transparent')
                .configure_axis(labelColor="#e5e7eb")
                .configure_legend(labelColor="#e5e7eb"),
                use_container_width=True
            )

    # ---------------- SPACE ----------------
    st.markdown("<div style='margin-bottom:25px;'></div>", unsafe_allow_html=True)

    # ---------------- ATTRIBUTES ----------------
    with st.container(border=True):

        st.markdown("""
        <h3 style='color:#f8fafc;'>🎯 Strategic Pillars</h3>
        <div style='color:#9ca3af;'>Key drivers of brand perception</div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='pillar-label'>Select Strategic Pillar</div>", unsafe_allow_html=True)

        selected_pillar = st.radio(
        "",
        list(brand_pillars.keys()),
        horizontal=True
    )

        active_indices = brand_pillars[selected_pillar]

        attr_data = []
        for idx in active_indices:
            score = get_metric(
                f"Attributes_New_DP_{code}_Q12a_{idx}_slice",
                "top2",
                where_clause,
                weight_col
            )
            if score > 0:
                attr_data.append({
                    "Attribute": attr_map[idx],
                    "Score": score
                })

        df_matrix = pd.DataFrame(attr_data).sort_values("Score", ascending=True)

        max_score = df_matrix["Score"].max()
        df_matrix["Highlight"] = df_matrix["Score"].apply(
            lambda x: "Top" if x == max_score else "Others"
        )

        bars = alt.Chart(df_matrix).mark_bar(
            size=28,
            cornerRadiusEnd=12
        ).encode(
            x=alt.X("Score:Q", axis=None, scale=alt.Scale(domain=[0,100])),
            y=alt.Y("Attribute:N", sort=None,
                    axis=alt.Axis(labelColor="#e5e7eb")),
            color=alt.Color("Highlight:N",
                scale=alt.Scale(
                    domain=["Top","Others"],
                    range=["#ff4d79","#5b5bd6"]
                ),
                legend=None
            )
        )

        text = bars.mark_text(
            align="left",
            baseline="middle",
            dx=6,
            color="#f8fafc"
        ).encode(
            text=alt.Text("Score:Q", format=".1f")
        )

        final_chart = (bars + text).properties(height=280)

        st.altair_chart(
            final_chart
            .configure_view(strokeOpacity=0, fill="transparent")
            .configure(background='transparent')
            .configure_axis(labelColor="#e5e7eb", grid=False),
            use_container_width=True,
            theme = None
        )
# -----------------------------
# TAB 2: GRAPHS VIEW
# -----------------------------
with tab2:
    with st.container():
        colg1, colg2, colg3, colg4 = st.columns(4)
        with colg1:
            g_country = st.multiselect("Filter Country (Trends Visuals)", countries, key="graph_country_input")
        with colg2:
            g_months = st.multiselect("Filter Month (Trends Visuals)", months, key="graph_month_input")
        with colg3:
            g_segment = st.selectbox("Segment Select (Trends Visuals)", ["Total", "Male", "Female"], key="graph_segment_input")
        with colg4:
            g_brand_sel = st.selectbox("Select Target Brand (Trends Visuals)", list(brand_map.keys()), key="graph_brand_input")

    st.markdown("<div style='margin-top: 15px; margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.subheader("📈 Trend Analysis (Time-based)")
        
        graph_where = build_where(g_months, g_country, g_segment)
        g_code = brand_map.get(g_brand_sel, 1)
        
        metrics_to_plot = [
            {"label": "Total Awareness", "col": f"Aided_Awareness_{g_code}_slice", "type": "yesno"},
            {"label": "Brand Favorability", "col": f"Brand_Favorability_{g_code}_slice", "type": "top2"},
            {"label": "Consideration Rate", "col": f"Consideration_{g_code}_slice", "type": "top2"},
            {"label": "Conversion Effect", "col": f"Consideration_Effect_{g_code}_slice", "type": "top2"},
        ]
        
        trend_list = []
        for m_info in metrics_to_plot:
            tdf = get_sparkline_data(m_info["col"], m_info["type"], graph_where, "Global_weight_Stacked")
            tdf["Metric"] = m_info["label"]
            trend_list.append(tdf)
            
        df_trends = pd.concat(trend_list, ignore_index=True)
        
        if not df_trends.empty and df_trends['val'].sum() > 0:
            multi_line_chart = alt.Chart(df_trends).mark_line(point=True, size=3).encode(
                x=alt.X("Month:O", title="Timeline Tracking Phase", sort=months),
                y=alt.Y("val:Q", title="Percentage Share Score (%)", scale=alt.Scale(zero=False)),
                color=alt.Color("Metric:N", legend=alt.Legend(title="Brand Funnel Layer")),
                tooltip=["Month", "Metric", "val"]
            ).properties(height=400).interactive().configure_view(strokeOpacity=0)
            
            st.altair_chart(
    multi_line_chart
    .configure_view(strokeOpacity=0, fill="transparent")
    .configure(background='transparent')
    .configure_axis(
        labelColor="#e5e7eb",
        titleColor="#e5e7eb"
    )
    .configure_legend(
        labelColor="#e5e7eb",
        titleColor="#e5e7eb"
    ),
    use_container_width=True
)
        else:
            st.warning("⚠️ No active dataset parameters match the selected analytical profile configuration metrics.")

# -----------------------------
# TAB 3: CHATBOT VIEW
# -----------------------------
with tab3:
    with st.container(border=True):
        st.subheader("🤖 AI Analytics Chatbot")

        user_query = st.text_input(
            "Interrogate your analytical metrics profile:",
            key="chatbot_query_input",
            placeholder="e.g., linkedin awareness in dec 2025"
        )

        if user_query:

            query = user_query.lower()

            # ✅ Extract month (basic)
            month_match = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s?\d{4}", query)
            month_selected = month_match.group(0).title() if month_match else None

            # ✅ Extract brands present in query
            mentioned_brands = [b.lower() for b in brand_map.keys() if b.lower() in query]

            # ✅ Base filters
            temp_month = [month_selected] if month_selected else []
            where_clause = build_where(temp_month, selected_countries, segment)
            weight_col = "Weight_Post" if len(selected_countries) == 1 else "Global_weight_Stacked"

            
            # --------------------------------------
            # ✅ CASE 2: Brand Comparison
            # --------------------------------------
            if "compare" in query and len(mentioned_brands) == 2:

                b1, b2 = mentioned_brands

                code1 = brand_map.get(next(b for b in brand_map if b.lower() == b1))
                code2 = brand_map.get(next(b for b in brand_map if b.lower() == b2))

                val1 = get_metric(f"Aided_Awareness_{code1}_slice", "yesno", where_clause, weight_col)
                val2 = get_metric(f"Aided_Awareness_{code2}_slice", "yesno", where_clause, weight_col)

                diff = round(val1 - val2, 1)

                st.success(
                    f"📊 In {month_selected}:  \n"
                    f"• {b1.title()}: **{val1}%**  \n"
                    f"• {b2.title()}: **{val2}%**  \n"
                    f"👉 Difference: **{diff}%**"
                )

            # --------------------------------------
            # ✅ CASE 2: Trend (MoM + YoY)
            # --------------------------------------
            elif "trend" in query or "trended" in query:

                if month_selected and len(mentioned_brands) == 1:

                    brand = mentioned_brands[0]
                    code = brand_map.get(next(b for b in brand_map if b.lower() == brand))

                    # current
                    val_curr = get_metric(f"Aided_Awareness_{code}_slice", "yesno", where_clause, weight_col)

                    # previous month
                    idx = months.index(month_selected) if month_selected in months else None

                    if idx and idx > 0:
                        prev_month = months[idx - 1]
                        prev_where = build_where([prev_month], selected_countries, segment)
                        val_prev = get_metric(f"Aided_Awareness_{code}_slice", "yesno", prev_where, weight_col)
                        mom = round(val_curr - val_prev, 1)
                    else:
                        mom = None

                    # YoY (same month last year)
                    try:
                        year = int(month_selected.split()[-1])
                        month_name = month_selected.split()[0]
                        prev_year_month = f"{month_name} {year-1}"

                        if prev_year_month in months:
                            yoy_where = build_where([prev_year_month], selected_countries, segment)
                            val_yoy = get_metric(f"Aided_Awareness_{code}_slice", "yesno", yoy_where, weight_col)
                            yoy = round(val_curr - val_yoy, 1)
                        else:
                            yoy = None
                    except:
                        yoy = None

                    mom_text = f"+{mom}%" if mom and mom > 0 else f"{mom}%"
                    yoy_text = f"+{yoy}%" if yoy and yoy > 0 else f"{yoy}%"

                    trend_comment = ""
                    if mom is not None:
                        trend_comment = "📈 Increasing momentum" if mom > 0 else "📉 Declining trend"

                    st.success(
                        f"📈 {brand.title()} Awareness in {month_selected}: **{val_curr}%**\n\n"
                        f"• MoM Change: **{mom_text}**  \n"
                        f"• YoY Change: **{yoy_text}** \n\n"
                        f"👉 Insight: {trend_comment}"
                    )
            # --------------------------------------
            # ✅ CASE 3: Single Brand Awareness
            # --------------------------------------
            elif "awareness" in query and len(mentioned_brands) == 1:

                brand = mentioned_brands[0]
                code = brand_map.get(next(b for b in brand_map if b.lower() == brand))

                val = get_metric(f"Aided_Awareness_{code}_slice", "yesno", where_clause, weight_col)

                st.success(f"📊 {brand.title()} Awareness in {month_selected}: **{val}%**")

            # --------------------------------------
            # ✅ FALLBACK
            # --------------------------------------
            else:
                st.warning("⚠️ Try queries like:\n- linkedin awareness in dec 2025\n- compare indeed vs linkedin\n- linkedin awareness trend dec 2025")
