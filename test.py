import requests
from requests.auth import HTTPBasicAuth

jenkins_url = "http://localhost:8080"
job_name = "test-freestyle"
user = "jungjinlee"
token = "11069e8b017773cb2ac4bb1e1d60f2e93f"

job_config_xml = """<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description>Freestyle 테스트 Job</description>
  <keepDependencies>false</keepDependencies>

  <triggers>
    <com.cloudbees.jenkins.GitHubPushTrigger plugin="github"/>
  </triggers>

  <scm class="hudson.plugins.git.GitSCM" plugin="git">
    <configVersion>2</configVersion>
    <userRemoteConfigs>
      <hudson.plugins.git.UserRemoteConfig>
        <url>https://github.com/jungjin-lee90/DevOpsPF</url>
      </hudson.plugins.git.UserRemoteConfig>
    </userRemoteConfigs>
    <branches>
      <hudson.plugins.git.BranchSpec>
        <name>*/main</name>
      </hudson.plugins.git.BranchSpec>
    </branches>
  </scm>

  <builders/>
  <publishers/>
  <buildWrappers/>
</project>
"""

url = f"{jenkins_url}/createItem?name={job_name}"
headers = {"Content-Type": "application/xml"}
auth = HTTPBasicAuth(user, token)

res = requests.post(url, headers=headers, data=job_config_xml.encode("utf-8"), auth=auth)
print(res.status_code)
print(res.text)

