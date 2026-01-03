#!/bin/bash

# AWS Load Balancer Controller용 IAM Role 생성

ACCOUNT_ID=324547056370
REGION=us-east-1
CLUSTER_NAME=fproject-dev-eks

echo "=== IAM Policy 생성 ==="

# IAM Policy 다운로드
curl -o iam-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.0/docs/install/iam_policy.json

# Policy 생성
aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam-policy.json \
    2>/dev/null || echo "Policy already exists"

echo "=== IAM Role Trust Policy 생성 ==="

# Trust Policy 생성
cat > trust-policy-alb.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/20577F600B73AC80C3C5172729DFC940"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "oidc.eks.us-east-1.amazonaws.com/id/20577F600B73AC80C3C5172729DFC940:sub": "system:serviceaccount:kube-system:aws-load-balancer-controller",
                    "oidc.eks.us-east-1.amazonaws.com/id/20577F600B73AC80C3C5172729DFC940:aud": "sts.amazonaws.com"
                }
            }
        }
    ]
}
EOF

# IAM Role 생성
aws iam create-role \
    --role-name AmazonEKSLoadBalancerControllerRole \
    --assume-role-policy-document file://trust-policy-alb.json \
    2>/dev/null || echo "Role already exists"

# Policy 연결
aws iam attach-role-policy \
    --role-name AmazonEKSLoadBalancerControllerRole \
    --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy

echo "=== IAM Role ARN ==="
aws iam get-role --role-name AmazonEKSLoadBalancerControllerRole --query 'Role.Arn' --output text

echo "=== 완료 ==="
echo "다음 단계: kubectl로 Controller 설치"

rm -f iam-policy.json trust-policy-alb.json
