"""Kakao Brand Message (브랜드 메시지) service.

Brand Messages replaced FriendTalk (친구톡) from 2026.1.1.
Used for marketing/advertising messages (53~103원/건).

Thin subclass of BaseKakaoService — only implements the SDK call
with extra parameters (buttons, image_id, targeting).
"""

from __future__ import annotations

from typing import Any, ClassVar

from .client import SolapiClient
from .kakao_base import BaseKakaoService


class BrandMessageService(BaseKakaoService):
    """SOLAPI Brand Message service with logging and debug skip support."""

    service_name: ClassVar[str] = "Brand message"
    error_prefix: ClassVar[str] = "브랜드 메시지 발송 실패"
    template_settings_key: ClassVar[str] = "SOLAPI_BRAND_MESSAGE_TEMPLATES"

    def _call_client(
        self,
        client: SolapiClient,
        phone: str,
        template_id: str,
        variables: dict[str, str] | None,
        *,
        disable_sms: bool,
        fallback_text: str | None,
        **extra_kwargs: Any,
    ) -> Any:
        return client.send_brand_message(
            to=phone,
            template_id=template_id,
            pf_id=self.pf_id,
            variables=variables,
            sender=self.sender,
            disable_sms=disable_sms,
            fallback_text=fallback_text,
            buttons=extra_kwargs.get("buttons"),
            image_id=extra_kwargs.get("image_id"),
            targeting=extra_kwargs.get("targeting", "M"),
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
        return self._send(
            phone,
            template_id,
            variables,
            disable_sms=disable_sms,
            fallback_text=fallback_text,
            raise_on_error=raise_on_error,
            buttons=buttons,
            image_id=image_id,
            targeting=targeting,
        )

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
        return self._send_by_key(phone, template_key, variables, **kwargs)
