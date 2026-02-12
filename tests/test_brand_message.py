from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from solapi_sms.brand_message import BrandMessageService
from solapi_sms.exceptions import SolapiKakaoConfigError


class TestBrandMessageServiceConfig:
    """Test Brand Message configuration validation."""

    def test_missing_pf_id_raises_error(self, settings: Any) -> None:
        settings.DEBUG = False
        service = BrandMessageService(api_key="test-key", api_secret="test-secret", pf_id="")
        with pytest.raises(SolapiKakaoConfigError, match="SOLAPI_KAKAO_PF_ID"):
            service.send_brand_message("01012345678", "template_001", raise_on_error=True)

    def test_empty_phone_returns_false(self, settings: Any) -> None:
        settings.DEBUG = False
        service = BrandMessageService(pf_id="@test")
        assert service.send_brand_message("", "template_001") is False


class TestBrandMessageDebugSkip:
    """Test debug skip behavior."""

    def test_debug_skip_returns_true(self, settings: Any) -> None:
        settings.DEBUG = True
        service = BrandMessageService(pf_id="@test")
        result = service.send_brand_message(
            "01012345678",
            "template_001",
            variables={"name": "테스트"},
            buttons=[
                {"button_name": "바로가기", "button_type": "WL", "link_mo": "https://example.com"}
            ],
        )
        assert result is True


class TestBrandMessageByKey:
    """Test template key lookup."""

    def test_unknown_key_raises_error(self, settings: Any) -> None:
        settings.SOLAPI_BRAND_MESSAGE_TEMPLATES = {"promo": "TPL_PROMO"}
        service = BrandMessageService(pf_id="@test")
        with pytest.raises(SolapiKakaoConfigError, match="unknown_key"):
            service.send_brand_message_by_key("01012345678", "unknown_key")

    def test_valid_key_calls_send(self, settings: Any) -> None:
        settings.DEBUG = True
        settings.SOLAPI_BRAND_MESSAGE_TEMPLATES = {"promo": "TPL_PROMO_001"}
        service = BrandMessageService(pf_id="@test")
        result = service.send_brand_message_by_key(
            "01012345678", "promo", variables={"coupon": "20OFF"}
        )
        assert result is True


class TestBrandMessageSend:
    """Test actual send flow (mocked)."""

    @patch("solapi_sms.kakao_base.SolapiClient")
    def test_successful_send(self, mock_client_cls: MagicMock, settings: Any) -> None:
        settings.DEBUG = False
        mock_instance = MagicMock()
        mock_instance.send_brand_message.return_value = MagicMock()
        mock_instance.serialize_response.return_value = {"statusCode": "2000"}
        mock_client_cls.return_value = mock_instance

        service = BrandMessageService(api_key="key", api_secret="secret", pf_id="@test")
        result = service.send_brand_message(
            "01012345678",
            "TPL_001",
            buttons=[
                {"button_name": "링크", "button_type": "WL", "link_mo": "https://example.com"}
            ],
            targeting="M",
        )
        assert result is True
        mock_instance.send_brand_message.assert_called_once()

    @patch("solapi_sms.kakao_base.SolapiClient")
    def test_send_with_image(self, mock_client_cls: MagicMock, settings: Any) -> None:
        settings.DEBUG = False
        mock_instance = MagicMock()
        mock_instance.send_brand_message.return_value = MagicMock()
        mock_instance.serialize_response.return_value = {"statusCode": "2000"}
        mock_client_cls.return_value = mock_instance

        service = BrandMessageService(api_key="key", api_secret="secret", pf_id="@test")
        result = service.send_brand_message(
            "01012345678",
            "TPL_001",
            image_id="IMG_001",
            targeting="I",
        )
        assert result is True
        call_kwargs = mock_instance.send_brand_message.call_args
        assert call_kwargs.kwargs.get("image_id") == "IMG_001"
        assert call_kwargs.kwargs.get("targeting") == "I"
