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
# CHATBOT HELPERS
 
def find_metric_word(q):
    keywords = ["awareness", "favorability", "favourability", "consideration", "effect"]
    for k in keywords:
        if k in q:
            return "favorability" if k in ["favorability", "favourability"] else k
    match = get_close_matches(q, keywords, n=1, cutoff=0.5)
    if match:
        return "favorability" if match[0] in ["favorability", "favourability"] else match[0]
    return None
 
def find_brand(q):
    found = []
    for b in brand_map.keys():
        if b.lower() in q:
            found.append(b)
    if found:
        return found[:2]  # return up to 2 brands
 
    words = q.split()
    for w in words:
        match = get_close_matches(w, list(brand_map.keys()), n=1, cutoff=0.6)
        if match and match[0] not in found:
            found.append(match[0])
        if len(found) == 2:
            break
    return found
 
def find_attribute(q):
    best_match = None
    best_score = 0
    for i, text in attr_map.items():
        score = len(set(q.split()) & set(text.lower().split()))
        if score > best_score:
            best_score = score
            best_match = i
    return best_match
 
# -----------------------------
# ✅ NEW: Detect intent — compare / trend / single
 
def detect_intent(q):
    compare_keywords = ["compare", "vs", "versus", "against", "difference between", "better", "higher", "lower"]
    trend_keywords = ["trend", "trended", "over time", "mom", "month on month", "month-on-month",
                      "yoy", "year on year", "year-on-year", "monthly", "yearly", "annual", "growth"]
    for k in compare_keywords:
        if k in q:
            return "compare"
    for k in trend_keywords:
        if k in q:
            return "trend"
    return "single"
 
# -----------------------------
# ✅ NEW: Get metric value for a brand (chatbot context, no filters)
 
def get_brand_metric_value(brand, metric):
    code = brand_map[brand]
    if metric == "awareness":
        return get_metric(f"Aided_Awareness_{code}_slice", "yesno")
    col_map = {
        "favorability": "Brand_Favorability",
        "consideration": "Consideration",
        "effect": "Consideration_Effect"
    }
    return get_metric(f"{col_map[metric]}_{code}_slice")
 
# -----------------------------
# ✅ NEW: Brand comparison — returns a formatted text + renders a bar chart
 
def chatbot_compare(brand1, brand2, metric):
    val1 = get_brand_metric_value(brand1, metric)
    val2 = get_brand_metric_value(brand2, metric)
    diff = round(val1 - val2, 1)
 
    leader = brand1 if val1 > val2 else brand2
    gap = abs(diff)
 
    summary = (
        f"**{metric.capitalize()} Comparison**\n\n"
        f"- **{brand1}**: {val1}%\n"
        f"- **{brand2}**: {val2}%\n\n"
        f"➡️ **{leader}** leads by **{gap}%**"
    )
 
    chart_data = pd.DataFrame({
        "Brand": [brand1, brand2],
        "Value": [val1, val2]
    })
 
    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X("Brand:N", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Value:Q", title=f"{metric.capitalize()} (%)"),
        color=alt.Color("Brand:N"),
        tooltip=["Brand", "Value"]
    ).properties(title=f"{metric.capitalize()} — {brand1} vs {brand2}", height=300)
 
    return summary, chart
 
# -----------------------------
# ✅ UPDATED: Trend — MOM (selected month vs prev month) | YOY (selected month vs same month last year)
 
def get_metric_for_month(col, metric_type, month_val):
    """Get metric value for a specific month."""
    where = f"WHERE Month = '{month_val}'"
    return get_metric(col, metric_type, where)
 
def build_metric_col(code, metric):
    """Return (column_name, metric_type) for a brand+metric combo."""
    if metric == "awareness":
        return f"Aided_Awareness_{code}_slice", "yesno"
    col_map = {
        "favorability": "Brand_Favorability",
        "consideration": "Consideration",
        "effect": "Consideration_Effect"
    }
    return f"{col_map[metric]}_{code}_slice", "top2"
 
