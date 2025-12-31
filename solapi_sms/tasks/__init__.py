"""
SMS Task Unified API.

Usage:
    from solapi_sms.tasks import enqueue_sms, enqueue_verification_code

    # Automatically uses the configured backend
    enqueue_sms("01012345678", "Message")
    enqueue_verification_code("01012345678")

Configuration:
    # settings.py
    SOLAPI_TASK_BACKEND = "sync"     # Synchronous execution (default)
    SOLAPI_TASK_BACKEND = "django6"  # Django 6 Tasks
    SOLAPI_TASK_BACKEND = "celery"   # Celery
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from types import ModuleType


def _get_backend_module() -> ModuleType:
    """Return the configured backend module."""
    from ..settings import SOLAPI_TASK_BACKEND

    if SOLAPI_TASK_BACKEND == "django6":
        from .backends import django6

        return django6
    elif SOLAPI_TASK_BACKEND == "celery":
        from .backends import celery

        return celery
    else:  # "sync" or default
        from .backends import sync

        return sync


def enqueue_sms(
    phone: str,
    message: str,
    message_type: str = "GENERIC",
) -> Any:
    """
    Enqueue SMS sending task.

    Uses the configured backend (sync, django6, or celery).

    Args:
        phone: Recipient phone number
        message: Message content
        message_type: Message type (default: "GENERIC")

    Returns:
        Backend-dependent:
        - sync: dict (immediate result)
        - django6: TaskResult
        - celery: AsyncResult
    """
    backend = _get_backend_module()
    return backend.enqueue_sms(phone, message, message_type)


def enqueue_verification_code(phone: str) -> Any:
    """
    Enqueue verification code sending task.

    Uses the configured backend (sync, django6, or celery).

    Args:
        phone: Recipient phone number

    Returns:
        Backend-dependent result
    """
    backend = _get_backend_module()
    return backend.enqueue_verification_code(phone)


def __getattr__(name: str) -> Any:
    """
    Support direct task access for backward compatibility.

    Example:
        from solapi_sms.tasks import send_sms_task
        send_sms_task.delay(...)  # Celery
        send_sms_task.enqueue(...)  # Django 6
    """
    from ..settings import SOLAPI_TASK_BACKEND

    if name in ("send_sms_task", "send_verification_code_task"):
        if SOLAPI_TASK_BACKEND == "celery":
            from .backends import celery

            return getattr(celery, name)
        elif SOLAPI_TASK_BACKEND == "django6":
            from .backends import django6

            return getattr(django6, name)
        else:
            raise AttributeError(
                f"'{name}' is only available with SOLAPI_TASK_BACKEND='celery' or 'django6'. "
                f"Current setting: '{SOLAPI_TASK_BACKEND}'"
            )
    raise AttributeError(f"module 'solapi_sms.tasks' has no attribute '{name}'")


__all__ = [
    "enqueue_sms",
    "enqueue_verification_code",
]
