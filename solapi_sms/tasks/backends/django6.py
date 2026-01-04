"""
Django 6 Tasks backend.

Uses Django's built-in Tasks framework (Django 6.0+).
Requires a configured TASKS backend in settings.
"""

from __future__ import annotations

from typing import Any, NoReturn

# Check if Django 6 Tasks is available
try:
    from django.tasks import task

    DJANGO_TASKS_AVAILABLE = True
except ImportError:
    DJANGO_TASKS_AVAILABLE = False
    task = None


if DJANGO_TASKS_AVAILABLE:
    from ..base import send_sms_func, send_verification_code_func

    @task
    def send_sms_task(
        phone: str,
        message: str,
        message_type: str = "GENERIC",
    ) -> dict[str, Any]:
        """
        SMS sending task for Django 6 Tasks.

        Args:
            phone: Recipient phone number
            message: Message content
            message_type: Message type (default: "GENERIC")

        Returns:
            dict with execution result
        """
        return send_sms_func(phone, message, message_type)

    @task
    def send_verification_code_task(phone: str) -> dict[str, Any]:
        """
        Verification code sending task for Django 6 Tasks.

        Args:
            phone: Recipient phone number

        Returns:
            dict with execution result
        """
        return send_verification_code_func(phone)

    def enqueue_sms(
        phone: str,
        message: str,
        message_type: str = "GENERIC",
    ) -> Any:
        """
        Enqueue SMS sending task.

        Args:
            phone: Recipient phone number
            message: Message content
            message_type: Message type (default: "GENERIC")

        Returns:
            TaskResult from Django Tasks
        """
        return send_sms_task.enqueue(
            phone=phone,
            message=message,
            message_type=message_type,
        )

    def enqueue_verification_code(phone: str) -> Any:
        """
        Enqueue verification code sending task.

        Args:
            phone: Recipient phone number

        Returns:
            TaskResult from Django Tasks
        """
        return send_verification_code_task.enqueue(phone=phone)

else:
    # Fallback when Django 6 Tasks is not available

    def send_sms_task(
        phone: str,
        message: str,
        message_type: str = "GENERIC",
    ) -> NoReturn:
        raise ImportError(
            "Django 6 Tasks is required. Use Django 6+ or set SOLAPI_TASK_BACKEND='sync'."
        )

    def send_verification_code_task(phone: str) -> NoReturn:
        raise ImportError(
            "Django 6 Tasks is required. Use Django 6+ or set SOLAPI_TASK_BACKEND='sync'."
        )

    def enqueue_sms(  # type: ignore[misc]
        phone: str,
        message: str,
        message_type: str = "GENERIC",
    ) -> NoReturn:
        raise ImportError(
            "Django 6 Tasks is required. Use Django 6+ or set SOLAPI_TASK_BACKEND='sync'."
        )

    def enqueue_verification_code(phone: str) -> NoReturn:  # type: ignore[misc]
        raise ImportError(
            "Django 6 Tasks is required. Use Django 6+ or set SOLAPI_TASK_BACKEND='sync'."
        )
