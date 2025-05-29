import streamlit as st
import os
import requests

def convert_raw_to_blob_url(raw_url: str) -> str:
    """
    Convert GitHub raw URL to blob (HTML) URL.
    """
    if "raw.githubusercontent.com" not in raw_url:
        return raw_url  # fallback

    parts = raw_url.replace("https://raw.githubusercontent.com/", "").split("/")
    if len(parts) < 4:
        return raw_url  # fallback

    user, repo, branch, *path = parts
    blob_url = f"https://github.com/{user}/{repo}/blob/{branch}/{'/'.join(path)}"
    return blob_url

def show_experiment(exp):
    st.markdown(f"**날짜**: {exp['date']}")
    st.markdown(f"**요약**: {exp['summary']}")

    # 🔧 주요 코드 (파일 경로 기반으로 불러오기)
    if exp.get("code_path"):
        st.markdown("### 🔧 주요 코드")
        # 파일명 추출
        filename = exp["code_path"].split("/")[-1]
        path_display = exp["code_path"]
        # GitHub 원본 링크로 변환
        if path_display.startswith("http") and "raw.githubusercontent.com" in path_display:
            blob_url = convert_raw_to_blob_url(path_display)
            st.markdown(
                f"<small>📎 코드 파일: <a href='{blob_url}' target='_blank'><code>{filename}</code></a></small>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<small>📎 코드 파일: <code>{filename}</code> ({path_display})</small>",
                unsafe_allow_html=True
            )

        code = ""
        if exp["code_path"].startswith("http"):
            # GitHub raw 링크로부터 코드 읽기
            try:
                res = requests.get(exp["code_path"])
                res.raise_for_status()
                code = res.text
            except Exception as e:
                st.error(f"코드를 불러오지 못했습니다: {e}")
        elif os.path.exists(exp["code_path"]):
            # 로컬 경로일 경우
            with open(exp["code_path"], "r") as f:
                code = f.read()
        else:
            st.warning("코드 파일을 찾을 수 없습니다.")

        # 언어 추정 (간단히 확장자 기반)
        if exp["code_path"].endswith(".py"):
            lang = "python"
        elif exp["code_path"].endswith(".yaml") or exp["code_path"].endswith(".yml"):
            lang = "yaml"
        elif exp["code_path"].endswith(".groovy"):
            lang = "groovy"
        else:
            lang = "text"

        if code:
            st.markdown(
                f"""```{lang}
    {code}
    ```""",
                unsafe_allow_html=True
            )

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
