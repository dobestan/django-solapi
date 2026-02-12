"""RCS (Rich Communication Services) messaging service.

RCS uses brand_id (telecom-level registration) unlike Kakao's pf_id,
so this is an independent class rather than a BaseKakaoService subclass.
Supports RCS_SMS, RCS_LMS, RCS_MMS, RCS_TPL, RCS_ITPL, RCS_LTPL.
"""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings as django_settings

from .client import SolapiClient
from .exceptions import SolapiRCSConfigError, SolapiRCSSendError
from .settings import (
    SOLAPI_API_KEY,
    SOLAPI_API_SECRET,
    SOLAPI_DEBUG_SKIP,
    SOLAPI_RCS_BRAND_ID,
    SOLAPI_SENDER_PHONE,
)

logger = logging.getLogger(__name__)


class RCSService:
    """SOLAPI RCS service with logging and debug skip support."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        sender: str | None = None,
        brand_id: str | None = None,
    ) -> None:
        self.api_key = api_key or SOLAPI_API_KEY
        self.api_secret = api_secret or SOLAPI_API_SECRET
        self.sender = sender or SOLAPI_SENDER_PHONE
        self.brand_id = brand_id or SOLAPI_RCS_BRAND_ID

    def _validate_config(self) -> None:
        if not all([self.api_key, self.api_secret, self.brand_id]):
            raise SolapiRCSConfigError(
                "SOLAPI RCS 설정이 누락되었습니다. "
                "SOLAPI_API_KEY, SOLAPI_API_SECRET, SOLAPI_RCS_BRAND_ID를 확인하세요."
            )

    @staticmethod
    def _mask_phone(phone: str) -> str:
        return phone[:3] + "****" if len(phone) > 3 else phone

    def send_rcs(
        self,
        phone: str,
        text: str,
        *,
        brand_id: str | None = None,
        template_id: str | None = None,
        variables: dict[str, str] | None = None,
        buttons: list[dict[str, Any]] | None = None,
        disable_sms: bool = False,
        message_type: str = "RCS_SMS",
        mms_type: str | None = None,
        raise_on_error: bool = False,
    ) -> bool:
        """Send RCS message.

        Args:
            phone: Recipient phone number.
            text: Message text (also used as SMS fallback).
            brand_id: Override instance brand_id.
            template_id: RCS template ID (for RCS_TPL/ITPL/LTPL).
            variables: Template variables.
            buttons: RCS button list (button_type, button_name, link, etc.).
            disable_sms: If True, skip SMS fallback when RCS fails.
            message_type: RCS message type (RCS_SMS, RCS_LMS, RCS_MMS, RCS_TPL, RCS_ITPL, RCS_LTPL).
            mms_type: MMS layout type (S3~S6, M3~M6) for RCS_MMS.
            raise_on_error: If True, raise exception on failure.

        Returns:
            True if sent successfully.
        """
        if not phone:
            if raise_on_error:
                raise SolapiRCSSendError("전화번호가 비어있습니다.")
            return False

        if django_settings.DEBUG and SOLAPI_DEBUG_SKIP:
            logger.info(
                "RCS skipped (debug mode)",
                extra={
                    "phone": self._mask_phone(phone),
                    "message_type": message_type,
                    "template_id": template_id or "",
                },
            )
            return True

        try:
            self._validate_config()
            client = SolapiClient(api_key=self.api_key, api_secret=self.api_secret)
            response = client.send_rcs(
                to=phone,
                text=text,
                sender=self.sender,
                brand_id=brand_id or self.brand_id,
                template_id=template_id,
                variables=variables,
                buttons=buttons,
                disable_sms=disable_sms,
                message_type=message_type,
                mms_type=mms_type,
            )
            response_dict = client.serialize_response(response)

            if "errorCode" in response_dict or "errorMessage" in response_dict:
                error_msg = response_dict.get("errorMessage", "Unknown error")
                logger.error("RCS send failed", extra={"error": error_msg})
                if raise_on_error:
                    raise SolapiRCSSendError(f"RCS 발송 실패: {error_msg}")
                return False

            logger.info(
                "RCS sent",
                extra={
                    "phone": self._mask_phone(phone),
                    "message_type": message_type,
                },
            )
            return True

        except SolapiRCSConfigError:
            raise
        except SolapiRCSSendError:
            raise
        except Exception as exc:
            logger.error("RCS send error", exc_info=exc)
            if raise_on_error:
                raise SolapiRCSSendError(str(exc)) from exc
            return False

    def send_rcs_by_key(
        self,
        phone: str,
        template_key: str,
        text: str = "",
        **kwargs: Any,
    ) -> bool:
        """Send RCS using a template key from SOLAPI_RCS_TEMPLATES.

        Args:
            phone: Recipient phone number.
            template_key: Key in SOLAPI_RCS_TEMPLATES dict.
            text: Message text (SMS fallback).
            **kwargs: Passed to send_rcs().

        Returns:
            True if sent successfully.
        """
        templates: dict[str, str] = getattr(django_settings, "SOLAPI_RCS_TEMPLATES", {})
        template_id = templates.get(template_key, "")
        if not template_id:
            raise SolapiRCSConfigError(
                f"RCS 템플릿 '{template_key}'이(가) SOLAPI_RCS_TEMPLATES에 등록되지 않았습니다."
            )
        return self.send_rcs(phone, text, template_id=template_id, **kwargs)
