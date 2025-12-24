# Models

기본 모델은 `SMSLog`, `SMSVerificationCode`이며 확장 가능한 추상 모델을 제공합니다.

## 기본 모델 사용

```python
from solapi_sms.models import SMSLog, SMSVerificationCode
```

## 커스텀 모델로 확장

```python
from solapi_sms.models import AbstractSMSLog, AbstractSMSVerificationCode

class MySMSLog(AbstractSMSLog):
    class Meta(AbstractSMSLog.Meta):
        db_table = "my_sms_log"

class MySMSVerificationCode(AbstractSMSVerificationCode):
    class Meta(AbstractSMSVerificationCode.Meta):
        db_table = "my_sms_verification"
```

```python
SOLAPI_SMS_LOG_MODEL = "myapp.MySMSLog"
SOLAPI_SMS_VERIFICATION_MODEL = "myapp.MySMSVerificationCode"
```
