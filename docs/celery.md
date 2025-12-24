# Celery

Celery를 사용하면 SMS 발송을 백그라운드 처리할 수 있습니다.

```python
from solapi_sms.tasks import send_sms_task

send_sms_task.delay("01012345678", "[서비스명] 비동기 SMS")
```

큐 분리:

```python
SOLAPI_CELERY_QUEUE = "sms"
```

```python
from solapi_sms.tasks import enqueue_sms

enqueue_sms("01012345678", "[서비스명] 큐 분리 발송")
```
