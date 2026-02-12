"""Tests for RCSService."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from solapi_sms.exceptions import SolapiRCSConfigError, SolapiRCSSendError
from solapi_sms.rcs import RCSService


class TestRCSServiceConfig:
    """Test RCS configuration validation."""

    def test_missing_brand_id_raises_error(self, settings: Any) -> None:
        settings.DEBUG = False
        service = RCSService(api_key="key", api_secret="secret", brand_id="")
        with pytest.raises(SolapiRCSConfigError, match="SOLAPI_RCS_BRAND_ID"):
            service.send_rcs("01012345678", "Hello", raise_on_error=True)

    def test_missing_api_key_raises_error(self, settings: Any) -> None:
        settings.DEBUG = False
        service = RCSService(api_key="", api_secret="", brand_id="BR001")
        with pytest.raises(SolapiRCSConfigError):
            service.send_rcs("01012345678", "Hello", raise_on_error=True)

    def test_empty_phone_raises_error(self, settings: Any) -> None:
        settings.DEBUG = False
        service = RCSService(brand_id="BR001")
        with pytest.raises(SolapiRCSSendError, match="전화번호"):
            service.send_rcs("", "Hello", raise_on_error=True)

    def test_empty_phone_returns_false(self, settings: Any) -> None:
        settings.DEBUG = False
        service = RCSService(brand_id="BR001")
        assert service.send_rcs("", "Hello") is False


class TestRCSDebugSkip:
    """Test debug skip behavior."""

    def test_debug_skip_returns_true(self, settings: Any) -> None:
        settings.DEBUG = True
        service = RCSService(brand_id="BR001")
        result = service.send_rcs("01012345678", "Hello RCS")
        assert result is True

    def test_debug_skip_with_template(self, settings: Any) -> None:
        settings.DEBUG = True
        service = RCSService(brand_id="BR001")
        result = service.send_rcs(
            "01012345678",
            "Hello RCS",
            template_id="TPL_001",
            message_type="RCS_TPL",
        )
        assert result is True


class TestRCSSend:
    """Test actual send flow (mocked)."""

    @patch("solapi_sms.rcs.SolapiClient")
    def test_successful_send(self, mock_client_cls: MagicMock, settings: Any) -> None:
        settings.DEBUG = False
        mock_instance = MagicMock()
        mock_instance.send_rcs.return_value = MagicMock()
        mock_instance.serialize_response.return_value = {"statusCode": "2000"}
        mock_client_cls.return_value = mock_instance

        service = RCSService(api_key="key", api_secret="secret", brand_id="BR001")
        result = service.send_rcs("01012345678", "Hello RCS")
        assert result is True
        mock_instance.send_rcs.assert_called_once()

    @patch("solapi_sms.rcs.SolapiClient")
    def test_send_with_buttons(self, mock_client_cls: MagicMock, settings: Any) -> None:
        settings.DEBUG = False
        mock_instance = MagicMock()
        mock_instance.send_rcs.return_value = MagicMock()
        mock_instance.serialize_response.return_value = {"statusCode": "2000"}
        mock_client_cls.return_value = mock_instance

        service = RCSService(api_key="key", api_secret="secret", brand_id="BR001")
        result = service.send_rcs(
            "01012345678",
            "Hello",
            buttons=[{"button_type": "WL", "button_name": "Visit", "link": "https://example.com"}],
        )
        assert result is True

    @patch("solapi_sms.rcs.SolapiClient")
    def test_send_error_response(self, mock_client_cls: MagicMock, settings: Any) -> None:
        settings.DEBUG = False
        mock_instance = MagicMock()
        mock_instance.send_rcs.return_value = MagicMock()
        mock_instance.serialize_response.return_value = {
            "errorCode": "RCSError",
            "errorMessage": "Brand not registered",
        }
        mock_client_cls.return_value = mock_instance

        service = RCSService(api_key="key", api_secret="secret", brand_id="BR001")
        result = service.send_rcs("01012345678", "Hello")
        assert result is False

    @patch("solapi_sms.rcs.SolapiClient")
    def test_send_error_raises(self, mock_client_cls: MagicMock, settings: Any) -> None:
        settings.DEBUG = False
        mock_instance = MagicMock()
        mock_instance.send_rcs.return_value = MagicMock()
        mock_instance.serialize_response.return_value = {
            "errorCode": "Error",
            "errorMessage": "Failed",
        }
        mock_client_cls.return_value = mock_instance

        service = RCSService(api_key="key", api_secret="secret", brand_id="BR001")
        with pytest.raises(SolapiRCSSendError, match="RCS 발송 실패"):
            service.send_rcs("01012345678", "Hello", raise_on_error=True)


class TestRCSByKey:
    """Test template key lookup."""

    def test_unknown_key_raises_error(self, settings: Any) -> None:
        settings.SOLAPI_RCS_TEMPLATES = {"welcome": "RCS_TPL_001"}
        service = RCSService(brand_id="BR001")
        with pytest.raises(SolapiRCSConfigError, match="unknown_key"):
            service.send_rcs_by_key("01012345678", "unknown_key")

    def test_valid_key(self, settings: Any) -> None:
        settings.DEBUG = True
        settings.SOLAPI_RCS_TEMPLATES = {"welcome": "RCS_TPL_WELCOME"}
        service = RCSService(brand_id="BR001")
        result = service.send_rcs_by_key("01012345678", "welcome", text="Welcome!")
        assert result is True
