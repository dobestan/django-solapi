from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from django.apps import apps as django_apps
from django.conf import settings as django_settings

from .client import SolapiClient

if TYPE_CHECKING:
    from django.db.models import Model
from .exceptions import SolapiSMSConfigError, SolapiSMSSendError
from .models import SMSLog, SMSLogStatus, SMSMessageType, SMSVerificationCode
from .settings import (
    SOLAPI_API_KEY,
    SOLAPI_API_SECRET,
    SOLAPI_APP_NAME,
    SOLAPI_DEBUG_SKIP,
    SOLAPI_LOG_SKIPPED,
    SOLAPI_SENDER_PHONE,
    SOLAPI_SUCCESS_STATUS_CODES,
    SOLAPI_TEMPLATES,
    SOLAPI_TEST_CREDENTIALS,
    SOLAPI_VERIFICATION_MAX_ATTEMPTS,
    SOLAPI_VERIFICATION_TTL_SECONDS,
)
from .utils import build_message, generate_verification_code, normalize_phone

logger = logging.getLogger(__name__)


def get_sms_log_model() -> type[Model]:
    """Return the configured SMS log model class."""
    model_path: str | None = getattr(django_settings, "SOLAPI_SMS_LOG_MODEL", None)
    if model_path:
        return django_apps.get_model(model_path)
    return SMSLog


def get_sms_verification_model() -> type[Model]:
    """Return the configured SMS verification model class."""
    model_path: str | None = getattr(django_settings, "SOLAPI_SMS_VERIFICATION_MODEL", None)
    if model_path:
        return django_apps.get_model(model_path)
    return SMSVerificationCode


