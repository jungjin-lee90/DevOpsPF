import streamlit as st

with st.form("ci_cd_form"):
    url = st.text_input("GitHub URL")
    submitted = st.form_submit_button("파이프라인 생성")

if submitted:
    st.success(f"제출됨! URL: {url}")
else:
    st.info("제출되지 않음.")

