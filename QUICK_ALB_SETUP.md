# AWS Load Balancer Controller 빠른 설치

## 현재 상태
- Ingress 파일: 준비됨 (k8s-ingress.yaml)
- ALB Controller: 미설치 (설치 필요)
- kubectl: 미설치 (설치 필요)

## 단계별 설치

### 1단계: IAM Role 생성 (Windows PowerShell)

```powershell
# IAM Policy 다운로드
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.0/docs/install/iam_policy.json" -OutFile "iam-policy.json"

# Policy 생성
aws iam create-policy --policy-name AWSLoadBalancerControllerIAMPolicy --policy-document file://iam-policy.json

# Trust Policy 생성
@"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::324547056370:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/20577F600B73AC80C3C5172729DFC940"
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
"@ | Out-File -FilePath trust-policy-alb.json -Encoding utf8

# IAM Role 생성
aws iam create-role --role-name AmazonEKSLoadBalancerControllerRole --assume-role-policy-document file://trust-policy-alb.json

# Policy 연결
aws iam attach-role-policy --role-name AmazonEKSLoadBalancerControllerRole --policy-arn arn:aws:iam::324547056370:policy/AWSLoadBalancerControllerIAMPolicy
```

### 2단계: GitHub Actions로 자동 설치 (권장)

GitHub Actions workflow를 추가하여 자동으로 설치하는 것이 가장 쉽습니다.

### 3단계: 또는 AWS CloudFormation 사용

AWS Console > CloudFormation에서 스택 생성:

**템플릿 URL:**
```
https://s3.us-west-2.amazonaws.com/amazon-eks/cloudformation/2023-01-11/aws-load-balancer-controller.yaml
```

**파라미터:**
- ClusterName: `fproject-dev-eks`
- ServiceAccountRoleArn: `arn:aws:iam::324547056370:role/AmazonEKSLoadBalancerControllerRole`

## 가장 쉬운 방법: GitHub Actions 사용

workflow 파일에 ALB Controller 설치 단계를 추가하면 자동으로 설치됩니다.

## 설치 확인

설치 후 다음 명령어로 확인:

```bash
kubectl get deployment -n kube-system aws-load-balancer-controller
```

## Ingress 배포

Controller 설치 후:

```bash
kubectl apply -f k8s-ingress.yaml
```

또는 GitHub Actions 다시 실행

## 대안: Service Type LoadBalancer 사용

ALB Controller 없이 바로 사용하려면 Service 타입을 LoadBalancer로 변경:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: journal-api-service
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing"
spec:
  type: LoadBalancer  # ClusterIP에서 변경
  selector:
    app: journal-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
```

이 방법은 NLB를 생성하며, ALB Controller 없이 바로 작동합니다.

```bash
# 1. IAM Policy 생성
curl -o iam-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.0/docs/install/iam_policy.json

aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam-policy.json

# 2. IAM Role 생성 및 ServiceAccount 연결
eksctl create iamserviceaccount \
  --cluster=fproject-dev-eks \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn=arn:aws:iam::324547056370:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve \
  --region=us-east-1

# 3. Helm으로 Controller 설치
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=fproject-dev-eks \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

## 설치 확인

```bash
kubectl get deployment -n kube-system aws-load-balancer-controller
```

출력 예시:
```
NAME                           READY   UP-TO-DATE   AVAILABLE   AGE
aws-load-balancer-controller   2/2     2            2           1m
```

## Ingress 배포

Controller 설치 후 Ingress 배포:

```bash
kubectl apply -f k8s-ingress.yaml
```

또는 GitHub Actions 다시 실행

## ALB 생성 확인

```bash
# Ingress 상태 확인
kubectl get ingress journal-api-ingress

# ALB 확인
aws elbv2 describe-load-balancers --region us-east-1 --query "LoadBalancers[?Type=='application']"
```

## Route 53 설정

ALB가 생성되면:

1. ALB DNS 이름 확인: `kubectl get ingress journal-api-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'`

2. Route 53에서 레코드 생성:
   - 이름: `journal`
   - 타입: `A - Alias`
   - 대상: ALB 선택

## 접근 테스트

```bash
curl https://journal.aws11.shop/health
```

## 예상 소요 시간

- Controller 설치: 2-3분
- ALB 생성: 3-5분
- DNS 전파: 1-2분

총 약 10분 소요
