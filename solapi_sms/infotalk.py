"""Kakao Infotalk (알림톡) service.

Thin subclass of BaseKakaoService — only implements the SDK call.
"""

from __future__ import annotations

from typing import Any, ClassVar

from .client import SolapiClient
from .kakao_base import BaseKakaoService


class InfotalkService(BaseKakaoService):
    """SOLAPI Infotalk service with logging and debug skip support."""

    service_name: ClassVar[str] = "Infotalk"
    error_prefix: ClassVar[str] = "알림톡 발송 실패"
    template_settings_key: ClassVar[str] = "SOLAPI_INFOTALK_TEMPLATES"

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
        return client.send_infotalk(
            to=phone,
            template_id=template_id,
            pf_id=self.pf_id,
            variables=variables,
            sender=self.sender,
            disable_sms=disable_sms,
            fallback_text=fallback_text,
        )

    def send_infotalk(
        self,
        phone: str,
        template_id: str,
        variables: dict[str, str] | None = None,
        *,
        disable_sms: bool = False,
        fallback_text: str | None = None,
        raise_on_error: bool = False,
    ) -> bool:
        """Send Infotalk message.

        Args:
            phone: Recipient phone number.
            template_id: Kakao-approved template ID.
            variables: Template variables (auto-wrapped with #{} by SDK).
            disable_sms: If True, skip SMS fallback on Infotalk failure.
            fallback_text: SMS fallback text (used when Infotalk fails).
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
        )

    def send_infotalk_by_key(
        self,
        phone: str,
        template_key: str,
        variables: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send Infotalk using a template key from SOLAPI_INFOTALK_TEMPLATES.

        Args:
            phone: Recipient phone number.
            template_key: Key in SOLAPI_INFOTALK_TEMPLATES dict.
            variables: Template variables.
            **kwargs: Passed to send_infotalk().

        Returns:
            True if sent successfully.
        """
        return self._send_by_key(phone, template_key, variables, **kwargs)