class SMSService:
    """SOLAPI SMS service with logging and verification helpers."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        sender: str | None = None,
        app_name: str | None = None,
    ) -> None:
        self.api_key = api_key or SOLAPI_API_KEY
        self.api_secret = api_secret or SOLAPI_API_SECRET
        self.sender = sender or SOLAPI_SENDER_PHONE
        self.app_name = app_name or SOLAPI_APP_NAME

    def _validate_config(self) -> None:
        if not all([self.api_key, self.api_secret, self.sender]):
            raise SolapiSMSConfigError("SOLAPI 설정이 누락되었습니다.")

    def _serialize_response(self, response: Any) -> dict[str, Any]:
        return SolapiClient.serialize_response(response)

    def _is_success(self, response_dict: dict[str, Any]) -> bool:
        if "errorCode" in response_dict or "errorMessage" in response_dict:
            return False
        status_code = response_dict.get("statusCode")
        if status_code and status_code not in SOLAPI_SUCCESS_STATUS_CODES:
            return False
        return True

    def _log_result(
        self,
        phone: str,
        message: str,
        message_type: str,
        status: str,
        response_data: dict[str, Any] | None = None,
        error_message: str = "",
    ) -> Model | None:
        from .settings import SOLAPI_LOG_ENABLED

        if not SOLAPI_LOG_ENABLED:
            return None

        model = get_sms_log_model()
        return model.objects.create(  # type: ignore[attr-defined, no-any-return]
            phone=phone,
            message=message,
            message_type=message_type,
            status=status,
            response_data=response_data or {},
            error_message=error_message,
        )

    def send_sms(
        self,
        phone: str,
        message: str,
        message_type: str = SMSMessageType.GENERIC,
        raise_on_error: bool = False,
    ) -> bool:
        phone = normalize_phone(phone)
        if not phone:
            if raise_on_error:
                raise SolapiSMSSendError("전화번호가 비어있습니다.")
            return False

        if (
            django_settings.DEBUG
            and SOLAPI_DEBUG_SKIP
            and not all([self.api_key, self.api_secret, self.sender])
        ):
            log_entry: Model | None = None
            if SOLAPI_LOG_SKIPPED:
                log_entry = self._log_result(
                    phone=phone,
                    message=message,
                    message_type=message_type,
                    status=SMSLogStatus.SKIPPED,
                    response_data={"debug_skip": True},
                )
            from .signals import sms_sent

            sms_sent.send(
                sender=self.__class__,
                phone=phone,
                message=message,
                message_type=message_type,
                log=log_entry,
                skipped=True,
            )
            return True

        try:
            self._validate_config()
            client = SolapiClient(api_key=self.api_key, api_secret=self.api_secret)
            response = client.send_message(phone, message, sender=self.sender)
            response_dict = self._serialize_response(response)

            if not self._is_success(response_dict):
                log_entry = self._log_result(
                    phone=phone,
                    message=message,
                    message_type=message_type,
                    status=SMSLogStatus.FAILED,
                    response_data=response_dict,
                    error_message=response_dict.get("errorMessage", ""),
                )
                from .signals import sms_failed

                sms_failed.send(
                    sender=self.__class__,
                    phone=phone,
                    message=message,
                    message_type=message_type,
                    log=log_entry,
                )
                if raise_on_error:
                    raise SolapiSMSSendError("SOLAPI 발송 실패")
                return False

            log_entry = self._log_result(
                phone=phone,
                message=message,
                message_type=message_type,
                status=SMSLogStatus.SUCCESS,
                response_data=response_dict,
            )
            from .signals import sms_sent

            sms_sent.send(
                sender=self.__class__,
                phone=phone,
                message=message,
                message_type=message_type,
                log=log_entry,
                skipped=False,
            )
            return True
        except Exception as exc:
            logger.error("SOLAPI send failed", exc_info=exc)
            log_entry = self._log_result(
                phone=phone,
                message=message,
                message_type=message_type,
                status=SMSLogStatus.FAILED,
                response_data={"error": str(exc)},
                error_message=str(exc),
            )
            from .signals import sms_failed

            sms_failed.send(
                sender=self.__class__,
                phone=phone,
                message=message,
                message_type=message_type,
                log=log_entry,
            )
            if raise_on_error:
                raise SolapiSMSSendError(str(exc)) from exc
            return False

    def send_templated(
        self,
        phone: str,
        template_key: str,
        message_type: str,
        **kwargs: object,
    ) -> bool:
        template = SOLAPI_TEMPLATES.get(template_key, "")
        message = build_message(template, app_name=self.app_name, **kwargs)
        return self.send_sms(phone, message, message_type=message_type)

    def create_verification(self, phone: str, code: str | None = None) -> Model:
        phone = normalize_phone(phone)
        code = code or generate_verification_code()
        model = get_sms_verification_model()
        verification = model.create_verification(  # type: ignore[attr-defined]
            phone, code, SOLAPI_VERIFICATION_TTL_SECONDS
        )
        from .signals import verification_created

        verification_created.send(
            sender=self.__class__,
            verification=verification,
        )
        return verification  # type: ignore[no-any-return]

    def send_verification_code(self, phone: str, code: str) -> bool:
        expires_minutes = max(1, SOLAPI_VERIFICATION_TTL_SECONDS // 60)
        return self.send_templated(
            phone,
            template_key="verification",
            message_type=SMSMessageType.VERIFICATION,
            code=code,
            expires_minutes=expires_minutes,
        )

    def verify_code(self, phone: str, code: str) -> bool:
        phone = normalize_phone(phone)

        # Test mode: bypass verification for configured test credentials
        if SOLAPI_TEST_CREDENTIALS and phone in SOLAPI_TEST_CREDENTIALS:
            if SOLAPI_TEST_CREDENTIALS[phone] == code:
                logger.info("Test credentials used for phone: %s", phone)
                return True

        model = get_sms_verification_model()
        verification = (
            model.objects.filter(phone=phone, verified_at__isnull=True)  # type: ignore[attr-defined]
            .order_by("-created_at")
            .first()
        )
        if not verification:
            return False
        is_expired = getattr(verification, "is_expired", False)
        if callable(is_expired):
            is_expired = is_expired()
        if is_expired:
            return False
        if verification.attempts >= SOLAPI_VERIFICATION_MAX_ATTEMPTS:
            return False

        verification.mark_attempt()
        if verification.code != code:
            return False

        verification.mark_verified()
        from .signals import verification_verified

        verification_verified.send(
            sender=self.__class__,
            verification=verification,
        )
        return True
