"""
Celery backend.

Uses Celery for distributed task processing.
Maintains backward compatibility with existing Celery-based deployments.
"""

from __future__ import annotations

from typing import Any, NoReturn

# Check if Celery is available
try:
    from celery import shared_task  # type: ignore[import-not-found]

    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    shared_task = None


if CELERY_AVAILABLE:
    from ...settings import SOLAPI_CELERY_QUEUE
    from ..base import send_sms_func, send_verification_code_func

    @shared_task(bind=True, max_retries=3, default_retry_delay=60)
    def send_sms_task(
        self: Any,
        phone: str,
        message: str,
        message_type: str = "GENERIC",
    ) -> dict[str, Any]:
        """
        SMS sending Celery task.

        Args:
            self: Celery task instance (bound)
            phone: Recipient phone number
            message: Message content
            message_type: Message type (default: "GENERIC")

        Returns:
            dict with execution result

        Raises:
            Retry: If sending fails (up to 3 retries)
        """
        result = send_sms_func(phone, message, message_type)
        if not result["success"]:
            raise self.retry(exc=Exception("SMS sending failed"))
        return result

    @shared_task(bind=True, max_retries=3, default_retry_delay=60)
    def send_verification_code_task(self: Any, phone: str) -> dict[str, Any]:
        """
        Verification code sending Celery task.

        Args:
            self: Celery task instance (bound)
            phone: Recipient phone number

        Returns:
            dict with execution result

        Raises:
            Retry: If sending fails (up to 3 retries)
        """
        result = send_verification_code_func(phone)
        if not result["success"]:
            raise self.retry(exc=Exception("Verification code sending failed"))
        return result

    def enqueue_sms(
        phone: str,
        message: str,
        message_type: str = "GENERIC",
    ) -> Any:
        """
        Enqueue SMS sending to Celery.

        Args:
            phone: Recipient phone number
            message: Message content
            message_type: Message type (default: "GENERIC")

        Returns:
            Celery AsyncResult
        """
        kwargs: dict[str, Any] = {}
        if SOLAPI_CELERY_QUEUE:
            kwargs["queue"] = SOLAPI_CELERY_QUEUE
        return send_sms_task.apply_async(
            args=[phone, message, message_type],
            **kwargs,
        )

    def enqueue_verification_code(phone: str) -> Any:
        """
        Enqueue verification code sending to Celery.

        Args:
            phone: Recipient phone number

        Returns:
            Celery AsyncResult
        """
        kwargs: dict[str, Any] = {}
        if SOLAPI_CELERY_QUEUE:
            kwargs["queue"] = SOLAPI_CELERY_QUEUE
        return send_verification_code_task.apply_async(
            args=[phone],
            **kwargs,
        )

else:
    # Fallback when Celery is not available

    def send_sms_task(
        self: Any,
        phone: str,
        message: str,
        message_type: str = "GENERIC",
    ) -> NoReturn:
        raise ImportError(
            "Celery is required. Install celery package or set SOLAPI_TASK_BACKEND='sync'."
        )

    def send_verification_code_task(self: Any, phone: str) -> NoReturn:
        raise ImportError(
            "Celery is required. Install celery package or set SOLAPI_TASK_BACKEND='sync'."
        )

    def enqueue_sms(  # type: ignore[misc]
        phone: str,
        message: str,
        message_type: str = "GENERIC",
    ) -> NoReturn:
        raise ImportError(
            "Celery is required. Install celery package or set SOLAPI_TASK_BACKEND='sync'."
        )

    def enqueue_verification_code(phone: str) -> NoReturn:  # type: ignore[misc]
        raise ImportError(
            "Celery is required. Install celery package or set SOLAPI_TASK_BACKEND='sync'."
        )
