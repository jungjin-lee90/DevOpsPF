import streamlit as st
import json
from components.experiment_card import show_experiment
from jenkins import generate_jenkinsfile, create_jenkins_job_with_trigger, register_github_webhook
from datetime import datetime

# 데이터 로딩
try:
    with open("data/experiments.json", "r") as f:
        experiments = json.load(f)
except Exception as e:
    st.error(f"❌ 데이터 로딩 실패: {e}")
    st.stop()

st.set_page_config(layout="wide")

# 스타일 커스터마이징
st.markdown("""
<style>
.block-container {
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 65% !important;
}
.element-container pre {
    white-space: pre-wrap !important;
    word-break: break-word !important;
}
.stCodeBlock, .stMarkdown {
    font-size: 14px;
    max-width: 100% !important;
    overflow-x: auto;
}
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "step" not in st.session_state:
    st.session_state.step = 1
if "create_ci" not in st.session_state:
    st.session_state.create_ci = False

# 사이드바
st.sidebar.title("📌 DevOps 포트폴리오")
if st.sidebar.button("🚀 CI/CD 구축하기"):
    st.session_state.step = 1
    st.session_state.create_ci = True

st.sidebar.markdown("---")
titles = [e["title"] for e in experiments]
selected = st.sidebar.selectbox("이전 프로젝트 회고록", titles, key="exp_selectbox")

# 본문
if st.session_state.step == 1:
    st.title("🧙‍♂️ 1단계: Jenkins 연결 정보 입력")

    with st.form("jenkins_form"):
        jenkins_url = st.text_input("🖥️ Jenkins 서버 주소", placeholder="http://localhost:8080")
        if any(ip in jenkins_url for ip in ["127.0.0.1", "localhost", "192.168."]):
            st.warning("⚠️ GitHub Webhook을 사용하려면 Jenkins URL은 외부에서 접근 가능한 주소여야 합니다.")
        jenkins_user = st.text_input("👤 Jenkins 사용자명")
        jenkins_token = st.text_input("🔑 Jenkins API Token", type="password")
        job_name = st.text_input("📝 생성할 Jenkins Job 이름", placeholder="my-cicd-job")
        submitted = st.form_submit_button("다음 단계로 →")

    if submitted:
        st.session_state.jenkins_url = jenkins_url
        st.session_state.jenkins_user = jenkins_user
        st.session_state.jenkins_token = jenkins_token
        st.session_state.job_name = job_name
        st.session_state.step = 2
        st.rerun()

elif st.session_state.step == 2:
    st.title("🧙‍♂️ 2단계: GitHub 및 배포 정보 입력")

    with st.form("github_form"):
        github_url = st.text_input("🔗 GitHub Repository URL", placeholder="https://github.com/user/repo")
        github_pat = st.text_input("🔑 GitHub Personal Access Token", type="password")
        branch = st.text_input("🌿 브랜치 이름", value="main")
        build_type = st.selectbox("⚙️ 빌드 방식 선택", ["Docker", "Maven", "NPM", "Gradle"])
        image_name = st.text_input("🐳 Docker 이미지 이름 (ECR repo/tag)", placeholder="my-ecr-repo:latest")
        deploy_target = st.text_input("🎯 배포 대상 (EKS namespace/deployment 이름 등)")

        col1, col2, col3 = st.columns([2, 2, 12])
        with col1:
            back_clicked = st.form_submit_button("← 이전 단계")
        with col2:
            next_clicked = st.form_submit_button("다음 단계로 →")

    if next_clicked:
        with st.status("📦 Jenkinsfile 생성 중입니다..."):
            st.session_state.github_url = github_url
            st.session_state.github_pat = github_pat
            st.session_state.branch = branch
            st.session_state.build_type = build_type
            st.session_state.image_name = image_name
            st.session_state.deploy_target = deploy_target
            st.session_state.step = 3
            st.rerun()
    elif back_clicked:
        st.session_state.step = 1
        st.rerun()

elif st.session_state.step == 3:
    st.title("🧙‍♂️ 3단계: Jenkinsfile 미리보기 및 다운로드")
    with st.spinner("🔧 Jenkinsfile 생성 중..."):
        jenkinsfile = generate_jenkinsfile(
            st.session_state.github_url,
            st.session_state.branch,
            st.session_state.image_name,
            st.session_state.deploy_target
        )

    st.subheader("🔧 생성된 Jenkinsfile")
    st.code(jenkinsfile, language="groovy")

    st.download_button(
        label="📄 Jenkinsfile 다운로드",
        data=jenkinsfile,
        file_name="generated_Jenkinsfile",
        mime="text/plain"
    )

    col1, col2, col3 = st.columns([2, 4, 12])
    with col1:
        if st.button("← 이전 단계"):
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("Jenkins에 Job 생성하기 →"):
            required_fields = [
                st.session_state.jenkins_url,
                st.session_state.jenkins_user,
                st.session_state.jenkins_token,
                st.session_state.job_name,
                st.session_state.github_url,
                st.session_state.github_pat,
                st.session_state.branch,
                st.session_state.build_type,
#                st.session_state.image_name,
#                st.session_state.deploy_target
            ]
            if any(not field.strip() for field in required_fields):
                st.error("❌ 입력 항목을 채워주세요. 빈 값이 있습니다.")
            else:
                with st.status("🚀 Jenkins Job 생성 중입니다...", expanded=True) as status:
                    status.update(label="🔧 Jenkinsfile 기반으로 Job 생성 중...")

                    status_code, result = create_jenkins_job_with_trigger(
                        st.session_state.jenkins_url,
                        st.session_state.jenkins_user,
                        st.session_state.jenkins_token,
                        st.session_state.job_name,
                        jenkinsfile
                    )
                    st.session_state["job_create_result"] = f"Status: {status_code}{result}"

                    if status_code == 200:
                        status.update(label="🔔 GitHub Webhook 등록 중...")

                        ok, webhook_result = register_github_webhook(
                            st.session_state.github_url,
                            st.session_state.github_pat,
                            st.session_state.jenkins_url
                        )
                        st.session_state["webhook_result"] = webhook_result

                        if ok:
                            status.update(label="✅ Jenkins Job 및 Webhook 등록 완료!", state="complete")
                            st.success("모든 작업이 완료되었습니다!")
                            st.session_state.step = 4
                            st.rerun()
                        else:
                            status.update(label="⚠️ Webhook 등록 실패", state="error")
                            st.error(f"Webhook 등록 실패: {webhook_result}")
                    else:
                        status.update(label="❌ Jenkins Job 생성 실패", state="error")
                        st.error(f"Job 생성 실패: {status_code}\n{result}")

elif st.session_state.step == 4:
    st.title("🧙‍♂️ 4단계: Jenkins 연동 결과 확인")

    st.subheader("📦 Job 생성 결과")
    st.code(st.session_state.get("job_create_result", "결과 없음"), language="text")

    st.subheader("🔗 GitHub Webhook 설정 결과")
    st.code(st.session_state.get("webhook_result", "결과 없음"), language="json")

    st.markdown("[🔗 Jenkins 열기](%s)" % st.session_state.jenkins_url)

    if st.button("🏁 처음으로 돌아가기"):
        st.session_state.step = 1
        st.session_state.create_ci = False
        st.rerun()

else:
    selected_exp = next(e for e in experiments if e["title"] == selected)
    st.title(f"🧪 {selected_exp['title']}")
    show_experiment(selected_exp)
