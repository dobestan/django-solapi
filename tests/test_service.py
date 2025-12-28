import pytest

from solapi_sms.models import SMSLog, SMSLogStatus, SMSVerificationCode
from solapi_sms.services import SMSService


@pytest.mark.django_db
def test_send_sms_debug_skip_logs(settings):
    """DEBUG 모드에서 API 키가 없을 때 스킵되고 로그가 남는지 테스트"""
    # pytest-django가 DEBUG=False로 설정하므로 명시적으로 True 설정
    settings.DEBUG = True

    service = SMSService()
    result = service.send_sms("01012345678", "테스트 메시지")
    assert result is True
    log = SMSLog.objects.first()
    assert log is not None
    assert log.status == SMSLogStatus.SKIPPED


@pytest.mark.django_db
def test_verification_flow():
    service = SMSService()
    verification = service.create_verification("01012345678", code="123456")
    assert isinstance(verification, SMSVerificationCode)
    assert verification.is_valid()
    assert service.verify_code("01012345678", "000000") is False
    assert service.verify_code("01012345678", "123456") is True
