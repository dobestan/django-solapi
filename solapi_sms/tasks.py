from celery import shared_task

from .services import SMSService
from .settings import SOLAPI_CELERY_QUEUE


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_sms_task(self, phone: str, message: str, message_type: str = "GENERIC"):
    service = SMSService()
    success = service.send_sms(phone, message, message_type=message_type)
    if not success:
        raise self.retry(exc=Exception("SMS 발송 실패"))
    return {"success": True}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_verification_code_task(self, phone: str):
    service = SMSService()
    verification = service.create_verification(phone)
    success = service.send_verification_code(phone, verification.code)
    if not success:
        raise self.retry(exc=Exception("SMS 인증코드 발송 실패"))
    return {"success": True, "verification_id": verification.id}


def enqueue_sms(phone: str, message: str, message_type: str = "GENERIC"):
    kwargs = {"queue": SOLAPI_CELERY_QUEUE} if SOLAPI_CELERY_QUEUE else {}
    return send_sms_task.apply_async(args=[phone, message, message_type], **kwargs)


def enqueue_verification_code(phone: str):
    kwargs = {"queue": SOLAPI_CELERY_QUEUE} if SOLAPI_CELERY_QUEUE else {}
    return send_verification_code_task.apply_async(args=[phone], **kwargs)
