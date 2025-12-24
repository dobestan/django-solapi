# Admin

기본 Admin은 `SMSLog`, `SMSVerificationCode`에 대해 표준 리스트/검색/필터를 제공합니다.

## 재발송 유틸

`SMSLog` 관리자 화면에서 "선택 SMS 재발송" 액션으로 재발송 가능합니다.

## 커스텀 모델 사용 시

```python
from django.contrib import admin
from solapi_sms.admin import SMSLogAdminMixin, SMSVerificationCodeAdminMixin
from .models import MySMSLog, MySMSVerificationCode

@admin.register(MySMSLog)
class MySMSLogAdmin(SMSLogAdminMixin, admin.ModelAdmin):
    pass

@admin.register(MySMSVerificationCode)
class MySMSVerificationCodeAdmin(SMSVerificationCodeAdminMixin, admin.ModelAdmin):
    pass
```
