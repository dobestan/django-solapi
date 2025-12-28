from __future__ import annotations

from datetime import timedelta
from typing import Self

from django.db import models
from django.utils import timezone

from . import settings


class SMSLogStatus(models.TextChoices):
    SUCCESS = "SUCCESS", "성공"
    FAILED = "FAILED", "실패"
    SKIPPED = "SKIPPED", "스킵"


class SMSMessageType(models.TextChoices):
    VERIFICATION = "VERIFICATION", "인증코드"
    LOGIN_NOTIFICATION = "LOGIN_NOTIFICATION", "로그인 알림"
    WELCOME = "WELCOME", "회원가입 환영"
    GENERIC = "GENERIC", "일반"


class AbstractSMSLog(models.Model):
    phone = models.CharField("수신번호", max_length=20, db_index=True)
    message = models.TextField("메시지 내용")
    message_type = models.CharField(
        "메시지 타입",
        max_length=30,
        choices=SMSMessageType.choices,
        default=SMSMessageType.GENERIC,
    )
    status = models.CharField(
        "발송상태",
        max_length=20,
        choices=SMSLogStatus.choices,
    )
    response_data = models.JSONField("응답 데이터", null=True, blank=True)
    error_message = models.TextField("에러 메시지", blank=True, default="")
    created_at = models.DateTimeField("발송시간", auto_now_add=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.phone} - {self.message_type} - {self.status}"


class SMSLog(AbstractSMSLog):
    class Meta(AbstractSMSLog.Meta):
        verbose_name = "SMS 발송기록"
        verbose_name_plural = "SMS 발송기록"


class AbstractSMSVerificationCode(models.Model):
    phone = models.CharField("전화번호", max_length=20, db_index=True)
    code = models.CharField("인증코드", max_length=6)
    created_at = models.DateTimeField("생성시간", auto_now_add=True)
    expires_at = models.DateTimeField("만료시간", db_index=True)
    verified_at = models.DateTimeField("인증완료시간", null=True, blank=True)
    attempts = models.PositiveIntegerField("시도 횟수", default=0)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.phone} - {self.code}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_verified(self) -> bool:
        return self.verified_at is not None

    def is_valid(self, max_attempts: int | None = None) -> bool:
        max_attempts = max_attempts or settings.SOLAPI_VERIFICATION_MAX_ATTEMPTS
        return (
            not self.is_expired
            and not self.is_verified
            and self.attempts < max_attempts
        )

    def mark_attempt(self) -> None:
        self.attempts += 1
        self.save(update_fields=["attempts"])

    def mark_verified(self) -> None:
        self.verified_at = timezone.now()
        self.save(update_fields=["verified_at"])

    @classmethod
    def create_verification(
        cls, phone: str, code: str, ttl_seconds: int | None = None
    ) -> Self:
        ttl = ttl_seconds or settings.SOLAPI_VERIFICATION_TTL_SECONDS
        expires_at = timezone.now() + timedelta(seconds=ttl)
        cls.objects.filter(phone=phone, verified_at__isnull=True).update(  # type: ignore[attr-defined]
            verified_at=timezone.now()
        )
        return cls.objects.create(phone=phone, code=code, expires_at=expires_at)  # type: ignore[attr-defined, no-any-return]


class SMSVerificationCode(AbstractSMSVerificationCode):
    class Meta(AbstractSMSVerificationCode.Meta):
        verbose_name = "SMS 인증코드"
        verbose_name_plural = "SMS 인증코드"
