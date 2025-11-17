# AWS CloudWatch 고급 모니터링 설정 가이드

Stock Lab 프로젝트를 위한 포괄적인 CloudWatch 모니터링 및 알람 설정 가이드입니다.

---

## 📋 목차

1. [모니터링 아키텍처](#모니터링-아키텍처)
2. [CloudWatch Agent 설정](#cloudwatch-agent-설정)
3. [커스텀 메트릭 수집](#커스텀-메트릭-수집)
4. [대시보드 구성](#대시보드-구성)
5. [알람 설정](#알람-설정)
6. [로그 그룹 및 필터](#로그-그룹-및-필터)
7. [비용 최적화](#비용-최적화)

---

## 모니터링 아키텍처

```
┌─────────────────────────────────────────────────┐
│                EC2 Instances                    │
│  ┌──────────────────────────────────────────┐  │
│  │      CloudWatch Agent                    │  │
│  │  - System Metrics (CPU, Memory, Disk)    │  │
│  │  - Application Logs                      │  │
│  │  - Custom Metrics                        │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│            CloudWatch Logs/Metrics              │
│  - Log Groups                                   │
│  - Metric Filters                               │
│  - Log Insights                                 │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│         CloudWatch Dashboards & Alarms          │
│  - Real-time Dashboards                         │
│  - Alarms → SNS → Slack/Email                   │
└─────────────────────────────────────────────────┘
```

---

## CloudWatch Agent 설정

### 1. IAM 역할 권한 추가

EC2 인스턴스의 IAM 역할에 CloudWatch 권한 추가:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "ec2:DescribeVolumes",
        "ec2:DescribeTags",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams",
        "logs:DescribeLogGroups",
        "logs:CreateLogStream",
        "logs:CreateLogGroup"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:PutParameter"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/AmazonCloudWatch-*"
    }
  ]
}
```

### 2. CloudWatch Agent 설정 파일

`/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json`:

```json
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "root"
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/app/SL-Back-end/logs/app.log",
            "log_group_name": "/stocklab/production/backend/application",
            "log_stream_name": "{instance_id}/app",
            "retention_in_days": 30,
            "timezone": "Local"
          },
          {
            "file_path": "/app/SL-Back-end/logs/error.log",
            "log_group_name": "/stocklab/production/backend/errors",
            "log_stream_name": "{instance_id}/errors",
            "retention_in_days": 90,
            "timezone": "Local"
          },
          {
            "file_path": "/app/SL-Front-End/logs/*.log",
            "log_group_name": "/stocklab/production/frontend/application",
            "log_stream_name": "{instance_id}/app",
            "retention_in_days": 30,
            "timezone": "Local"
          },
          {
            "file_path": "/var/log/docker.log",
            "log_group_name": "/stocklab/production/docker",
            "log_stream_name": "{instance_id}/docker",
            "retention_in_days": 14,
            "timezone": "Local"
          },
          {
            "file_path": "/var/log/messages",
            "log_group_name": "/stocklab/production/system",
            "log_stream_name": "{instance_id}/messages",
            "retention_in_days": 7,
            "timezone": "Local"
          }
        ]
      }
    }
  },
  "metrics": {
    "namespace": "StockLab/Production",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          {
            "name": "cpu_usage_idle",
            "rename": "CPU_IDLE",
            "unit": "Percent"
          },
          {
            "name": "cpu_usage_iowait",
            "rename": "CPU_IOWAIT",
            "unit": "Percent"
          },
          "cpu_time_guest"
        ],
        "metrics_collection_interval": 60,
        "resources": [
          "*"
        ],
        "totalcpu": false
      },
      "disk": {
        "measurement": [
          {
            "name": "used_percent",
            "rename": "DISK_USED",
            "unit": "Percent"
          },
          "inodes_free"
        ],
        "metrics_collection_interval": 60,
        "resources": [
          "*"
        ]
      },
      "diskio": {
        "measurement": [
          "io_time",
          "write_bytes",
          "read_bytes",
          "writes",
          "reads"
        ],
        "metrics_collection_interval": 60,
        "resources": [
          "*"
        ]
      },
      "mem": {
        "measurement": [
          {
            "name": "mem_used_percent",
            "rename": "MEMORY_USED",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60
      },
      "netstat": {
        "measurement": [
          "tcp_established",
          "tcp_time_wait"
        ],
        "metrics_collection_interval": 60
      },
      "swap": {
        "measurement": [
          {
            "name": "swap_used_percent",
            "rename": "SWAP_USED",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60
      }
    }
  }
}
```

### 3. EC2 User Data에 Agent 설치 추가

`ec2-user-data-ecr.sh`에 추가:

```bash
#!/bin/bash

# ... 기존 코드 ...

# CloudWatch Agent 설치
echo "Installing CloudWatch Agent..."
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
sudo rpm -U ./amazon-cloudwatch-agent.rpm

# CloudWatch Agent 설정 파일 생성
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json <<'EOF'
{
  # ... 위의 설정 파일 내용 ...
}
EOF

# CloudWatch Agent 시작
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# CloudWatch Agent 자동 시작 설정
sudo systemctl enable amazon-cloudwatch-agent
sudo systemctl start amazon-cloudwatch-agent

echo "CloudWatch Agent installed and started"
```

---

## 커스텀 메트릭 수집

### Backend 애플리케이션 메트릭

`SL-Back-end/app/monitoring/cloudwatch.py`:

```python
import boto3
from datetime import datetime
from functools import wraps
import time

class CloudWatchMetrics:
    def __init__(self, namespace="StockLab/Application"):
        self.cloudwatch = boto3.client('cloudwatch', region_name='ap-northeast-2')
        self.namespace = namespace

    def put_metric(self, metric_name: str, value: float, unit: str = "Count", dimensions: dict = None):
        """CloudWatch에 커스텀 메트릭 전송"""
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow()
        }

        if dimensions:
            metric_data['Dimensions'] = [
                {'Name': k, 'Value': v} for k, v in dimensions.items()
            ]

        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[metric_data]
            )
        except Exception as e:
            # 메트릭 전송 실패는 애플리케이션 실행에 영향을 주지 않음
            print(f"Failed to send metric: {e}")

    def measure_execution_time(self, metric_name: str):
        """함수 실행 시간 측정 데코레이터"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    execution_time = (time.time() - start_time) * 1000  # ms
                    self.put_metric(
                        metric_name=metric_name,
                        value=execution_time,
                        unit='Milliseconds',
                        dimensions={'Function': func.__name__}
                    )
            return wrapper
        return decorator

    def count_api_calls(self, endpoint: str, status_code: int):
        """API 호출 횟수 카운트"""
        self.put_metric(
            metric_name='APIRequests',
            value=1,
            dimensions={
                'Endpoint': endpoint,
                'StatusCode': str(status_code)
            }
        )

    def track_error(self, error_type: str):
        """에러 발생 추적"""
        self.put_metric(
            metric_name='ApplicationErrors',
            value=1,
            dimensions={'ErrorType': error_type}
        )

    def track_database_query_time(self, query_name: str, duration_ms: float):
        """데이터베이스 쿼리 시간 추적"""
        self.put_metric(
            metric_name='DatabaseQueryDuration',
            value=duration_ms,
            unit='Milliseconds',
            dimensions={'QueryName': query_name}
        )

# 싱글톤 인스턴스
cloudwatch_metrics = CloudWatchMetrics()
```

### 사용 예시

```python
from app.monitoring.cloudwatch import cloudwatch_metrics
from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/api/v1/stocks")
@cloudwatch_metrics.measure_execution_time("StocksList")
async def get_stocks(request: Request):
    try:
        # ... 비즈니스 로직 ...

        cloudwatch_metrics.count_api_calls(
            endpoint="/api/v1/stocks",
            status_code=200
        )

        return {"stocks": stocks}

    except Exception as e:
        cloudwatch_metrics.track_error(type(e).__name__)
        raise
```

---

## 대시보드 구성

### CloudWatch Dashboard JSON

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/EC2", "CPUUtilization", {"stat": "Average"}],
          ["StockLab/Production", "CPU_IDLE", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "ap-northeast-2",
        "title": "CPU Utilization",
        "yAxis": {"left": {"min": 0, "max": 100}}
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["StockLab/Production", "MEMORY_USED", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "ap-northeast-2",
        "title": "Memory Usage",
        "yAxis": {"left": {"min": 0, "max": 100}}
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["StockLab/Application", "APIRequests", {"stat": "Sum"}]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "ap-northeast-2",
        "title": "API Requests"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ApplicationELB", "TargetResponseTime", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "ap-northeast-2",
        "title": "ALB Response Time"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ApplicationELB", "HealthyHostCount", {"stat": "Average"}],
          [".", "UnHealthyHostCount", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "ap-northeast-2",
        "title": "Target Health"
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '/stocklab/production/backend/errors'\n| fields @timestamp, @message\n| sort @timestamp desc\n| limit 20",
        "region": "ap-northeast-2",
        "title": "Recent Errors",
        "stacked": false
      }
    }
  ]
}
```

### CLI로 대시보드 생성

```bash
aws cloudwatch put-dashboard \
  --dashboard-name StockLab-Production \
  --dashboard-body file://dashboard.json \
  --region ap-northeast-2
```

---

## 알람 설정

### 1. CPU 사용률 알람

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name stocklab-prod-high-cpu \
  --alarm-description "CPU utilization exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --datapoints-to-alarm 2 \
  --alarm-actions arn:aws:sns:ap-northeast-2:ACCOUNT_ID:stocklab-alerts \
  --region ap-northeast-2
```

### 2. 메모리 사용률 알람

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name stocklab-prod-high-memory \
  --alarm-description "Memory utilization exceeds 85%" \
  --metric-name MEMORY_USED \
  --namespace StockLab/Production \
  --statistic Average \
  --period 300 \
  --threshold 85 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:ap-northeast-2:ACCOUNT_ID:stocklab-alerts \
  --region ap-northeast-2
```

### 3. ALB 5xx 에러 알람

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name stocklab-prod-alb-5xx-errors \
  --alarm-description "ALB 5xx errors detected" \
  --metric-name HTTPCode_Target_5XX_Count \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 60 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:ap-northeast-2:ACCOUNT_ID:stocklab-critical \
  --region ap-northeast-2
```

### 4. 디스크 사용률 알람

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name stocklab-prod-high-disk \
  --alarm-description "Disk usage exceeds 80%" \
  --metric-name DISK_USED \
  --namespace StockLab/Production \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:ap-northeast-2:ACCOUNT_ID:stocklab-alerts \
  --region ap-northeast-2
```

### 5. RDS CPU 알람

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name stocklab-prod-rds-high-cpu \
  --alarm-description "RDS CPU exceeds 75%" \
  --metric-name CPUUtilization \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 75 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=DBInstanceIdentifier,Value=stocklab-prod-db \
  --alarm-actions arn:aws:sns:ap-northeast-2:ACCOUNT_ID:stocklab-alerts \
  --region ap-northeast-2
```

### SNS 토픽 생성 및 Slack 연동

```bash
# SNS 토픽 생성
aws sns create-topic \
  --name stocklab-alerts \
  --region ap-northeast-2

# 이메일 구독 추가
aws sns subscribe \
  --topic-arn arn:aws:sns:ap-northeast-2:ACCOUNT_ID:stocklab-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com \
  --region ap-northeast-2
```

### Lambda로 SNS → Slack 연동

`cloudwatch-slack-lambda.py`:

```python
import json
import urllib3
import os

http = urllib3.PoolManager()

def lambda_handler(event, context):
    url = os.environ['SLACK_WEBHOOK_URL']

    message = json.loads(event['Records'][0]['Sns']['Message'])

    alarm_name = message['AlarmName']
    new_state = message['NewStateValue']
    reason = message['NewStateReason']

    color = '#FF0000' if new_state == 'ALARM' else '#36a64f'
    emoji = '🚨' if new_state == 'ALARM' else '✅'

    slack_message = {
        'text': f"{emoji} CloudWatch Alarm: {alarm_name}",
        'attachments': [
            {
                'color': color,
                'fields': [
                    {'title': 'Alarm Name', 'value': alarm_name, 'short': True},
                    {'title': 'State', 'value': new_state, 'short': True},
                    {'title': 'Reason', 'value': reason, 'short': False}
                ]
            }
        ]
    }

    encoded_msg = json.dumps(slack_message).encode('utf-8')
    resp = http.request('POST', url, body=encoded_msg)

    return {
        'statusCode': 200,
        'body': json.dumps('Message sent to Slack')
    }
```

---

## 로그 그룹 및 필터

### Metric Filter 생성

#### 에러 로그 필터

```bash
# ERROR 레벨 로그 카운트
aws logs put-metric-filter \
  --log-group-name /stocklab/production/backend/errors \
  --filter-name ErrorCount \
  --filter-pattern "[timestamp, level=ERROR*, ...]" \
  --metric-transformations \
    metricName=ErrorCount,metricNamespace=StockLab/Logs,metricValue=1,defaultValue=0 \
  --region ap-northeast-2
```

#### 응답 시간 필터

```bash
# API 응답 시간 추출
aws logs put-metric-filter \
  --log-group-name /stocklab/production/backend/application \
  --filter-name APIResponseTime \
  --filter-pattern "[timestamp, level, msg, duration]" \
  --metric-transformations \
    metricName=APIResponseTime,metricNamespace=StockLab/Logs,metricValue=$duration \
  --region ap-northeast-2
```

### Log Insights 쿼리 예시

#### 에러 빈도 분석

```sql
fields @timestamp, @message
| filter @message like /ERROR/
| stats count() as error_count by bin(5m)
| sort @timestamp desc
```

#### 느린 API 요청 분석

```sql
fields @timestamp, endpoint, duration
| filter duration > 1000
| sort duration desc
| limit 20
```

---

## 비용 최적화

### 현재 비용 구조

```
CloudWatch Logs:
- 수집: $0.50/GB
- 저장: $0.03/GB/월

CloudWatch Metrics:
- 커스텀 메트릭: $0.30/메트릭/월
- API 요청: $0.01/1,000 요청

CloudWatch Dashboards:
- $3/대시보드/월

예상 월 비용:
- Logs (10GB/월): $5.00
- Metrics (20개): $6.00
- Dashboard (1개): $3.00
─────────────────────────
Total: ~$14/월
```

### 비용 절감 팁

1. **로그 보존 기간 설정**
```bash
# 중요하지 않은 로그는 짧은 보존 기간 설정
aws logs put-retention-policy \
  --log-group-name /stocklab/production/system \
  --retention-in-days 7
```

2. **로그 필터링**
```python
# DEBUG 로그는 프로덕션에서 비활성화
import logging

if os.getenv("ENV") == "production":
    logging.getLogger().setLevel(logging.INFO)
```

3. **메트릭 수집 간격 조정**
```json
{
  "metrics_collection_interval": 300  // 5분 간격 (60초 대신)
}
```

---

## 체크리스트

- [ ] IAM 역할에 CloudWatch 권한 추가
- [ ] CloudWatch Agent 설정 파일 작성
- [ ] EC2 User Data에 Agent 설치 스크립트 추가
- [ ] 커스텀 메트릭 코드 통합
- [ ] SNS 토픽 생성
- [ ] Slack webhook 연동
- [ ] 주요 알람 생성 (CPU, 메모리, 디스크, ALB)
- [ ] CloudWatch Dashboard 생성
- [ ] Metric Filter 설정
- [ ] 로그 보존 정책 설정

---

**CloudWatch 모니터링 설정 완료! 📊**
