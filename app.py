import streamlit as st
import json
from components.experiment_card import show_experiment

# 데이터 로딩
try:
    with open("data/experiments.json", "r") as f:
        experiments = json.load(f)
except Exception as e:
    st.error(f"❌ 데이터 로딩 실패: {e}")
    st.stop()


st.sidebar.title("📌 DevOps 프로젝트 목록")
titles = [e["title"] for e in experiments]
selected = st.sidebar.selectbox("프로젝트를 선택하세요", titles)

# 선택한 실험 데이터 가져오기
selected_exp = next(e for e in experiments if e["title"] == selected)

# 본문 영역 표시
st.title(f"🧪 {selected_exp['title']}")
show_experiment(selected_exp)
