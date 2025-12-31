# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.5] - 2024-12-29

### Changed
- Python 3.14 / Django 6.0 지원

## [1.0.0] - 2024-12-28

**Initial Release** - SOLAPI SMS 통합 Django 패키지

### Added

#### Features
- **SMSService**: SOLAPI SDK 기반 SMS 발송 서비스
- **SMSLog Model**: SMS 발송 로그 저장 (status, response_data 포함)
- **SMSVerificationCode Model**: 인증코드 생성/검증
- **Task Backends**: Django 6 Tasks, Celery, Sync 지원
- **Signals**: SMS 발송 및 인증 이벤트 시그널
  - `sms_sent` - SMS 발송 성공
  - `sms_failed` - SMS 발송 실패
  - `verification_created` - 인증코드 생성
  - `verification_verified` - 인증코드 검증 성공
- **Admin**: SMSLog, SMSVerificationCode 관리자 페이지

#### Technical
- Python 3.12+ 지원
- Django 5.0, 5.1, 5.2, 6.0 지원
- mypy strict 모드 타입 힌트
- PEP 561 준수 (py.typed)
