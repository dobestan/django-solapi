from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SMSLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "phone",
                    models.CharField(db_index=True, max_length=20, verbose_name="수신번호"),
                ),
                ("message", models.TextField(verbose_name="메시지 내용")),
                (
                    "message_type",
                    models.CharField(
                        choices=[
                            ("VERIFICATION", "인증코드"),
                            ("LOGIN_NOTIFICATION", "로그인 알림"),
                            ("WELCOME", "회원가입 환영"),
                            ("GENERIC", "일반"),
                        ],
                        default="GENERIC",
                        max_length=30,
                        verbose_name="메시지 타입",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("SUCCESS", "성공"),
                            ("FAILED", "실패"),
                            ("SKIPPED", "스킵"),
                        ],
                        max_length=20,
                        verbose_name="발송상태",
                    ),
                ),
                (
                    "response_data",
                    models.JSONField(blank=True, null=True, verbose_name="응답 데이터"),
                ),
                (
                    "error_message",
                    models.TextField(blank=True, default="", verbose_name="에러 메시지"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="발송시간"),
                ),
            ],
            options={
                "verbose_name": "SMS 발송기록",
                "verbose_name_plural": "SMS 발송기록",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="SMSVerificationCode",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "phone",
                    models.CharField(db_index=True, max_length=20, verbose_name="전화번호"),
                ),
                ("code", models.CharField(max_length=6, verbose_name="인증코드")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="생성시간"),
                ),
                (
                    "expires_at",
                    models.DateTimeField(db_index=True, verbose_name="만료시간"),
                ),
                (
                    "verified_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="인증완료시간"),
                ),
                (
                    "attempts",
                    models.PositiveIntegerField(default=0, verbose_name="시도 횟수"),
                ),
            ],
            options={
                "verbose_name": "SMS 인증코드",
                "verbose_name_plural": "SMS 인증코드",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="smsverificationcode",
            index=models.Index(
                fields=["phone", "-created_at"], name="solapi_sms_phone_created_idx"
            ),
        ),
    ]
