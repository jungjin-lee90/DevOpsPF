import streamlit as st
import json
from components.experiment_card import show_experiment
from jenkins import generate_jenkinsfile, create_jenkins_job_with_trigger, register_github_webhook, create_jenkins_job_with_multiple_branches, push_jenkinsfile_to_github
from datetime import datetime
from components.aws import run_aws_command

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
        branch_input = st.text_input("🧵 브랜치 목록 (쉼표로 구분)", value="main,develop,release/*")
        branches = [b.strip() for b in branch_input.split(",") if b.strip()]
        build_type = st.selectbox("⚙️ 빌드 방식 선택", ["Docker", "Maven", "NPM", "Gradle"])
        image_name = st.text_input("🐳 Docker 이미지 이름(Account ID 포함) (ECR repo/tag)", placeholder="my-ecr-repo:latest")
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
            st.session_state.branches = branches
            st.session_state.build_type = build_type
            st.session_state.image_name = image_name
            st.session_state.deploy_target = deploy_target
            st.session_state.step = 3
            st.rerun()
    elif back_clicked:
        st.session_state.step = 1
        st.rerun()
elif st.session_state.step == 3:
    st.title("🧙‍♂️ 3단계: AWS 설정 (ECR/EKS)")

    with st.form("aws_form"):
        aws_access_key = st.text_input("🔐 AWS Access Key ID", type="default")
        aws_secret_key = st.text_input("🕵️ AWS Secret Access Key", type="password")
        aws_region = st.text_input("🌍 AWS Region", value="ap-northeast-2")
        cluster_name = st.text_input("☸️ EKS 클러스터 이름", placeholder="devops-cluster")
        ecr_repo = st.text_input("📦 ECR Repo 주소", placeholder="000000000000.dkr.ecr.ap-northeast-2.amazonaws.com/my-repo")

        col1, col2, col3 = st.columns([2, 2, 12])
        with col1:
            back_clicked = st.form_submit_button("← 이전 단계")
        with col2:
            next_clicked = st.form_submit_button("다음 단계로 →")

    if next_clicked:
        with st.status("🔐 AWS 설정 저장 중..."):
            st.session_state.aws_access_key = aws_access_key
            st.session_state.aws_secret_key = aws_secret_key
            st.session_state.aws_region = aws_region
            st.session_state.cluster_name = cluster_name
            st.session_state.ecr_repo = ecr_repo
            st.session_state.step = 4
            st.rerun()
    elif back_clicked:
        st.session_state.step = 2
        st.rerun()

elif st.session_state.step == 4:
    st.title("🧙‍♂️ 3단계: Jenkinsfile 미리보기 및 다운로드")

    if not st.session_state.image_name.strip():
        with st.spinner("🔧 ECR 생성 중..."):
            # account ID 추출
            ecr_domain = f"{st.session_state.aws_access_key}.dkr.ecr.{st.session_state.aws_region}.amazonaws.com"
            repo_name = "streamlit-auto"
            ecr_full = f"{ecr_domain}/{repo_name}"

            # ECR 리포 자동 생성 시도
            create_cmd = f"aws ecr create-repository --repository-name {repo_name}"
            stdout, stderr = run_aws_command(
                st.session_state.aws_access_key,
                st.session_state.aws_secret_key,
                st.session_state.aws_region,
                create_cmd
            )
            # 생성 결과 저장 및 자동 등록
            st.session_state.image_name = ecr_full
            st.session_state["ecr_create_log"] = stdout or stderr
            st.subheader("📦 ECR 생성 결과")
            st.code(st.session_state.get("ecr_create_log", "결과 없음"), language="text")

    with st.spinner("🔧 Jenkinsfile 생성 중..."):
        jenkinsfile = generate_jenkinsfile(
            st.session_state.github_url,
            st.session_state.branches,
            st.session_state.image_name,
            st.session_state.deploy_target,
            use_helm=True,
            helm_chart_path="./helm-chart",
            helm_release_name="DevOpsPF",
            helm_namespace="default"
        )

    with st.spinner("🔧 Jenkinsfile push 중..."):
        push_jenkinsfile_to_github(st.session_state.github_url, st.session_state.github_pat, st.session_state.branches, jenkinsfile)

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
            st.session_state.step = 3
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
                st.session_state.branches,
                st.session_state.build_type,
