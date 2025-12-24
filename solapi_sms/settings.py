from django.conf import settings as django_settings

SOLAPI_API_KEY = getattr(django_settings, "SOLAPI_API_KEY", "")
SOLAPI_API_SECRET = getattr(django_settings, "SOLAPI_API_SECRET", "")
SOLAPI_SENDER_PHONE = getattr(django_settings, "SOLAPI_SENDER_PHONE", "")
SOLAPI_APP_NAME = getattr(django_settings, "SOLAPI_APP_NAME", "")

SOLAPI_DEBUG_SKIP = getattr(django_settings, "SOLAPI_DEBUG_SKIP", True)
SOLAPI_LOG_SKIPPED = getattr(django_settings, "SOLAPI_LOG_SKIPPED", True)

SOLAPI_SUCCESS_STATUS_CODES = getattr(
    django_settings, "SOLAPI_SUCCESS_STATUS_CODES", ("2000",)
)

SOLAPI_VERIFICATION_TTL_SECONDS = getattr(
    django_settings, "SOLAPI_VERIFICATION_TTL_SECONDS", 180
)
SOLAPI_VERIFICATION_MAX_ATTEMPTS = getattr(
    django_settings, "SOLAPI_VERIFICATION_MAX_ATTEMPTS", 5
)

SOLAPI_CELERY_QUEUE = getattr(django_settings, "SOLAPI_CELERY_QUEUE", None)

SOLAPI_TEMPLATES = getattr(
    django_settings,
    "SOLAPI_TEMPLATES",
    {
        "verification": "[{app_name}] 인증번호는 [{code}]입니다. {expires_minutes}분 내로 입력해주세요.",
        "login_notification": "[{app_name}] [{username}]님이 로그인 하였습니다.",
        "welcome": "[{app_name}] 회원가입을 환영합니다.",
    },
)

SOLAPI_SMS_LOG_MODEL = getattr(django_settings, "SOLAPI_SMS_LOG_MODEL", None)
SOLAPI_SMS_VERIFICATION_MODEL = getattr(
    django_settings, "SOLAPI_SMS_VERIFICATION_MODEL", None
)
