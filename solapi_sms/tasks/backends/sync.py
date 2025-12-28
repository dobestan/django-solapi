"""
Synchronous execution backend (default).

Tasks are executed immediately in the same process.
No worker required.
"""

from __future__ import annotations

from typing import Any

from ..base import send_sms_func, send_verification_code_func


def enqueue_sms(
    phone: str,
    message: str,
    message_type: str = "GENERIC",
) -> dict[str, Any]:
    """
    Execute SMS sending synchronously.

    Args:
        phone: Recipient phone number
        message: Message content
        message_type: Message type (default: "GENERIC")

    Returns:
        dict with execution result
    """
    return send_sms_func(phone, message, message_type)


def enqueue_verification_code(phone: str) -> dict[str, Any]:
    """
    Execute verification code sending synchronously.

    Args:
        phone: Recipient phone number

    Returns:
        dict with execution result
    """
    return send_verification_code_func(phone)
