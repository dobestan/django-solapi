# django-solapi

Django SMS integration for SOLAPI with models, admin, and async task support.

## 개발 명령어

```bash
make install    # uv sync --group dev
make lint       # ruff check
make format     # ruff format
make typecheck  # mypy solapi_sms/
make test       # pytest tests/
make ci         # 전체 CI (lint, format, typecheck, test)
make hooks      # Git hooks 설치
```

## 프로젝트 구조

```
django-solapi/
├── solapi_sms/
│   ├── __init__.py
│   ├── admin.py           # SMSLog, SMSVerificationCode Admin
│   ├── apps.py
│   ├── auth.py            # send_verification_code, verify_code 헬퍼
│   ├── client.py          # SOLAPI SDK 래퍼
│   ├── exceptions.py      # SMSError
│   ├── models.py          # SMSLog, SMSVerificationCode
│   ├── services.py        # SMSService
│   ├── settings.py        # Django settings 래퍼
│   ├── signals.py         # sms_sent, sms_failed, verification_*
│   ├── utils.py
│   ├── migrations/
│   └── tasks/
│       ├── __init__.py
│       ├── base.py
│       └── backends/
│           ├── celery.py
│           ├── django6.py
│           └── sync.py
├── tests/
│   ├── settings.py
│   └── test_service.py
└── docs/
    ├── installation.md
    ├── models.md
    ├── admin.md
    ├── auth.md
    └── celery.md
```

## 주요 모듈

### SMSService (services.py)
```python
from solapi_sms.services import SMSService

service = SMSService()
service.send_sms("01012345678", "메시지 내용")

# 인증코드
verification = service.create_verification("01012345678")
service.send_verification_code("01012345678", verification.code)
is_valid = service.verify_code("01012345678", "123456")
```

### Auth Helpers (auth.py)
```python
from solapi_sms.auth import send_verification_code, verify_code

result = send_verification_code("01012345678")
result = verify_code("01012345678", "123456")
```

### Signals (signals.py)
- `sms_sent` - SMS 발송 성공
- `sms_failed` - SMS 발송 실패
- `verification_created` - 인증코드 생성
- `verification_verified` - 인증코드 검증 성공

## Django Settings

```python
INSTALLED_APPS = ["solapi_sms"]

# 필수 설정
SOLAPI_API_KEY = "your-api-key"
SOLAPI_API_SECRET = "your-api-secret"
SOLAPI_SENDER_PHONE = "01012345678"

# 선택 설정
SOLAPI_APP_NAME = "서비스명"
SOLAPI_VERIFICATION_TTL_SECONDS = 180
SOLAPI_VERIFICATION_MAX_ATTEMPTS = 5
SOLAPI_TASK_BACKEND = "django6"  # django6, celery, sync
```

## 테스트

```bash
# 전체 테스트
make test

# 특정 테스트
uv run pytest tests/test_service.py -v
```
