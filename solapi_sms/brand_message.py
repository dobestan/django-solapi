"""Kakao Brand Message (브랜드 메시지) service with logging and debug skip.

Brand Messages replaced FriendTalk (친구톡) from 2026.1.1.
Used for marketing/advertising messages (53~103원/건).
"""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings as django_settings

from .client import SolapiClient
from .exceptions import SolapiKakaoConfigError, SolapiKakaoSendError
from .settings import (
    SOLAPI_API_KEY,
    SOLAPI_API_SECRET,
    SOLAPI_DEBUG_SKIP,
    SOLAPI_KAKAO_PF_ID,
    SOLAPI_SENDER_PHONE,
)

logger = logging.getLogger(__name__)


class BrandMessageService:
    """SOLAPI Brand Message service with logging and debug skip support."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        sender: str | None = None,
        pf_id: str | None = None,
    ) -> None:
        self.api_key = api_key or SOLAPI_API_KEY
        self.api_secret = api_secret or SOLAPI_API_SECRET
        self.sender = sender or SOLAPI_SENDER_PHONE
        self.pf_id = pf_id or SOLAPI_KAKAO_PF_ID

    def _validate_config(self) -> None:
        if not all([self.api_key, self.api_secret, self.pf_id]):
            raise SolapiKakaoConfigError(
                "SOLAPI Brand Message 설정이 누락되었습니다. "
                "SOLAPI_API_KEY, SOLAPI_API_SECRET, SOLAPI_KAKAO_PF_ID를 확인하세요."
            )

    def send_brand_message(
        self,
        phone: str,
        template_id: str,
        variables: dict[str, str] | None = None,
        *,
        disable_sms: bool = False,
        fallback_text: str | None = None,
        buttons: list[dict[str, str]] | None = None,
        image_id: str | None = None,
        targeting: str = "M",
        raise_on_error: bool = False,
    ) -> bool:
        """Send Brand Message (카카오 브랜드 메시지).

        Args:
            phone: Recipient phone number.
            template_id: Kakao-approved template ID.
            variables: Template variables (auto-wrapped with #{} by SDK).
            disable_sms: If True, skip SMS fallback on failure.
            fallback_text: SMS fallback text.
            buttons: Kakao button list (button_name, button_type, link_mo, etc.).
            image_id: SOLAPI image ID for image-type brand messages.
            targeting: Bms targeting type ("M"=mobile, "N"=naver, "I"=image).
            raise_on_error: If True, raise exception on failure.

        Returns:
            True if sent successfully.
        """
        if not phone:
            if raise_on_error:
                raise SolapiKakaoSendError("전화번호가 비어있습니다.")
            return False

        if django_settings.DEBUG and SOLAPI_DEBUG_SKIP:
            logger.info(
                "Brand message skipped (debug mode)",
                extra={
                    "phone": phone[:3] + "****" if len(phone) > 3 else phone,
                    "template_id": template_id,
                    "targeting": targeting,
                },
            )
            return True

        try:
            self._validate_config()
            client = SolapiClient(api_key=self.api_key, api_secret=self.api_secret)
            response = client.send_brand_message(
                to=phone,
                template_id=template_id,
                pf_id=self.pf_id,
                variables=variables,
                sender=self.sender,
                disable_sms=disable_sms,
                fallback_text=fallback_text,
                buttons=buttons,
                image_id=image_id,
                targeting=targeting,
            )
            response_dict = client.serialize_response(response)

            if "errorCode" in response_dict or "errorMessage" in response_dict:
                error_msg = response_dict.get("errorMessage", "Unknown error")
                logger.error("Brand message send failed", extra={"error": error_msg})
                if raise_on_error:
                    raise SolapiKakaoSendError(f"브랜드 메시지 발송 실패: {error_msg}")
                return False

            logger.info(
                "Brand message sent",
                extra={
                    "phone": phone[:3] + "****" if len(phone) > 3 else phone,
                    "template_id": template_id,
                },
            )
            return True

        except SolapiKakaoConfigError:
            raise
        except SolapiKakaoSendError:
            raise
        except Exception as exc:
            logger.error("Brand message send error", exc_info=exc)
            if raise_on_error:
                raise SolapiKakaoSendError(str(exc)) from exc
            return False

    def send_brand_message_by_key(
        self,
        phone: str,
        template_key: str,
        variables: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send Brand Message using a template key from SOLAPI_BRAND_MESSAGE_TEMPLATES.

        Args:
            phone: Recipient phone number.
            template_key: Key in SOLAPI_BRAND_MESSAGE_TEMPLATES dict.
            variables: Template variables.
            **kwargs: Passed to send_brand_message().

        Returns:
            True if sent successfully.
        """
        templates: dict[str, str] = getattr(django_settings, "SOLAPI_BRAND_MESSAGE_TEMPLATES", {})
        template_id = templates.get(template_key, "")
        if not template_id:
            raise SolapiKakaoConfigError(
                f"브랜드 메시지 템플릿 '{template_key}'이(가) "
                "SOLAPI_BRAND_MESSAGE_TEMPLATES에 등록되지 않았습니다."
            )
        return self.send_brand_message(phone, template_id, variables, **kwargs)
