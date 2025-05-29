import streamlit as st
import os

def show_experiment(exp):
    st.markdown(f"**날짜**: {exp['date']}")
    st.markdown(f"**요약**: {exp['summary']}")

    # 🔧 주요 코드 (파일 경로 기반으로 불러오기)
    if exp.get("code_path") and os.path.exists(exp["code_path"]):
        st.markdown("### 🔧 주요 코드")
        with open(exp["code_path"], "r") as f:
            code = f.read()
        # 파일 확장자에 따라 언어 자동 추정
        lang = "groovy" if exp["code_path"].endswith(".groovy") else "yaml"
        st.code(code, language=lang)
    else:
        st.warning("코드 파일을 찾을 수 없습니다.")

    # 🗂️ 구성도
    if exp.get("image"):
        st.markdown("### 🗂️ 구성도")
        try:
            st.image(f"data/images/{exp['image']}", use_container_width=True)
        except:
            st.warning("이미지를 불러올 수 없습니다.")

    # ✅ 결과 요약
    if exp.get("result"):
        st.markdown("### ✅ 결과")
        st.info(exp["result"])
        if exp.get("resultimage"):
            try:
                st.image(f"data/images/{exp['resultimage']}", use_container_width=True)
            except:
                st.warning("이미지를 불러올 수 없습니다.")

    # 📓 회고
    if exp.get("reflection"):
        st.markdown("### 📓 실험 회고")
        st.info(exp["reflection"])
