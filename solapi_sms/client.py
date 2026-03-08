from __future__ import annotations

import logging
import ssl
import time
from typing import Any
from urllib.error import URLError

import httpx
from solapi import SolapiMessageService
from solapi.model import RequestMessage
from solapi.model.kakao.kakao_option import KakaoOption

from . import settings

logger = logging.getLogger(__name__)

# Errors that indicate a transient failure (worth retrying).
_RETRYABLE_EXCEPTIONS: tuple[type[BaseException], ...] = (
    TimeoutError,
    ConnectionError,
    OSError,
    ssl.SSLError,
    URLError,
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
)

# SOLAPI SDK error codes that are NOT retryable (client errors).
_NON_RETRYABLE_ERROR_CODES: frozenset[str] = frozenset(
    {
        "ValidationError",
        "InvalidParameter",
        "Unauthorized",
        "Forbidden",
        "InvalidApiKey",
        "NotEnoughBalance",
        "InvalidPhoneNumber",
    }
)


def _is_retryable(exc: BaseException) -> bool:
    """Return True if the exception is transient and worth retrying."""
    # Known transient exception types
    if isinstance(exc, _RETRYABLE_EXCEPTIONS):
        return True
    # SOLAPI SDK raises generic Exception(errorCode, errorMessage) for HTTP errors.
    # 5xx errors use errorCode="UnknownError" — retryable.
    # 4xx errors use specific codes — NOT retryable.
    if isinstance(exc, Exception) and exc.args:
        error_code = str(exc.args[0])
        if error_code in _NON_RETRYABLE_ERROR_CODES:
            return False
        # "UnknownError" from 5xx or unrecognized codes — retry
        if error_code == "UnknownError":
            return True
    return False


class SolapiClient:
    """Thin wrapper around SOLAPI SDK with retry support."""

    def __init__(self, api_key: str | None = None, api_secret: str | None = None) -> None:
        self.api_key = api_key or settings.SOLAPI_API_KEY
        self.api_secret = api_secret or settings.SOLAPI_API_SECRET
        self._client = SolapiMessageService(api_key=self.api_key, api_secret=self.api_secret)

    def _send_with_retry(self, message: RequestMessage) -> Any:
        """Send a message with exponential backoff on transient failures.

        Retry schedule: 1s → 2s → 4s (max 3 retries).
        Non-retryable errors (auth failure, invalid phone, etc.) fail immediately.
        """
        max_retries: int = settings.SOLAPI_RETRY_MAX_ATTEMPTS
        base_delay: float = settings.SOLAPI_RETRY_BASE_DELAY

        last_exc: BaseException | None = None
        for attempt in range(max_retries + 1):
            try:
                return self._client.send(message)
            except Exception as exc:
                last_exc = exc
                if not _is_retryable(exc) or attempt >= max_retries:
                    raise
                delay = base_delay * (2**attempt)
                logger.warning(
                    "SOLAPI send failed (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    max_retries + 1,
                    delay,
                    exc_info=exc,
                )
                time.sleep(delay)

        # Should not reach here, but satisfy type checker
        if last_exc is not None:
            raise last_exc  # pragma: no cover
        raise RuntimeError("Unexpected retry loop exit")  # pragma: no cover

    def send_message(
        self, to: str, text: str, sender: str | None = None, subject: str | None = None
    ) -> Any:
        message = RequestMessage(
            to=to,
            from_=sender or settings.SOLAPI_SENDER_PHONE,
            text=text,
            subject=subject,
        )
        return self._send_with_retry(message)

    def send_infotalk(
        self,
        to: str,
        template_id: str,
        pf_id: str,
        variables: dict[str, str] | None = None,
        *,
        sender: str | None = None,
        disable_sms: bool = False,
        fallback_text: str | None = None,
    ) -> Any:
        """Send Infotalk (카카오 알림톡) message.

        SOLAPI handles SMS fallback server-side when disable_sms=False.
        """
        kakao_option = KakaoOption(
            pf_id=pf_id,
            template_id=template_id,
            variables=variables or {},
            disable_sms=disable_sms,
        )
        message = RequestMessage(
            to=to,
            from_=sender or settings.SOLAPI_SENDER_PHONE,
            kakao_options=kakao_option,
            text=fallback_text,
        )
        return self._send_with_retry(message)

    def send_brand_message(
        self,
        to: str,
        template_id: str,
        pf_id: str,
        variables: dict[str, str] | None = None,
        *,
        sender: str | None = None,
        disable_sms: bool = False,
        fallback_text: str | None = None,
        buttons: list[dict[str, str]] | None = None,
        image_id: str | None = None,
        targeting: str = "M",
    ) -> Any:
        """Send Brand Message (카카오 브랜드 메시지, 친구톡 대체).

        Args:
            targeting: Bms targeting type ("M"=mobile, "N"=naver, "I"=image).
        """
        from solapi.model.request.kakao.bms import Bms

        kakao_option = KakaoOption(
            pf_id=pf_id,
            template_id=template_id,
            variables=variables or {},
            disable_sms=disable_sms,
            image_id=image_id,
            bms=Bms(targeting=targeting),
        )
        # Add buttons if provided
        if buttons:
            from solapi.model.kakao.kakao_button import KakaoButton

            kakao_option.buttons = [KakaoButton(**btn) for btn in buttons]
        message = RequestMessage(
            to=to,
            from_=sender or settings.SOLAPI_SENDER_PHONE,
            kakao_options=kakao_option,
            text=fallback_text,
        )
        return self._send_with_retry(message)

    def send_rcs(
        self,
        to: str,
        text: str,
        *,
        sender: str | None = None,
        brand_id: str | None = None,
        template_id: str | None = None,
        variables: dict[str, str] | None = None,
        buttons: list[dict[str, Any]] | None = None,
        disable_sms: bool = False,
        message_type: str = "RCS_SMS",
        mms_type: str | None = None,
    ) -> Any:
        """Send RCS message.

        Supports RCS_SMS, RCS_LMS, RCS_MMS, RCS_TPL, RCS_ITPL, RCS_LTPL.
        Falls back to SMS when disable_sms=False (default).
        """
        from solapi.model.message_type import MessageType
        from solapi.model.rcs.rcs_options import RcsOption

        rcs_kwargs: dict[str, Any] = {
            "brand_id": brand_id,
            "disable_sms": disable_sms,
        }
        if template_id:
            rcs_kwargs["template_id"] = template_id
        if variables:
            rcs_kwargs["variables"] = variables
        if mms_type:
            from solapi.model.rcs.rcs_options import RcsMmsType

            rcs_kwargs["mms_type"] = RcsMmsType(mms_type)
        if buttons:
            from solapi.model.rcs.rcs_options import RcsButton

            rcs_kwargs["buttons"] = [RcsButton(**btn) for btn in buttons]

        rcs_option = RcsOption(**rcs_kwargs)
        message = RequestMessage(
            to=to,
            from_=sender or settings.SOLAPI_SENDER_PHONE,
            text=text,
            rcs_options=rcs_option,
            type=MessageType(message_type),
        )
        return self._send_with_retry(message)

    @staticmethod
    def serialize_response(response: Any) -> dict[str, Any]:
        if hasattr(response, "model_dump"):
            return response.model_dump(mode="json")  # type: ignore[no-any-return]
        if isinstance(response, dict):
            return response
        if hasattr(response, "__dict__"):
            return dict(response.__dict__)
        return {"raw_response": str(response)}