#                st.session_state.image_name,
#                st.session_state.deploy_target
            ]
            missing_fields = []
            labels = [
                ("Jenkins 서버 주소", st.session_state.jenkins_url),
                ("Jenkins 사용자명", st.session_state.jenkins_user),
                ("Jenkins API Token", st.session_state.jenkins_token),
                ("Jenkins Job 이름", st.session_state.job_name),
                ("GitHub Repository URL", st.session_state.github_url),
                ("GitHub PAT", st.session_state.github_pat),
                ("브랜치 이름", st.session_state.branches),
                ("빌드 방식", st.session_state.build_type),
                #("Docker 이미지 이름", st.session_state.image_name),
                #("배포 대상", st.session_state.deploy_target)
            ]
            for label, value in labels:
                if not str(value).strip():
                    missing_fields.append(label)

            if missing_fields:
                st.error("❌ 다음 항목이 비어 있습니다: " + ", ".join(missing_fields))
            else:
                with st.status("🚀 Jenkins Job 생성 중입니다...", expanded=True) as status:
                    status.update(label="🔧 Jenkinsfile 기반으로 Job 생성 중...")

                    status_code, result = create_jenkins_job_with_multiple_branches(
                        st.session_state.jenkins_url,
                        st.session_state.jenkins_user,
                        st.session_state.jenkins_token,
                        st.session_state.job_name,
                        jenkinsfile,
                        st.session_state.github_url,
                        st.session_state.branches
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
                            st.session_state.step = 5
                            st.rerun()
                        else:
                            status.update(label="⚠️ Webhook 등록 실패", state="error")
                            st.error(f"Webhook 등록 실패: {webhook_result}")
                    else:
                        status.update(label="❌ Jenkins Job 생성 실패", state="error")
                        st.error(f"Job 생성 실패: {status_code}\n{result}")

elif st.session_state.step == 5:
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
    
elif st.session_state.step == 6:
    st.title("🧙‍♂️ 5단계: Docker 이미지 ECR에 배포하기")

    # ✅ 자동 ECR 생성 시도
    if "ecr_create_result" not in st.session_state:
        ecr_repo_name = st.session_state.ecr_repo.split("/")[-1]
        create_ecr_command = f"aws ecr create-repository --repository-name {ecr_repo_name}"
        stdout, stderr = run_aws_command(
            st.session_state.aws_access_key,
            st.session_state.aws_secret_key,
            st.session_state.aws_region,
            create_ecr_command
        )
        st.session_state["ecr_create_result"] = stdout if stdout else stderr

    st.subheader("📦 ECR 리포지토리 생성 결과")
    st.code(st.session_state["ecr_create_result"], language="json")

    # ✅ ECR에 Docker 이미지 자동 푸시
    if "ecr_push_result" not in st.session_state:
        with st.spinner("🐳 Docker 이미지 ECR에 푸시 중..."):
            import time

            # ECR 도메인만 추출
            ecr_domain = st.session_state.ecr_repo.split("/")[0]
            tag = "latest"  # 또는 datetime.now().strftime('%Y%m%d%H%M%S')
            image_full = f"{st.session_state.ecr_repo}:{tag}"

            # 1단계: ECR 로그인
            login_cmd = f"aws ecr get-login-password --region {st.session_state.aws_region} | docker login --username AWS --password-stdin {ecr_domain}"
            _, login_err = run_aws_command(
                st.session_state.aws_access_key,
                st.session_state.aws_secret_key,
                st.session_state.aws_region,
                login_cmd
            )

            if login_err:
                st.session_state["ecr_push_result"] = f"[로그인 실패]\n{login_err}"
            else:
                # 2단계: Docker Build
                build_cmd = f"docker build -t {image_full} ."
                build_out, build_err = run_aws_command(
                    st.session_state.aws_access_key,
                    st.session_state.aws_secret_key,
                    st.session_state.aws_region,
                    build_cmd
                )

                # 3단계: Docker Push
                push_cmd = f"docker push {image_full}"
                push_out, push_err = run_aws_command(
                    st.session_state.aws_access_key,
                    st.session_state.aws_secret_key,
                    st.session_state.aws_region,
                    push_cmd
                )

                # 결과 저장
                st.session_state["ecr_push_result"] = build_out + "\n" + push_out if not (build_err or push_err) else f"[에러]\n{build_err}\n{push_err}"

                st.subheader("🐳 Docker 이미지 푸시 결과")
                st.code(st.session_state["ecr_push_result"], language="text")

    if st.button("다음 단계로 →"):
        st.session_state.step = 7
        st.rerun()

elif st.session_state.step == 7:
    st.title("🧙‍♂️ 6단계: EKS 클러스터에 Helm 배포")

    with st.status("🚀 Helm 배포 준비 중..."):
        cluster_name = st.session_state.cluster_name
        region = st.session_state.aws_region
        helm_release = "devops-app"
        namespace = "default"
        ecr_repo = st.session_state.ecr_repo
        image_tag = "latest"
        chart_path = "./helm-chart"

        # kubeconfig 설정
        update_cmd = f"aws eks update-kubeconfig --name {cluster_name} --region {region}"
        out1, err1 = run_aws_command(
            st.session_state.aws_access_key,
            st.session_state.aws_secret_key,
            region,
            update_cmd
        )

        # helm upgrade --install
        helm_cmd = f"""
        helm upgrade --install {helm_release} {chart_path} \
          --set image.repository={ecr_repo} \
          --set image.tag={image_tag} \
          --namespace {namespace} \
          --create-namespace
        """
        out2, err2 = run_aws_command(
            st.session_state.aws_access_key,
            st.session_state.aws_secret_key,
            region,
            helm_cmd
        )

        if err1 or err2:
            st.error("❌ 배포 실패")
            st.code(err1 + "\n" + err2, language="text")
        else:
            st.success("✅ Helm 배포 성공!")
            st.code(out2, language="text")

    if st.button("🏁 처음으로 돌아가기"):
        st.session_state.step = 1
        st.session_state.create_ci = False
        st.rerun()


else:
    selected_exp = next(e for e in experiments if e["title"] == selected)
    st.title(f"🧪 {selected_exp['title']}")
    show_experiment(selected_exp)
