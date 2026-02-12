"""Base class for Kakao messaging services (Infotalk, Brand Message).

Extracts shared logic: config validation, debug skip, error checking,
phone masking, and template key lookup.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, ClassVar

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


class BaseKakaoService(ABC):
    """Abstract base for Kakao messaging services.

    Subclasses must define class variables and implement _call_client().
    """

    service_name: ClassVar[str]
    error_prefix: ClassVar[str]
    template_settings_key: ClassVar[str]

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
                f"SOLAPI {self.service_name} 설정이 누락되었습니다. "
                "SOLAPI_API_KEY, SOLAPI_API_SECRET, SOLAPI_KAKAO_PF_ID를 확인하세요."
            )

    @staticmethod
    def _mask_phone(phone: str) -> str:
        return phone[:3] + "****" if len(phone) > 3 else phone

    @abstractmethod
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
        """Call the appropriate SolapiClient method. Subclasses implement this."""
        ...

    def _send(
        self,
        phone: str,
        template_id: str,
        variables: dict[str, str] | None = None,
        *,
        disable_sms: bool = False,
        fallback_text: str | None = None,
        raise_on_error: bool = False,
        **extra_kwargs: Any,
    ) -> bool:
        """Core send logic shared by all Kakao services."""
        if not phone:
            if raise_on_error:
                raise SolapiKakaoSendError("전화번호가 비어있습니다.")
            return False

        if django_settings.DEBUG and SOLAPI_DEBUG_SKIP:
            logger.info(
                f"{self.service_name} skipped (debug mode)",
                extra={
                    "phone": self._mask_phone(phone),
                    "template_id": template_id,
                },
            )
            return True

        try:
            self._validate_config()
            client = SolapiClient(api_key=self.api_key, api_secret=self.api_secret)
            response = self._call_client(
                client,
                phone,
                template_id,
                variables,
                disable_sms=disable_sms,
                fallback_text=fallback_text,
                **extra_kwargs,
            )
            response_dict = client.serialize_response(response)

            if "errorCode" in response_dict or "errorMessage" in response_dict:
                error_msg = response_dict.get("errorMessage", "Unknown error")
                logger.error(f"{self.service_name} send failed", extra={"error": error_msg})
                if raise_on_error:
                    raise SolapiKakaoSendError(f"{self.error_prefix}: {error_msg}")
                return False

            logger.info(
                f"{self.service_name} sent",
                extra={
                    "phone": self._mask_phone(phone),
                    "template_id": template_id,
                },
            )
            return True

        except SolapiKakaoConfigError:
            raise
        except SolapiKakaoSendError:
            raise
        except Exception as exc:
            logger.error(f"{self.service_name} send error", exc_info=exc)
            if raise_on_error:
                raise SolapiKakaoSendError(str(exc)) from exc
            return False

    def _send_by_key(
        self,
        phone: str,
        template_key: str,
        variables: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send using a template key from Django settings."""
        templates: dict[str, str] = getattr(django_settings, self.template_settings_key, {})
        template_id = templates.get(template_key, "")
        if not template_id:
            raise SolapiKakaoConfigError(
                f"{self.service_name} 템플릿 '{template_key}'이(가) "
                f"{self.template_settings_key}에 등록되지 않았습니다."
            )
        return self._send(phone, template_id, variables, **kwargs)
