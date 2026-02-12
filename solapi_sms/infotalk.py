"""Kakao Infotalk (알림톡) service with logging and debug skip."""

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


class InfotalkService:
    """SOLAPI Infotalk service with logging and debug skip support."""

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
                "SOLAPI Infotalk 설정이 누락되었습니다. "
                "SOLAPI_API_KEY, SOLAPI_API_SECRET, SOLAPI_KAKAO_PF_ID를 확인하세요."
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
        if not phone:
            if raise_on_error:
                raise SolapiKakaoSendError("전화번호가 비어있습니다.")
            return False

        if django_settings.DEBUG and SOLAPI_DEBUG_SKIP:
            logger.info(
                "Infotalk skipped (debug mode)",
                extra={
                    "phone": phone[:3] + "****" if len(phone) > 3 else phone,
                    "template_id": template_id,
                },
            )
            return True

        try:
            self._validate_config()
            client = SolapiClient(api_key=self.api_key, api_secret=self.api_secret)
            response = client.send_infotalk(
                to=phone,
                template_id=template_id,
                pf_id=self.pf_id,
                variables=variables,
                sender=self.sender,
                disable_sms=disable_sms,
                fallback_text=fallback_text,
            )
            response_dict = client.serialize_response(response)

            if "errorCode" in response_dict or "errorMessage" in response_dict:
                error_msg = response_dict.get("errorMessage", "Unknown error")
                logger.error("Infotalk send failed", extra={"error": error_msg})
                if raise_on_error:
                    raise SolapiKakaoSendError(f"알림톡 발송 실패: {error_msg}")
                return False

            logger.info(
                "Infotalk sent",
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
            logger.error("Infotalk send error", exc_info=exc)
            if raise_on_error:
                raise SolapiKakaoSendError(str(exc)) from exc
            return False

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
        templates: dict[str, str] = getattr(django_settings, "SOLAPI_INFOTALK_TEMPLATES", {})
        template_id = templates.get(template_key, "")
        if not template_id:
            raise SolapiKakaoConfigError(
                f"알림톡 템플릿 '{template_key}'이(가) SOLAPI_INFOTALK_TEMPLATES에 등록되지 않았습니다."
            )
        return self.send_infotalk(phone, template_id, variables, **kwargs)
