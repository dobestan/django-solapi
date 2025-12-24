from django.dispatch import Signal

sms_sent = Signal()
sms_failed = Signal()
verification_created = Signal()
verification_verified = Signal()
