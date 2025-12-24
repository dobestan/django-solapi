# django-solapi

Django SMS integration for SOLAPI with standardized models, admin utilities, and Celery-friendly tasks.

## Features

- SOLAPI SDK 기반 SMS 발송
- SMS 발송 로그 모델 (Admin 포함)
- SMS 인증코드 생성/검증 모델 및 서비스
- Admin 표준 유틸 (상태 배지, 재발송 액션 등)
- Celery 작업(Task) 기반 확장 지원

## Installation

```bash
uv add git+https://github.com/dobestan/django-solapi.git
```

## Settings

```python
INSTALLED_APPS = [
    ...
    "solapi_sms",
]

SOLAPI_API_KEY = "your-api-key"
SOLAPI_API_SECRET = "your-api-secret"
SOLAPI_SENDER_PHONE = "01012345678"
SOLAPI_APP_NAME = "서비스명"
```

## Quick Start

```python
from solapi_sms.services import SMSService

service = SMSService()
service.send_sms("01012345678", "[서비스명] 테스트 메시지입니다.")
```

## Verification Code

```python
from solapi_sms.services import SMSService

service = SMSService()
verification = service.create_verification("01012345678")
service.send_verification_code("01012345678", verification.code)

is_verified = service.verify_code("01012345678", "123456")
```

## Celery Task (Optional)

```python
from solapi_sms.tasks import send_sms_task

send_sms_task.delay("01012345678", "[서비스명] 비동기 발송 테스트")
```

## Admin

`SMSLog`, `SMSVerificationCode` 모델이 기본 등록되어 있으며,
프로젝트별 확장을 위해 추상 모델도 제공됩니다.
