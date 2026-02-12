from __future__ import annotations

import logging
from typing import Any

from solapi import SolapiMessageService
from solapi.model import RequestMessage
from solapi.model.kakao.kakao_option import KakaoOption

from . import settings

logger = logging.getLogger(__name__)


class SolapiClient:
    """Thin wrapper around SOLAPI SDK."""

    def __init__(self, api_key: str | None = None, api_secret: str | None = None) -> None:
        self.api_key = api_key or settings.SOLAPI_API_KEY
        self.api_secret = api_secret or settings.SOLAPI_API_SECRET
        self._client = SolapiMessageService(api_key=self.api_key, api_secret=self.api_secret)

    def send_message(
        self, to: str, text: str, sender: str | None = None, subject: str | None = None
    ) -> Any:
        message = RequestMessage(
            to=to,
            from_=sender or settings.SOLAPI_SENDER_PHONE,
            text=text,
            subject=subject,
        )
        return self._client.send(message)

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
        return self._client.send(message)

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
        return self._client.send(message)

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
        return self._client.send(message)

    @staticmethod
    def serialize_response(response: Any) -> dict[str, Any]:
        if hasattr(response, "model_dump"):
            return response.model_dump(mode="json")  # type: ignore[no-any-return]
        if isinstance(response, dict):
            return response
        if hasattr(response, "__dict__"):
            return dict(response.__dict__)
        return {"raw_response": str(response)}
