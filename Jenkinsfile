pipeline {
  agent any

  environment {
    AWS_REGION = 'ap-northeast-2'
    ECR_REPO = '123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/devops-dashboard'
    IMAGE_TAG = "latest"
    K8S_MANIFEST_DIR = "k8s"
  }

  stages {
    stage('Checkout') {
      steps {
        echo "✅ GitHub 코드 체크아웃"
        checkout scm
      }
    }

    stage('Login to AWS ECR') {
      steps {
        echo "🔐 ECR 로그인"
        sh '''
          aws ecr get-login-password --region $AWS_REGION \
            | docker login --username AWS --password-stdin $ECR_REPO
        '''
      }
    }

    stage('Build Docker Image') {
      steps {
        echo "🔧 Docker 이미지 빌드"
        sh '''
          docker build -t devops-dashboard:$IMAGE_TAG .
          docker tag devops-dashboard:$IMAGE_TAG $ECR_REPO:$IMAGE_TAG
        '''
      }
    }

    stage('Push to ECR') {
      steps {
        echo "📤 ECR로 Docker 이미지 푸시"
        sh '''
          docker push $ECR_REPO:$IMAGE_TAG
        '''
      }
    }

    stage('Deploy to EKS') {
      steps {
        echo "🚀 EKS 클러스터로 배포"
        sh '''
          aws eks update-kubeconfig --region $AWS_REGION --name <클러스터명>

          # 환경 변수 주입을 위해 이미지 경로를 YAML에 삽입하거나 sed 치환 가능
          kubectl set image deployment/devops-dashboard \
            devops-dashboard=$ECR_REPO:$IMAGE_TAG \
            --namespace default || \
          kubectl apply -f $K8S_MANIFEST_DIR/
        '''
      }
    }
  }

  post {
    success {
      echo "🎉 전체 파이프라인 완료: 빌드 → 푸시 → 배포"
    }
    failure {
      echo "❌ 실패 발생: 로그 확인 요망"
    }
  }
}
