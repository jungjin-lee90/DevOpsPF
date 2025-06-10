#!/bin/bash

set -e

echo "시스템 패키지 업데이트..."
sudo apt update && sudo apt upgrade -y

echo "필수 패키지 설치 (git, curl, unzip, etc)..."
sudo apt install -y git curl unzip apt-transport-https ca-certificates gnupg lsb-release software-properties-common

### ----------------------------
### Docker 설치 및 구성
### ----------------------------
echo "Docker 설치 중..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

echo "Docker 권한 부여 (ubuntu 계정)..."
sudo usermod -aG docker $USER

### ----------------------------
### Jenkins 설치
### ----------------------------
echo "Jenkins 설치 중..."
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee \
  /usr/share/keyrings/jenkins-keyring.asc > /dev/null

echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null

sudo apt update
sudo apt install -y openjdk-17-jdk jenkins

echo "Jenkins 시작 중..."
sudo systemctl enable jenkins
sudo systemctl start jenkins

### ----------------------------
### AWS CLI 설치
### ----------------------------
echo "AWS CLI 설치 중..."
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -rf aws awscliv2.zip

### ----------------------------
### kubectl 설치
### ----------------------------
echo "kubectl 설치 중..."
curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

### ----------------------------
### Helm 설치
### ----------------------------
echo "Helm 설치 중..."
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

echo "모든 DevOps 도구 설치 완료"
echo "Jenkins 초기 비밀번호:"
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
