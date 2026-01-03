#!/bin/bash

# AWS Load Balancer Controller 설치 스크립트

CLUSTER_NAME=fproject-dev-eks
REGION=us-east-1
ACCOUNT_ID=324547056370

echo "=== AWS Load Balancer Controller 설치 ==="

# 1. IAM Policy 생성
echo "1. IAM Policy 다운로드 및 생성..."
curl -o iam-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.0/docs/install/iam_policy.json

aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam-policy.json \
    2>/dev/null || echo "Policy already exists"

# 2. IAM Role 생성 (IRSA)
echo "2. ServiceAccount용 IAM Role 생성..."
eksctl create iamserviceaccount \
  --cluster=$CLUSTER_NAME \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn=arn:aws:iam::${ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve \
  --region=$REGION

# 3. Helm 설치 (없는 경우)
if ! command -v helm &> /dev/null; then
    echo "Helm 설치 중..."
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

# 4. Helm repo 추가
echo "3. Helm repo 추가..."
helm repo add eks https://aws.github.io/eks-charts
helm repo update

# 5. AWS Load Balancer Controller 설치
echo "4. AWS Load Balancer Controller 설치..."
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=$CLUSTER_NAME \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set region=$REGION \
  --set vpcId=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query "cluster.resourcesVpcConfig.vpcId" --output text)

# 6. 설치 확인
echo "5. 설치 확인..."
kubectl get deployment -n kube-system aws-load-balancer-controller

echo "=== 설치 완료 ==="
echo "Ingress를 배포하면 자동으로 ALB가 생성됩니다."
