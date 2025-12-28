from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.safestring import SafeString

from .models import SMSLog, SMSLogStatus, SMSVerificationCode
from .services import SMSService
from .utils import mask_phone


class SMSLogAdminMixin:
    """SMSLog 관리자에서 사용할 수 있는 메서드들을 제공하는 Mixin"""

    @admin.display(description="수신번호")
    def masked_phone(self, obj: SMSLog) -> str:
        return mask_phone(obj.phone)

    @admin.display(description="상태")
    def sms_status_badge(self, obj: SMSLog) -> SafeString:
        color_map: dict[str, str] = {
            SMSLogStatus.SUCCESS: "#0f766e",
            SMSLogStatus.FAILED: "#b91c1c",
            SMSLogStatus.SKIPPED: "#6b7280",
        }
        color = color_map.get(obj.status, "#6b7280")
        return format_html(
            '<span style="padding:2px 6px;border-radius:4px;color:white;background:{};">{}</span>',
            color,
            obj.get_status_display(),
        )


class SMSVerificationCodeAdminMixin:
    """SMSVerificationCode 관리자에서 사용할 수 있는 메서드들을 제공하는 Mixin"""

    @admin.display(description="만료됨", boolean=True)
    def sms_is_expired(self, obj: SMSVerificationCode) -> bool:
        value: Any = getattr(obj, "is_expired", False)
        result = value() if callable(value) else value
        return bool(result)

    @admin.display(description="유효", boolean=True)
    def sms_is_valid(self, obj: SMSVerificationCode) -> bool:
        return obj.is_valid()


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ["masked_phone", "message_type", "status_badge", "created_at"]
    list_filter = ["message_type", "status", "created_at"]
    search_fields = ["phone", "message"]
    readonly_fields = [
        "phone",
        "message",
        "message_type",
        "status",
        "response_data",
        "error_message",
        "created_at",
    ]
    actions = ["resend_selected_sms"]
    date_hierarchy = "created_at"

    @admin.display(description="수신번호")
    def masked_phone(self, obj: SMSLog) -> str:
        return mask_phone(obj.phone)

    @admin.display(description="상태")
    def status_badge(self, obj: SMSLog) -> SafeString:
        color_map: dict[str, str] = {
            SMSLogStatus.SUCCESS: "#0f766e",
            SMSLogStatus.FAILED: "#b91c1c",
            SMSLogStatus.SKIPPED: "#6b7280",
        }
        color = color_map.get(obj.status, "#6b7280")
        return format_html(
            '<span style="padding:2px 6px;border-radius:4px;color:white;background:{};">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.action(description="선택 SMS 재발송")
    def resend_selected_sms(
        self, request: HttpRequest, queryset: QuerySet[SMSLog]
    ) -> None:
        service = SMSService()
        success = 0
        failed = 0
        for log in queryset:
            if service.send_sms(log.phone, log.message, log.message_type):
                success += 1
            else:
                failed += 1
        self.message_user(request, f"재발송 성공: {success}건, 실패: {failed}건")


@admin.register(SMSVerificationCode)
class SMSVerificationCodeAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = [
        "phone",
        "code",
        "created_at",
        "expires_at",
        "verified_at",
        "attempts",
        "is_expired",
        "is_valid",
    ]
    list_filter = ["verified_at", "created_at"]
    search_fields = ["phone", "code"]
    readonly_fields = ["created_at", "verified_at"]
    date_hierarchy = "created_at"

    @admin.display(description="만료됨", boolean=True)
    def is_expired(self, obj: SMSVerificationCode) -> bool:
        value: Any = getattr(obj, "is_expired", False)
        result = value() if callable(value) else value
        return bool(result)

    @admin.display(description="유효", boolean=True)
    def is_valid(self, obj: SMSVerificationCode) -> bool:
        return obj.is_valid()
