pipeline {
    agent any

    environment {
        AWS_REGION = 'ap-northeast-2'
        ECR_REPO = '000000000000.dkr.ecr.ap-northeast-2.amazonaws.com/my-repo' // Streamlit 입력값
        IMAGE_TAG = "${new Date().format('yyyyMMddHHmmss')}"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/your/repo.git'
            }
        }

        stage('Docker Build & Push') {
            steps {
                sh '''
                aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO
                docker build -t $ECR_REPO:$IMAGE_TAG .
                docker push $ECR_REPO:$IMAGE_TAG
                '''
            }
        }

        stage('Helm Deploy to EKS') {
            steps {
                sh '''
                aws eks update-kubeconfig --region $AWS_REGION --name your-eks-cluster
                helm upgrade --install devops-app ./helm-chart \
                  --set image.repository=$ECR_REPO \
                  --set image.tag=$IMAGE_TAG \
                  --namespace default \
                  --create-namespace
                '''
            }
        }
    }
}