def find_month_in_query(q):
    """
    Try to find a month mention in the query.
    Supports formats: dec2025, dec 2025, december 2025, 2025-12, Dec-25 etc.
    Returns the matching value from the months list or None.
    """
    month_aliases = {
        "jan": "Jan", "feb": "Feb", "mar": "Mar", "apr": "Apr",
        "may": "May", "jun": "Jun", "jul": "Jul", "aug": "Aug",
        "sep": "Sep", "oct": "Oct", "nov": "Nov", "dec": "Dec",
        "january": "Jan", "february": "Feb", "march": "Mar", "april": "Apr",
        "june": "Jun", "july": "Jul", "august": "Aug", "september": "Sep",
        "october": "Oct", "november": "Nov", "december": "Dec"
    }
 
    # Try matching each known month in the months list directly against query words
    q_clean = q.replace("-", " ").replace("_", " ")
    for m in months:
        if m.lower() in q_clean:
            return m
 
    # Try pattern: "dec 2025", "dec2025", "december 2025"
    pattern = re.search(
        r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        r"[\s\-]?(\d{2,4})",
        q, re.IGNORECASE
    )
    if pattern:
        mon_raw = pattern.group(1).lower()[:3]
        yr_raw  = pattern.group(2)
        yr = "20" + yr_raw if len(yr_raw) == 2 else yr_raw
        short_yr = yr[-2:]  # e.g. "25"
        mon_short = month_aliases.get(mon_raw, mon_raw.capitalize())
 
        # Try common formats against actual months list
        candidates = [
            f"{mon_short}-{short_yr}",          # Dec-25
            f"{mon_short}-{yr}",                 # Dec-2025
            f"{mon_short} {yr}",                 # Dec 2025
            f"{mon_short}{yr}",                  # Dec2025
            f"{yr}-{pattern.group(2).zfill(2)}", # 2025-12
        ]
        for c in candidates:
            if c in months:
                return c
        # fuzzy fallback
        match = get_close_matches(f"{mon_short}-{yr}", months, n=1, cutoff=0.5)
        if match:
            return match[0]
 
    return None
 
def get_prev_month(selected_month):
    """Return the month just before selected_month from the months list, or None."""
    if selected_month in months:
        idx = months.index(selected_month)
        return months[idx - 1] if idx > 0 else None
    return None
 
def get_same_month_last_year(selected_month):
    """
    Return the month from last year that corresponds to selected_month.
    E.g. Dec-25 → Dec-24 / Dec-2024.
    Matches by month name prefix (first 3 chars) and year offset.
    """
    if selected_month not in months:
        return None
 
    # Extract short month name (first 3 alpha chars) from the selected month
    mon_prefix = re.search(r"[A-Za-z]{3}", selected_month)
    if not mon_prefix:
        return None
    mon_short = mon_prefix.group(0)  # e.g. "Dec"
 
    # Extract year digits from selected_month
    yr_match = re.search(r"(\d{2,4})", selected_month)
    if not yr_match:
        return None
    yr_raw = yr_match.group(1)
    yr_full = int("20" + yr_raw) if len(yr_raw) == 2 else int(yr_raw)
    prev_yr_full = yr_full - 1
    prev_yr_short = str(prev_yr_full)[-2:]  # "24"
 
    # Build candidates for same month last year
    candidates = [
        f"{mon_short}-{prev_yr_short}",       # Dec-24
        f"{mon_short}-{prev_yr_full}",         # Dec-2024
        f"{mon_short} {prev_yr_full}",         # Dec 2024
        f"{prev_yr_full}-{str(yr_full).zfill(2)}",  # approximate
    ]
    for c in candidates:
        if c in months:
            return c
 
    # fuzzy fallback
    match = get_close_matches(f"{mon_short}-{prev_yr_full}", months, n=1, cutoff=0.5)
    return match[0] if match else None
 
def format_change(current, compare, label):
    """Return a formatted insight string for current vs compare month."""
    if compare is None:
        return f"  _(no {label} data available)_"
    diff = round(current - compare, 1)
    arrow = "▲" if diff > 0 else ("▼" if diff < 0 else "→")
    sign  = "+" if diff > 0 else ""
    return f"  {arrow} {sign}{diff}% vs {label}"
 
