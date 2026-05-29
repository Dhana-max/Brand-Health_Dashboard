import streamlit as st

st.set_page_config(layout="wide")

# ✅ TEST CSS
st.markdown("""
<style>

.test-card {
    background: white;
    padding: 30px;
    border-radius: 15px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}

.test-title {
    font-size: 20px;
    color: blue;
    font-weight: 700;
}

</style>
""", unsafe_allow_html=True)

# ✅ TEST HTML
st.markdown("""
<div class="test-card">
    <div class="test-title">✅ CSS WORKING</div>
    <p>If this box has shadow & rounded corners → CSS is working</p>
</div>
""", unsafe_allow_html=True)
