# django-solapi

Django SMS integration for SOLAPI with models, admin, and async task support.

## 개발

```bash
poe ci         # lint + format + typecheck + test
poe test       # pytest
```

## 프로젝트 구조

```
solapi_sms/
├── client.py          # SOLAPI SDK 래퍼
├── services.py        # SMSService
├── auth.py            # send_verification_code, verify_code
├── models.py          # SMSLog, SMSVerificationCode
├── signals.py         # sms_sent, sms_failed, verification_*
└── tasks/backends/    # django6, celery, sync
```

## 사용법

```python
from solapi_sms.services import SMSService
from solapi_sms.auth import send_verification_code, verify_code

# 서비스 직접 사용
service = SMSService()
service.send_sms("01012345678", "메시지")
verification = service.create_verification("01012345678")

# 헬퍼 사용
send_verification_code("01012345678")
verify_code("01012345678", "123456")
```

## Django Settings

```python
INSTALLED_APPS = ["solapi_sms"]

SOLAPI_API_KEY = "your-api-key"
SOLAPI_API_SECRET = "your-api-secret"
SOLAPI_SENDER_PHONE = "01012345678"
SOLAPI_TASK_BACKEND = "django6"  # django6, celery, sync
SOLAPI_VERIFICATION_TTL_SECONDS = 180
```
