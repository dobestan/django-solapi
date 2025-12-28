from __future__ import annotations

from typing import Any

from django.core.cache import cache as default_cache
from django.core.cache.backends.base import BaseCache
from django.db.models import Model

from .services import SMSService, get_sms_verification_model
from .settings import (
    SOLAPI_VERIFICATION_MAX_ATTEMPTS,
    SOLAPI_VERIFICATION_RATE_LIMIT_COUNT,
    SOLAPI_VERIFICATION_RATE_LIMIT_WINDOW_SECONDS,
)
from .utils import is_valid_phone, normalize_phone


def _is_expired(verification: Any) -> bool:
    """Check if a verification is expired, handling both property and method."""
    value = getattr(verification, "is_expired", False)
    return value() if callable(value) else bool(value)


def get_latest_verification(phone: str) -> Model | None:
    """Get the latest unverified verification for a phone number."""
    model = get_sms_verification_model()
    return (  # type: ignore[no-any-return]
        model.objects.filter(phone=phone, verified_at__isnull=True)  # type: ignore[attr-defined]
        .order_by("-created_at")
        .first()
    )


def check_rate_limit(
    phone: str,
    *,
    cache: BaseCache | None = None,
    key_prefix: str = "solapi_sms_attempt",
    limit: int | None = None,
    window_seconds: int | None = None,
) -> dict[str, Any]:
    """
    Check rate limit for SMS sending.

    Args:
        phone: Phone number to check
        cache: Cache backend to use (defaults to Django's default cache)
        key_prefix: Prefix for cache key
        limit: Maximum attempts allowed
        window_seconds: Time window in seconds

    Returns:
        dict with allowed status and attempt info
    """
    used_cache = cache or default_cache
    effective_limit = limit if limit is not None else SOLAPI_VERIFICATION_RATE_LIMIT_COUNT
    effective_window = (
        window_seconds
        if window_seconds is not None
        else SOLAPI_VERIFICATION_RATE_LIMIT_WINDOW_SECONDS
    )
    if not effective_limit or not effective_window:
        return {"allowed": True, "attempts": 0, "limit": 0, "window_seconds": 0}

    cache_key = f"{key_prefix}_{phone}"
    attempts: int = used_cache.get(cache_key, 0)
    if attempts >= effective_limit:
        return {
            "allowed": False,
            "attempts": attempts,
            "limit": effective_limit,
            "window_seconds": effective_window,
        }
    used_cache.set(cache_key, attempts + 1, effective_window)
    return {
        "allowed": True,
        "attempts": attempts + 1,
        "limit": effective_limit,
        "window_seconds": effective_window,
    }


def send_verification_code(
    phone: str,
    *,
    service: SMSService | None = None,
    code: str | None = None,
    validate_phone: bool = True,
    rate_limit: bool = True,
    cache: BaseCache | None = None,
    rate_limit_key_prefix: str = "solapi_sms_attempt",
) -> dict[str, Any]:
    """
    Send a verification code to a phone number.

    Args:
        phone: Recipient phone number
        service: SMSService instance (optional)
        code: Custom verification code (optional)
        validate_phone: Whether to validate phone format
        rate_limit: Whether to apply rate limiting
        cache: Cache backend for rate limiting
        rate_limit_key_prefix: Prefix for rate limit cache key

    Returns:
        dict with success status and details
    """
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
    success = service.send_verification_code(phone, verification.code)  # type: ignore[attr-defined]
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
) -> dict[str, Any]:
    """
    Verify a code for a phone number.

    Args:
        phone: Phone number to verify
        code: Verification code to check
        service: SMSService instance (optional)
        validate_phone: Whether to validate phone format
        max_attempts: Maximum verification attempts allowed

    Returns:
        dict with success status and details
    """
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

    effective_max_attempts = max_attempts or SOLAPI_VERIFICATION_MAX_ATTEMPTS
    if verification.attempts >= effective_max_attempts:  # type: ignore[attr-defined]
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
        remaining = max(effective_max_attempts - verification.attempts, 0)  # type: ignore[attr-defined]
        if _is_expired(verification):
            error = "expired"
            message = "인증번호가 만료되었습니다. 다시 요청해주세요."
        elif verification.attempts >= effective_max_attempts:  # type: ignore[attr-defined]
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
