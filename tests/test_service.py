from typing import Any

import pytest

from solapi_sms.models import SMSLog, SMSLogStatus, SMSVerificationCode
from solapi_sms.services import SMSService


@pytest.mark.django_db
def test_send_sms_debug_skip_logs(settings: Any) -> None:
    """DEBUG 모드에서 API 키가 없을 때 스킵되고 로그가 남는지 테스트"""
    settings.DEBUG = True

    service = SMSService()
    result = service.send_sms("01012345678", "테스트 메시지")
    assert result is True
    log = SMSLog.objects.first()
    assert log is not None
    assert log.status == SMSLogStatus.SKIPPED


@pytest.mark.django_db
def test_send_sms_debug_skip_with_credentials(settings: Any) -> None:
    """DEBUG 모드에서 실제 credentials가 있어도 스킵되는지 테스트 (핵심 버그 방지)"""
    settings.DEBUG = True

    service = SMSService(
        api_key="real-api-key",
        api_secret="real-api-secret",  # noqa: S106
        sender="01012345678",
    )
    result = service.send_sms("01099998888", "테스트 메시지")
    assert result is True
    log = SMSLog.objects.first()
    assert log is not None
    assert log.status == SMSLogStatus.SKIPPED
    assert log.response_data == {"debug_skip": True}


@pytest.mark.django_db
def test_verification_flow() -> None:
    service = SMSService()
    verification = service.create_verification("01012345678", code="123456")
    assert isinstance(verification, SMSVerificationCode)
    assert verification.is_valid()
    assert service.verify_code("01012345678", "000000") is False
    assert service.verify_code("01012345678", "123456") is True
