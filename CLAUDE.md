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

## 카카오/RCS 메시징

```python
from solapi_sms.infotalk import InfotalkService
from solapi_sms.brand_message import BrandMessageService
from solapi_sms.rcs import RCSService

# 카카오 알림톡
infotalk = InfotalkService()
infotalk.send("01012345678", template_id="KA01TP001", variables={"name": "홍길동"})

# 카카오 브랜드 메시지
brand = BrandMessageService()
brand.send("01012345678", template_id="BM01TP001", variables={"order_id": "ORD-001"})

# RCS 메시징
rcs = RCSService()
rcs.send("01012345678", "RCS 메시지 내용")
```

모든 메시징 채널은 동일한 retry + backoff 정책 적용.

## 에러 처리

| Exception | 발생 시점 |
|-----------|----------|
| `SolapiSMSConfigError` | API Key/Secret/Sender 미설정 |
| `SolapiSMSSendError` | SMS 발송 실패 (잔액 부족, 잘못된 번호 등) |
| `SolapiKakaoConfigError` | 카카오 설정 미완료 |
| `SolapiKakaoSendError` | 카카오 메시지 발송 실패 |
| `SolapiRCSConfigError` | RCS 설정 미완료 |
| `SolapiRCSSendError` | RCS 메시지 발송 실패 |

**Retry 대상**: `TimeoutError`, `ConnectionError`, `OSError`, `ssl.SSLError`, SOLAPI 5xx (`UnknownError`)
**즉시 실패**: 인증 실패, 잔액 부족, 잘못된 전화번호

## Django Signals

| Signal | 발생 시점 |
|--------|----------|
| `sms_sent` | SMS 발송 성공 |
| `sms_failed` | SMS 발송 실패 |
| `verification_requested` | 인증코드 요청 |
| `verification_completed` | 인증코드 검증 성공 |

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

## 주의사항

| 주의 | 설명 |
|------|------|
| Task backend | 프로덕션에서 `django6` backend 사용 시 `python manage.py db_worker` 필요 |
| SMSLog 모델 | 발송 기록 자동 저장. Admin에서 조회 가능 |
| 인증코드 TTL | 기본 180초. `SOLAPI_VERIFICATION_TTL_SECONDS`로 조정 |
| 배치 격리 | `send_sms_batch()`에서 하나 실패해도 나머지 계속 발송 |
| 테스트 환경 | 실제 SMS 발송 없이 테스트하려면 mock 필요 (sandbox API 미제공) |
