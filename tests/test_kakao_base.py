"""Tests for BaseKakaoService shared logic."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from solapi_sms.exceptions import SolapiKakaoConfigError, SolapiKakaoSendError
from solapi_sms.kakao_base import BaseKakaoService


class ConcreteKakaoService(BaseKakaoService):
    """Concrete implementation for testing."""

    service_name = "TestKakao"
    error_prefix = "테스트 발송 실패"
    template_settings_key = "SOLAPI_TEST_TEMPLATES"

    def _call_client(
        self,
        client: Any,
        phone: str,
        template_id: str,
        variables: dict[str, str] | None,
        **kwargs: Any,
    ) -> Any:
        return client.send_test(
            to=phone,
            template_id=template_id,
            pf_id=self.pf_id,
            variables=variables,
        )


class TestBaseKakaoServiceConfig:
    """Test configuration validation."""

    def test_validate_missing_all(self, settings: Any) -> None:
        settings.DEBUG = False
        service = ConcreteKakaoService(api_key="", api_secret="", pf_id="")
        with pytest.raises(SolapiKakaoConfigError, match="SOLAPI_KAKAO_PF_ID"):
            service._validate_config()

    def test_validate_missing_pf_id(self, settings: Any) -> None:
        settings.DEBUG = False
        service = ConcreteKakaoService(api_key="key", api_secret="secret", pf_id="")
        with pytest.raises(SolapiKakaoConfigError):
            service._validate_config()

    def test_validate_success(self, settings: Any) -> None:
        service = ConcreteKakaoService(api_key="key", api_secret="secret", pf_id="@pf")
        service._validate_config()  # Should not raise


class TestMaskPhone:
    """Test phone masking."""

    def test_normal_phone(self) -> None:
        assert BaseKakaoService._mask_phone("01012345678") == "010****"

    def test_short_phone(self) -> None:
        assert BaseKakaoService._mask_phone("010") == "010"

    def test_empty_phone(self) -> None:
        assert BaseKakaoService._mask_phone("") == ""


class TestBaseSend:
    """Test _send() shared logic."""

    def test_empty_phone_returns_false(self, settings: Any) -> None:
        settings.DEBUG = False
        service = ConcreteKakaoService(pf_id="@test")
        assert service._send("", "TPL_001") is False

    def test_empty_phone_raises(self, settings: Any) -> None:
        settings.DEBUG = False
        service = ConcreteKakaoService(pf_id="@test")
        with pytest.raises(SolapiKakaoSendError, match="전화번호"):
            service._send("", "TPL_001", raise_on_error=True)

    def test_debug_skip(self, settings: Any) -> None:
        settings.DEBUG = True
        service = ConcreteKakaoService(pf_id="@test")
        assert service._send("01012345678", "TPL_001") is True

    @patch("solapi_sms.kakao_base.SolapiClient")
    def test_success_flow(self, mock_client_cls: MagicMock, settings: Any) -> None:
        settings.DEBUG = False
        mock_instance = MagicMock()
        mock_instance.send_test.return_value = MagicMock()
        mock_instance.serialize_response.return_value = {"statusCode": "2000"}
        mock_client_cls.return_value = mock_instance

        service = ConcreteKakaoService(api_key="key", api_secret="secret", pf_id="@test")
        assert service._send("01012345678", "TPL_001") is True

    @patch("solapi_sms.kakao_base.SolapiClient")
    def test_error_response(self, mock_client_cls: MagicMock, settings: Any) -> None:
        settings.DEBUG = False
        mock_instance = MagicMock()
        mock_instance.send_test.return_value = MagicMock()
        mock_instance.serialize_response.return_value = {
            "errorCode": "Err",
            "errorMessage": "Test error",
        }
        mock_client_cls.return_value = mock_instance

        service = ConcreteKakaoService(api_key="key", api_secret="secret", pf_id="@test")
        assert service._send("01012345678", "TPL_001") is False

    @patch("solapi_sms.kakao_base.SolapiClient")
    def test_exception_returns_false(self, mock_client_cls: MagicMock, settings: Any) -> None:
        settings.DEBUG = False
        mock_client_cls.side_effect = RuntimeError("Connection error")

        service = ConcreteKakaoService(api_key="key", api_secret="secret", pf_id="@test")
        assert service._send("01012345678", "TPL_001") is False

    @patch("solapi_sms.kakao_base.SolapiClient")
    def test_exception_raises(self, mock_client_cls: MagicMock, settings: Any) -> None:
        settings.DEBUG = False
        mock_client_cls.side_effect = RuntimeError("Connection error")

        service = ConcreteKakaoService(api_key="key", api_secret="secret", pf_id="@test")
        with pytest.raises(SolapiKakaoSendError, match="Connection error"):
            service._send("01012345678", "TPL_001", raise_on_error=True)


class TestBaseSendByKey:
    """Test _send_by_key() template lookup."""

    def test_unknown_key_raises(self, settings: Any) -> None:
        settings.SOLAPI_TEST_TEMPLATES = {"welcome": "TPL_001"}
        service = ConcreteKakaoService(pf_id="@test")
        with pytest.raises(SolapiKakaoConfigError, match="nonexistent"):
            service._send_by_key("01012345678", "nonexistent")

    def test_valid_key(self, settings: Any) -> None:
        settings.DEBUG = True
        settings.SOLAPI_TEST_TEMPLATES = {"welcome": "TPL_WELCOME"}
        service = ConcreteKakaoService(pf_id="@test")
        assert service._send_by_key("01012345678", "welcome") is True

    def test_empty_templates(self, settings: Any) -> None:
        service = ConcreteKakaoService(pf_id="@test")
        with pytest.raises(SolapiKakaoConfigError):
            service._send_by_key("01012345678", "any_key")
