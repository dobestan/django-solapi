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
├── client.py          # SOLAPI SDK 래퍼 (retry with exponential backoff)
├── services.py        # SMSService (send_sms, send_sms_batch)
├── auth.py            # send_verification_code, verify_code
├── models.py          # SMSLog, SMSVerificationCode
├── settings.py        # Django settings 읽기 (SOLAPI_RETRY_* 포함)
├── exceptions.py      # SolapiSMSSendError, SolapiKakaoSendError, etc.
├── signals.py         # sms_sent, sms_failed, verification_*
├── kakao_base.py      # BaseKakaoService (Infotalk/Brand Message 공통)
├── infotalk.py        # InfotalkService (카카오 알림톡)
├── brand_message.py   # BrandMessageService (카카오 브랜드 메시지)
├── rcs.py             # RCSService (RCS 메시징)
└── tasks/backends/    # django6, celery, sync
```

## 사용법

```python
from solapi_sms.services import SMSService
from solapi_sms.auth import send_verification_code, verify_code

# 단일 SMS
service = SMSService()
service.send_sms("01012345678", "메시지")

# 배치 SMS (에러 격리 — 하나 실패해도 나머지 계속)
results = service.send_sms_batch([
    ("01012345678", "첫번째 메시지"),
    ("01099998888", "두번째 메시지"),
])
# [{"phone": "01012345678", "success": True}, {"phone": "01099998888", "success": True}]

# 인증코드
send_verification_code("01012345678")
verify_code("01012345678", "123456")
```

## Reliability & Performance

### Retry with Exponential Backoff
All SOLAPI API calls (SMS, Infotalk, Brand Message, RCS) retry transient
failures up to 3 times with exponential backoff (1s → 2s → 4s).
Transient: `TimeoutError`, `ConnectionError`, `OSError`, `ssl.SSLError`,
`URLError`, httpx errors, SOLAPI 5xx (`UnknownError`).
Non-retryable (auth failure, insufficient balance, invalid phone) fail immediately.
Configurable via `SOLAPI_RETRY_MAX_ATTEMPTS` and `SOLAPI_RETRY_BASE_DELAY`.

### Error Isolation
`send_sms_batch()` processes each message independently. One failed SMS
never aborts the batch. Each result includes `success`/`error` status.

## Django Settings

```python
INSTALLED_APPS = ["solapi_sms"]

SOLAPI_API_KEY = "your-api-key"
SOLAPI_API_SECRET = "your-api-secret"
SOLAPI_SENDER_PHONE = "01012345678"
SOLAPI_TASK_BACKEND = "django6"  # django6, celery, sync
SOLAPI_VERIFICATION_TTL_SECONDS = 180

# Retry (optional — defaults shown)
SOLAPI_RETRY_MAX_ATTEMPTS = 3    # max retries on transient failure
SOLAPI_RETRY_BASE_DELAY = 1.0    # base delay in seconds (doubles each retry)
```