def chatbot_trend(brand, metric, trend_type, selected_month=None):
    """
    MOM : selected_month value vs previous month value
    YOY : selected_month value vs same month last year value
    If no month given, default to the latest month in the list.
    """
    code = brand_map[brand]
    col, mtype = build_metric_col(code, metric)
 
    # Default to latest month if not specified
    ref_month = selected_month if selected_month else months[-1]
 
    current_val = get_metric_for_month(col, mtype, ref_month)
 
    if trend_type == "mom":
        prev_month = get_prev_month(ref_month)
        prev_val   = get_metric_for_month(col, mtype, prev_month) if prev_month else None
        change_str = format_change(current_val, prev_val, prev_month or "previous month")
 
        summary = (
            f"**{brand} — {metric.capitalize()} MOM Insight ({ref_month})**\n\n"
            f"- **{ref_month}**: {current_val}%{change_str}\n"
        )
        if prev_month:
            summary += f"- **{prev_month}**: {prev_val}%\n"
 
        # Bar chart: current vs previous
        chart_rows = [{"Month": ref_month, "Value": current_val}]
        if prev_month and prev_val is not None:
            chart_rows.insert(0, {"Month": prev_month, "Value": prev_val})
 
        chart_df = pd.DataFrame(chart_rows)
        chart_df["Month"] = pd.Categorical(chart_df["Month"], categories=months, ordered=True)
 
        chart = alt.Chart(chart_df).mark_bar().encode(
            x=alt.X("Month:O", axis=alt.Axis(labelAngle=0), sort=None),
            y=alt.Y("Value:Q", title=f"{metric.capitalize()} (%)"),
            color=alt.condition(
                alt.datum.Month == ref_month,
                alt.value("#1f77b4"),
                alt.value("#aec7e8")
            ),
            tooltip=["Month", "Value"]
        ).properties(
            title=f"{brand} {metric.capitalize()} — {ref_month} vs {prev_month or 'Prev Month'}",
            height=300
        )
 
    else:  # YOY
        same_last_yr_month = get_same_month_last_year(ref_month)
        ly_val = get_metric_for_month(col, mtype, same_last_yr_month) if same_last_yr_month else None
        change_str = format_change(current_val, ly_val, same_last_yr_month or "same month last year")
 
        summary = (
            f"**{brand} — {metric.capitalize()} YOY Insight ({ref_month})**\n\n"
            f"- **{ref_month}**: {current_val}%{change_str}\n"
        )
        if same_last_yr_month:
            summary += f"- **{same_last_yr_month}**: {ly_val}%\n"
 
        # Bar chart: current vs same month last year
        chart_rows = [{"Month": ref_month, "Value": current_val}]
        if same_last_yr_month and ly_val is not None:
            chart_rows.insert(0, {"Month": same_last_yr_month, "Value": ly_val})
 
        chart_df = pd.DataFrame(chart_rows)
 
        chart = alt.Chart(chart_df).mark_bar().encode(
            x=alt.X("Month:N", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Value:Q", title=f"{metric.capitalize()} (%)"),
            color=alt.condition(
                alt.datum.Month == ref_month,
                alt.value("#1f77b4"),
                alt.value("#aec7e8")
            ),
            tooltip=["Month", "Value"]
        ).properties(
            title=f"{brand} {metric.capitalize()} — {ref_month} vs {same_last_yr_month or 'Same Month LY'}",
            height=300
        )
 
    return summary, chart
 
# -----------------------------
# ✅ MAIN CHATBOT FUNCTION (original logic intact + new intents added)
 
def local_chatbot(query):
    q = query.lower()
 
    intent = detect_intent(q)
    metric = find_metric_word(q)
    brand_match = find_brand(q)
 
    # ── COMPARE INTENT ──────────────────────────────────────────────
    if intent == "compare":
        if len(brand_match) < 2:
            return "Please mention **two brand names** to compare. E.g. _'Compare LinkedIn vs Indeed favorability'_", None
        if not metric:
            return "Please mention a metric to compare — awareness, favorability, consideration, or effect.", None
 
        summary, chart = chatbot_compare(brand_match[0], brand_match[1], metric)
        return summary, chart
 
    # ── TREND INTENT ────────────────────────────────────────────────
    if intent == "trend":
        if not brand_match:
            return "Please mention a brand for the trend. E.g. _'LinkedIn awareness MOM trend'_", None
        if not metric:
            return "Please mention a metric — awareness, favorability, consideration, or effect.", None
 
        trend_type = "yoy" if any(k in q for k in ["yoy", "year on year", "year-on-year", "yearly", "annual"]) else "mom"
        summary, chart = chatbot_trend(brand_match[0], metric, trend_type)
        return summary, chart
 
    # ── ORIGINAL SINGLE BRAND LOGIC (unchanged) ─────────────────────
    if not brand_match:
        return "Please mention a valid brand.", None
 
    brand = brand_match[0]
    code = brand_map[brand]
 
    if not metric:
        attr_id = find_attribute(q)
        if attr_id:
            val = get_metric(f"Attributes_New_DP_{code}_Q12a_{attr_id}_slice")
            return f"{brand} attribute \"{attr_map[attr_id]}\" is {val}%", None
        return "Ask about awareness, favorability, consideration, effect or attributes.", None
 
    if metric == "awareness":
        val = get_metric(f"Aided_Awareness_{code}_slice", "yesno")
    else:
        col_map = {
            "favorability": "Brand_Favorability",
            "consideration": "Consideration",
            "effect": "Consideration_Effect"
        }
        val = get_metric(f"{col_map[metric]}_{code}_slice")
 
    return f"{brand} {metric} is {val}%", None
 
# -----------------------------
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 Graphs", "🤖 Chatbot"])
 
# -----------------------------
with tab1:
    colf1, colf2, colf3, colf4 = st.columns(4)
 
    selected_countries = colf1.multiselect("Country", countries)
    selected_months = colf2.multiselect("Month", months)
    segment = colf3.selectbox("Segment", ["Total", "Male", "Female"])
 
    filtered_brand_map = get_brands_by_country(selected_countries)
    selected_brand = colf4.selectbox("Brand", list(filtered_brand_map.keys()))
 
    code = filtered_brand_map[selected_brand]
 
    where_clause = build_where(selected_months, selected_countries, segment)
    weight_col = "Weight_Post" if len(selected_countries) == 1 else "Global_weight_Stacked"
 
    col1, col2, col3, col4 = st.columns(4)
 
    col1.metric("Awareness", f"{get_metric(f'Aided_Awareness_{code}_slice', 'yesno', where_clause, weight_col)}%")
    col2.metric("Favorability", f"{get_metric(f'Brand_Favorability_{code}_slice', 'top2', where_clause, weight_col)}%")
    col3.metric("Consideration", f"{get_metric(f'Consideration_{code}_slice', 'top2', where_clause, weight_col)}%")
    col4.metric("Effect", f"{get_metric(f'Consideration_Effect_{code}_slice', 'top2', where_clause, weight_col)}%")
 
    st.subheader("Brand Attributes")
 
    attr_data = [
        {"Attribute": attr_map[i], "Value (%)": get_metric(f"Attributes_New_DP_{code}_Q12a_{i}_slice", "top2", where_clause, weight_col)}
        for i in range(1, 18)
    ]
    st.dataframe(pd.DataFrame(attr_data), use_container_width=True)
 
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
    df_chart["Month_order"] = pd.Categorical(df_chart["Month"], categories=months, ordered=True)
 
    if view_type == "Trended View":
        chart = alt.Chart(df_chart).mark_line(point=True).encode(
            x="Month_order:O",
            y="Value:Q",
            color="Brand"
        )
    else:
        chart = alt.Chart(df_chart).mark_line(point=True).encode(
            x="Brand",
            y="Value:Q",
            color="Month"
        )
 
    st.altair_chart(chart, use_container_width=True)
 
# -----------------------------
with tab3:
    st.subheader("🤖 Ask KPI Questions")
 
    # ── Usage hints ─────────────────────────────────────────────────
    with st.expander("💡 What can you ask?", expanded=False):
        st.markdown("""
        **Single Brand KPI**
        > _"LinkedIn awareness"_
        > _"Indeed favorability"_
        > _"Glassdoor consideration"_
 
        **Attribute**
        > _"LinkedIn helps me find the right job"_
 
        **Brand Comparison**
        > _"Compare LinkedIn vs Indeed on favorability"_
        > _"LinkedIn vs Glassdoor awareness"_
 
        **MOM Trend**
        > _"LinkedIn awareness MOM trend"_
        > _"Show Indeed favorability month on month"_
 
        **YOY Trend**
        > _"LinkedIn consideration YOY"_
        > _"Glassdoor awareness year on year"_
        """)
 
    # ── Chat history ─────────────────────────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
 
    user_query = st.text_input("Ask about KPIs", placeholder="e.g. Compare LinkedIn vs Indeed favorability")
 
    if user_query:
        response_text, response_chart = local_chatbot(user_query)
 
        # Store in history (text only)
        st.session_state.chat_history.append({
            "question": user_query,
            "answer": response_text
        })
 
        # Show latest response
        st.markdown(response_text)
        if response_chart is not None:
            st.altair_chart(response_chart, use_container_width=True)
 
    # ── Conversation history ─────────────────────────────────────────
    if st.session_state.chat_history:
        st.divider()
        st.markdown("#### 🕘 Previous Questions")
        for item in reversed(st.session_state.chat_history[:-1]):
            with st.expander(f"Q: {item['question']}"):
                st.markdown(item["answer"])
