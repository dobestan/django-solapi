from __future__ import annotations

from typing import Any

from django.core.cache import cache as default_cache

from .services import SMSService, get_sms_verification_model
from .settings import (
    SOLAPI_VERIFICATION_MAX_ATTEMPTS,
    SOLAPI_VERIFICATION_RATE_LIMIT_COUNT,
    SOLAPI_VERIFICATION_RATE_LIMIT_WINDOW_SECONDS,
)
from .utils import is_valid_phone, normalize_phone


def _is_expired(verification: Any) -> bool:
    value = getattr(verification, "is_expired", False)
    return value() if callable(value) else bool(value)


def get_latest_verification(phone: str):
    model = get_sms_verification_model()
    return (
        model.objects.filter(phone=phone, verified_at__isnull=True)
        .order_by("-created_at")
        .first()
    )


def check_rate_limit(
    phone: str,
    *,
    cache=None,
    key_prefix: str = "solapi_sms_attempt",
    limit: int | None = None,
    window_seconds: int | None = None,
) -> dict:
    cache = cache or default_cache
    limit = limit if limit is not None else SOLAPI_VERIFICATION_RATE_LIMIT_COUNT
    window_seconds = (
        window_seconds
        if window_seconds is not None
        else SOLAPI_VERIFICATION_RATE_LIMIT_WINDOW_SECONDS
    )
    if not limit or not window_seconds:
        return {"allowed": True, "attempts": 0, "limit": 0, "window_seconds": 0}

    cache_key = f"{key_prefix}_{phone}"
    attempts = cache.get(cache_key, 0)
    if attempts >= limit:
        return {
            "allowed": False,
            "attempts": attempts,
            "limit": limit,
            "window_seconds": window_seconds,
        }
    cache.set(cache_key, attempts + 1, window_seconds)
    return {
        "allowed": True,
        "attempts": attempts + 1,
        "limit": limit,
        "window_seconds": window_seconds,
    }


def send_verification_code(
    phone: str,
    *,
    service: SMSService | None = None,
    code: str | None = None,
    validate_phone: bool = True,
    rate_limit: bool = True,
    cache=None,
    rate_limit_key_prefix: str = "solapi_sms_attempt",
) -> dict:
    phone = normalize_phone(phone)
    if validate_phone and not is_valid_phone(phone):
        return {
            "success": False,
            "error": "invalid_phone",
            "message": "올바른 휴대폰 번호를 입력해주세요.",
            "phone": phone,
        }

    if rate_limit:
        rate = check_rate_limit(
            phone,
            cache=cache,
            key_prefix=rate_limit_key_prefix,
        )
        if not rate["allowed"]:
            return {
                "success": False,
                "error": "rate_limited",
                "message": "너무 많은 시도입니다. 잠시 후 다시 시도해주세요.",
                "phone": phone,
                "rate_limit": rate,
            }

    service = service or SMSService()
    verification = service.create_verification(phone, code=code)
    success = service.send_verification_code(phone, verification.code)
    if not success:
        return {
            "success": False,
            "error": "send_failed",
            "message": "SMS 발송에 실패했습니다. 다시 시도해주세요.",
            "phone": phone,
            "verification": verification,
        }

    return {
        "success": True,
        "phone": phone,
        "verification": verification,
    }


def verify_code(
    phone: str,
    code: str,
    *,
    service: SMSService | None = None,
    validate_phone: bool = True,
    max_attempts: int | None = None,
) -> dict:
    phone = normalize_phone(phone)
    if validate_phone and not is_valid_phone(phone):
        return {
            "success": False,
            "error": "invalid_phone",
            "message": "올바른 휴대폰 번호를 입력해주세요.",
            "phone": phone,
        }
    if not code:
        return {
            "success": False,
            "error": "missing_code",
            "message": "인증번호를 입력해주세요.",
            "phone": phone,
        }

    verification = get_latest_verification(phone)
    if not verification:
        return {
            "success": False,
            "error": "missing_verification",
            "message": "인증 요청을 먼저 진행해주세요.",
            "phone": phone,
        }

    if _is_expired(verification):
        return {
            "success": False,
            "error": "expired",
            "message": "인증번호가 만료되었습니다. 다시 요청해주세요.",
            "phone": phone,
            "verification": verification,
        }

    max_attempts = max_attempts or SOLAPI_VERIFICATION_MAX_ATTEMPTS
    if verification.attempts >= max_attempts:
        return {
            "success": False,
            "error": "max_attempts",
            "message": "인증 시도 횟수를 초과했습니다. 다시 요청해주세요.",
            "phone": phone,
            "verification": verification,
        }

    service = service or SMSService()
    if not service.verify_code(phone, code):
        verification.refresh_from_db()
        remaining = max(max_attempts - verification.attempts, 0)
        if _is_expired(verification):
            error = "expired"
            message = "인증번호가 만료되었습니다. 다시 요청해주세요."
        elif verification.attempts >= max_attempts:
            error = "max_attempts"
            message = "인증 시도 횟수를 초과했습니다. 다시 요청해주세요."
        else:
            error = "invalid_code"
            message = "인증번호가 올바르지 않습니다."
        return {
            "success": False,
            "error": error,
            "message": message,
            "phone": phone,
            "verification": verification,
            "remaining_attempts": remaining,
        }

    verification.refresh_from_db()
    return {
        "success": True,
        "phone": phone,
        "verification": verification,
    }
