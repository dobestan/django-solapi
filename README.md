# django-solapi

Django SMS integration for SOLAPI with standardized models, admin utilities, and async task support.

## Features

- SOLAPI SDK 기반 SMS 발송
- SMS 발송 로그 모델 (Admin 포함)
- SMS 인증코드 생성/검증 모델 및 서비스
- Admin 표준 유틸 (상태 배지, 재발송 액션 등)
- **Django 6 Tasks** 네이티브 지원
- **Celery** 작업(Task) 기반 확장 지원
- 인증코드 발송/검증 헬퍼 (뷰 표준화)
- Signals: `sms_sent`, `sms_failed`, `verification_created`, `verification_verified`

## Installation

### Git (Private Repository)

```bash
# uv
uv add git+https://github.com/dobestan/django-solapi.git

# pip
pip install git+https://github.com/dobestan/django-solapi.git

# Celery 지원 포함
uv add "django-solapi[celery] @ git+https://github.com/dobestan/django-solapi.git"
```

### PyPI (추후 예정)

```bash
uv add django-solapi
```

## Settings

```python
INSTALLED_APPS = [
    ...
    "solapi_sms",
]

# 필수 설정
SOLAPI_API_KEY = "your-api-key"
SOLAPI_API_SECRET = "your-api-secret"
SOLAPI_SENDER_PHONE = "01012345678"

# 선택 설정
SOLAPI_APP_NAME = "서비스명"  # 메시지 템플릿에 사용
SOLAPI_VERIFICATION_TTL_SECONDS = 180  # 인증코드 유효시간 (기본: 3분)
SOLAPI_VERIFICATION_MAX_ATTEMPTS = 5  # 최대 시도 횟수
SOLAPI_VERIFICATION_RATE_LIMIT_COUNT = 5  # Rate limit 횟수
SOLAPI_VERIFICATION_RATE_LIMIT_WINDOW_SECONDS = 3600  # Rate limit 윈도우

# Task 백엔드 설정 (django6, celery, sync)
SOLAPI_TASK_BACKEND = "sync"  # 기본값
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

# 인증코드 생성 및 발송
verification = service.create_verification("01012345678")
service.send_verification_code("01012345678", verification.code)

# 인증코드 검증
is_verified = service.verify_code("01012345678", "123456")
```

## Auth Helpers (Views)

뷰에서 간편하게 사용할 수 있는 헬퍼 함수:

```python
from solapi_sms.auth import send_verification_code, verify_code

# 인증코드 발송
send_result = send_verification_code("01012345678")
if send_result["success"]:
    verification = send_result["verification"]

# 인증코드 검증
verify_result = verify_code("01012345678", "123456")
if verify_result["success"]:
    # 인증 성공
    pass
```

## Async Tasks

### Django 6 Tasks (권장)

Django 6.0+에서는 내장 Tasks 프레임워크를 사용할 수 있습니다:

```python
# settings.py
SOLAPI_TASK_BACKEND = "django6"

# 사용
from solapi_sms.tasks import enqueue_sms, enqueue_verification_code

enqueue_sms("01012345678", "[서비스명] 비동기 발송 테스트")
enqueue_verification_code("01012345678")
```

### Celery

```python
# settings.py
SOLAPI_TASK_BACKEND = "celery"

# 사용
from solapi_sms.tasks import send_sms_task

send_sms_task.delay("01012345678", "[서비스명] 비동기 발송 테스트")
```

## Admin

`SMSLog`, `SMSVerificationCode` 모델이 기본 등록되어 있으며,
프로젝트별 확장을 위해 추상 모델도 제공됩니다.

## API Reference

### SMSService Methods

| 메서드 | 설명 |
|--------|------|
| `send_sms(phone, message)` | SMS 발송 |
| `send_templated(phone, template_key, ...)` | 템플릿 기반 SMS 발송 |
| `create_verification(phone)` | 인증코드 생성 |
| `send_verification_code(phone, code)` | 인증코드 발송 |
| `verify_code(phone, code)` | 인증코드 검증 |

### Signals

| 시그널 | 발생 시점 | 전달 데이터 |
|--------|----------|------------|
| `sms_sent` | SMS 발송 성공 | phone, message, message_type, log, skipped |
| `sms_failed` | SMS 발송 실패 | phone, message, message_type, log |
| `verification_created` | 인증코드 생성 | verification |
| `verification_verified` | 인증코드 검증 성공 | verification |

## Requirements

- Python >= 3.12
- Django >= 5.0 (Django 6.0+ 권장)
- solapi >= 5.0.2

## Changelog

### v1.0.0 (2024-12-28)

**Initial Release** - SOLAPI SMS 통합 Django 패키지

#### Features
- **SMSService**: SOLAPI SDK 기반 SMS 발송 서비스
- **SMSLog Model**: SMS 발송 로그 저장 (status, response_data 포함)
- **SMSVerificationCode Model**: 인증코드 생성/검증
- **Task Backends**: Django 6 Tasks, Celery, Sync 지원
- **Signals**: SMS 발송 및 인증 이벤트 시그널
- **Admin**: SMSLog, SMSVerificationCode 관리자 페이지

#### Technical
- Python 3.12+ 지원
- Django 5.0, 5.1, 5.2, 6.0 지원
- mypy strict 모드 타입 힌트
- PEP 561 준수 (py.typed)

## Documentation

- [설치 가이드](docs/installation.md)
- [모델 상속](docs/models.md)
- [Admin 커스터마이징](docs/admin.md)
- [인증 모듈](docs/auth.md)
- [Celery 설정](docs/celery.md)

## License

MIT License

## Links

- [SOLAPI 개발자 센터](https://developers.solapi.com/)
- [SOLAPI Python SDK](https://github.com/solapi/solapi-python)
