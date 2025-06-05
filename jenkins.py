from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth

def generate_jenkinsfile(github_url, branch, image_name, deploy_target):
    image_tag = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"""pipeline {{
    agent any

    environment {{
        AWS_REGION = 'ap-northeast-2'
        ECR_REPO = '{image_name}'
        IMAGE_TAG = '{image_tag}'
    }}

    stages {{
        stage('Checkout') {{
            steps {{
                git branch: '{branch}', url: '{github_url}'
            }}
        }}

        stage('Build Docker Image') {{
            steps {{
                sh 'docker build -t ${{ECR_REPO}}:${{IMAGE_TAG}} .'
            }}
        }}

        stage('Push to ECR') {{
            steps {{
                sh '''
                aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO
                docker push $ECR_REPO:$IMAGE_TAG
                '''
            }}
        }}

        stage('Deploy to EKS') {{
            steps {{
                sh '''
                aws eks update-kubeconfig --name devops-cluster --region $AWS_REGION
                kubectl set image deployment/{deploy_target} app-container=$ECR_REPO:$IMAGE_TAG
                '''
            }}
        }}
    }}
}}"""

def create_jenkins_job(jenkins_url, jenkins_user, jenkins_token, job_name, jenkinsfile):
    # Jenkinsfile을 XML에 삽입
    job_config_xml = f"""<?xml version='1.0' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <description>{job_name} 자동 생성됨</description>
  <keepDependencies>false</keepDependencies>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
    <script>{jenkinsfile}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
</flow-definition>
"""
    url = f"{jenkins_url}/createItem?name={job_name}"
    headers = {"Content-Type": "application/xml"}
    auth = HTTPBasicAuth(jenkins_user, jenkins_token)

    response = requests.post(
        url,
        headers=headers,
        data=job_config_xml.encode('utf-8'),
        auth=auth
    )

    return response.status_code, response.text

def create_jenkins_job_with_trigger(jenkins_url, jenkins_user, jenkins_token, job_name, jenkinsfile, github_url, branch):
    job_config_xml = f"""<?xml version='1.0' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <description>{job_name} 자동 생성됨</description>
  <keepDependencies>false</keepDependencies>

  <properties>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers>
        <com.cloudbees.jenkins.GitHubPushTrigger plugin="github">
          <spec></spec>
        </com.cloudbees.jenkins.GitHubPushTrigger>
      </triggers>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>

  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition" plugin="workflow-cps">
    <scm class="hudson.plugins.git.GitSCM" plugin="git">
      <configVersion>2</configVersion>
      <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
          <url>{github_url}</url>
        </hudson.plugins.git.UserRemoteConfig>
      </userRemoteConfigs>
      <branches>
        <hudson.plugins.git.BranchSpec>
          <name>*/{branch}</name>
        </hudson.plugins.git.BranchSpec>
      </branches>
      <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
      <submoduleCfg class="empty-list"/>
      <extensions/>
    </scm>
    <scriptPath>Jenkinsfile</scriptPath>
    <lightweight>true</lightweight>
  </definition>

  <disabled>false</disabled>
</flow-definition>
"""

    url = f"{jenkins_url}/createItem?name={job_name}"
    headers = {"Content-Type": "application/xml"}
    auth = HTTPBasicAuth(jenkins_user, jenkins_token)

    response = requests.post(
        url,
        headers=headers,
        data=job_config_xml.encode("utf-8"),
        auth=auth
    )

    return response.status_code, response.text


def register_github_webhook(github_url, github_pat, jenkins_url):
    import re
    match = re.match(r"https://github.com/(.+)/(.+)", github_url)
    if not match:
        return False, "GitHub URL이 올바르지 않습니다."

    owner, repo = match.groups()
    api_url = f"https://api.github.com/repos/{owner}/{repo}/hooks"
    headers = {
        "Authorization": f"Bearer {github_pat}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": "web",
        "active": True,
        "events": ["push"],
        "config": {
            "url": f"{jenkins_url}/github-webhook/",
            "content_type": "json"
        }
    }
    res = requests.post(api_url, json=data, headers=headers)
    return res.status_code in [201, 422], res.json()

def create_jenkins_job_with_multiple_branches(
    jenkins_url, jenkins_user, jenkins_token,
    job_name, github_url, branches,  # 🔁 branches = ['main', 'develop', 'release/*']
):
    branch_specs = "\n".join([
        f"""<hudson.plugins.git.BranchSpec><name>*/{b}</name></hudson.plugins.git.BranchSpec>"""
        for b in branches
    ])

    job_config_xml = f"""<?xml version='1.0' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <description>{job_name} 자동 생성됨</description>
  <keepDependencies>false</keepDependencies>

  <properties>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers>
        <com.cloudbees.jenkins.GitHubPushTrigger plugin="github">
          <spec></spec>
        </com.cloudbees.jenkins.GitHubPushTrigger>
      </triggers>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>

  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition" plugin="workflow-cps">
    <scm class="hudson.plugins.git.GitSCM" plugin="git">
      <configVersion>2</configVersion>
      <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
          <url>{github_url}</url>
        </hudson.plugins.git.UserRemoteConfig>
      </userRemoteConfigs>
      <branches>
        {branch_specs}
      </branches>
      <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
      <submoduleCfg class="empty-list"/>
      <extensions/>
    </scm>
    <scriptPath>Jenkinsfile</scriptPath>
    <lightweight>true</lightweight>
  </definition>

  <disabled>false</disabled>
</flow-definition>
"""

    import requests
    from requests.auth import HTTPBasicAuth
    headers = {"Content-Type": "application/xml"}
    url = f"{jenkins_url}/createItem?name={job_name}"
    res = requests.post(url, headers=headers, data=job_config_xml.encode("utf-8"), auth=HTTPBasicAuth(jenkins_user, jenkins_token))
    return res.status_code, res.text



