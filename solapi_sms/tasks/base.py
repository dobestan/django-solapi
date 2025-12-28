"""
Backend-independent task logic (pure functions).

These functions contain the actual business logic and are called by all backends.
"""

from __future__ import annotations

from typing import Any


def send_sms_func(
    phone: str,
    message: str,
    message_type: str = "GENERIC",
) -> dict[str, Any]:
    """
    Send SMS - pure function.

    Args:
        phone: Recipient phone number
        message: Message content
        message_type: Message type (default: "GENERIC")

    Returns:
        dict with 'success' and 'phone' keys
    """
    from ..services import SMSService

    service = SMSService()
    success = service.send_sms(phone, message, message_type=message_type)
    return {"success": success, "phone": phone}


def send_verification_code_func(phone: str) -> dict[str, Any]:
    """
    Send verification code - pure function.

    Args:
        phone: Recipient phone number

    Returns:
        dict with 'success', 'phone', and 'verification_id' keys
    """
    from ..services import SMSService

    service = SMSService()
    verification = service.create_verification(phone)
    success = service.send_verification_code(phone, verification.code)  # type: ignore[attr-defined]
    return {
        "success": success,
        "phone": phone,
        "verification_id": verification.id,  # type: ignore[attr-defined]
    }
