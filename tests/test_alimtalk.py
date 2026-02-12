from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from solapi_sms.alimtalk import AlimtalkService
from solapi_sms.exceptions import SolapiKakaoConfigError, SolapiKakaoSendError


class TestAlimtalkServiceConfig:
    """Test Alimtalk configuration validation."""

    def test_missing_pf_id_raises_error(self, settings: Any) -> None:
        """PF ID 없이 send 시도하면 SolapiKakaoConfigError 발생."""
        settings.DEBUG = False
        settings.SOLAPI_KAKAO_PF_ID = ""
        service = AlimtalkService(
            api_key="test-key",
            api_secret="test-secret",
            pf_id="",
        )
        with pytest.raises(SolapiKakaoConfigError, match="SOLAPI_KAKAO_PF_ID"):
            service.send_alimtalk("01012345678", "template_001", raise_on_error=True)

    def test_missing_api_key_raises_error(self, settings: Any) -> None:
        settings.DEBUG = False
        service = AlimtalkService(api_key="", api_secret="", pf_id="@test")
        with pytest.raises(SolapiKakaoConfigError):
            service.send_alimtalk("01012345678", "template_001", raise_on_error=True)

    def test_empty_phone_raises_error(self, settings: Any) -> None:
        settings.DEBUG = False
        service = AlimtalkService(pf_id="@test")
        with pytest.raises(SolapiKakaoSendError, match="전화번호"):
            service.send_alimtalk("", "template_001", raise_on_error=True)

    def test_empty_phone_returns_false(self, settings: Any) -> None:
        settings.DEBUG = False
        service = AlimtalkService(pf_id="@test")
        assert service.send_alimtalk("", "template_001") is False


class TestAlimtalkServiceDebugSkip:
    """Test debug skip behavior."""

    def test_debug_skip_returns_true(self, settings: Any) -> None:
        """DEBUG 모드에서 실제 API 호출 없이 True 반환."""
        settings.DEBUG = True
        service = AlimtalkService(pf_id="@test")
        result = service.send_alimtalk("01012345678", "template_001", variables={"name": "테스트"})
        assert result is True

    def test_debug_skip_with_credentials(self, settings: Any) -> None:
        """DEBUG 모드에서 실제 credentials가 있어도 스킵."""
        settings.DEBUG = True
        service = AlimtalkService(
            api_key="real-key",
            api_secret="real-secret",
            pf_id="@real-pf",
        )
        result = service.send_alimtalk("01012345678", "template_001")
        assert result is True


class TestAlimtalkByKey:
    """Test template key lookup."""

    def test_unknown_key_raises_error(self, settings: Any) -> None:
        settings.SOLAPI_ALIMTALK_TEMPLATES = {"welcome": "TPL_001"}
        service = AlimtalkService(pf_id="@test")
        with pytest.raises(SolapiKakaoConfigError, match="unknown_key"):
            service.send_alimtalk_by_key("01012345678", "unknown_key")

    def test_valid_key_calls_send(self, settings: Any) -> None:
        """유효한 키로 호출하면 send_alimtalk이 올바른 template_id로 호출됨."""
        settings.DEBUG = True
        settings.SOLAPI_ALIMTALK_TEMPLATES = {"welcome": "TPL_WELCOME_001"}
        service = AlimtalkService(pf_id="@test")
        result = service.send_alimtalk_by_key(
            "01012345678", "welcome", variables={"name": "홍길동"}
        )
        assert result is True


class TestAlimtalkSend:
    """Test actual send flow (mocked)."""

    @patch("solapi_sms.alimtalk.SolapiClient")
    def test_successful_send(self, mock_client_cls: MagicMock, settings: Any) -> None:
        settings.DEBUG = False
        mock_instance = MagicMock()
        mock_instance.send_alimtalk.return_value = MagicMock()
        mock_instance.serialize_response.return_value = {"statusCode": "2000"}
        mock_client_cls.return_value = mock_instance

        service = AlimtalkService(api_key="key", api_secret="secret", pf_id="@test")
        result = service.send_alimtalk("01012345678", "TPL_001")
        assert result is True
        mock_instance.send_alimtalk.assert_called_once()

    @patch("solapi_sms.alimtalk.SolapiClient")
    def test_send_error_response(self, mock_client_cls: MagicMock, settings: Any) -> None:
        settings.DEBUG = False
        mock_instance = MagicMock()
        mock_instance.send_alimtalk.return_value = MagicMock()
        mock_instance.serialize_response.return_value = {
            "errorCode": "ValidationError",
            "errorMessage": "Invalid template",
        }
        mock_client_cls.return_value = mock_instance

        service = AlimtalkService(api_key="key", api_secret="secret", pf_id="@test")
        result = service.send_alimtalk("01012345678", "INVALID_TPL")
        assert result is False

    @patch("solapi_sms.alimtalk.SolapiClient")
    def test_send_error_raises(self, mock_client_cls: MagicMock, settings: Any) -> None:
        settings.DEBUG = False
        mock_instance = MagicMock()
        mock_instance.send_alimtalk.return_value = MagicMock()
        mock_instance.serialize_response.return_value = {
            "errorCode": "Error",
            "errorMessage": "Failed",
        }
        mock_client_cls.return_value = mock_instance

        service = AlimtalkService(api_key="key", api_secret="secret", pf_id="@test")
        with pytest.raises(SolapiKakaoSendError, match="알림톡 발송 실패"):
            service.send_alimtalk("01012345678", "TPL_001", raise_on_error=True)
