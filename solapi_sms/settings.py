from django.conf import settings as django_settings

SOLAPI_API_KEY = getattr(django_settings, "SOLAPI_API_KEY", "")
SOLAPI_API_SECRET = getattr(django_settings, "SOLAPI_API_SECRET", "")
SOLAPI_SENDER_PHONE = getattr(django_settings, "SOLAPI_SENDER_PHONE", "")
SOLAPI_APP_NAME = getattr(django_settings, "SOLAPI_APP_NAME", "")

SOLAPI_DEBUG_SKIP = getattr(django_settings, "SOLAPI_DEBUG_SKIP", True)
SOLAPI_LOG_SKIPPED = getattr(django_settings, "SOLAPI_LOG_SKIPPED", True)

# Set to False to disable SMSLog creation (useful when using django-notify's NotificationLog)
SOLAPI_LOG_ENABLED = getattr(django_settings, "SOLAPI_LOG_ENABLED", True)

SOLAPI_SUCCESS_STATUS_CODES = getattr(django_settings, "SOLAPI_SUCCESS_STATUS_CODES", ("2000",))

SOLAPI_VERIFICATION_TTL_SECONDS = getattr(django_settings, "SOLAPI_VERIFICATION_TTL_SECONDS", 180)
SOLAPI_VERIFICATION_MAX_ATTEMPTS = getattr(django_settings, "SOLAPI_VERIFICATION_MAX_ATTEMPTS", 5)
SOLAPI_VERIFICATION_RATE_LIMIT_COUNT = getattr(
    django_settings, "SOLAPI_VERIFICATION_RATE_LIMIT_COUNT", 0
)
SOLAPI_VERIFICATION_RATE_LIMIT_WINDOW_SECONDS = getattr(
    django_settings, "SOLAPI_VERIFICATION_RATE_LIMIT_WINDOW_SECONDS", 0
)

SOLAPI_CELERY_QUEUE = getattr(django_settings, "SOLAPI_CELERY_QUEUE", None)

# Task backend configuration
# Options: "sync" (default), "django6", "celery"
SOLAPI_TASK_BACKEND = getattr(django_settings, "SOLAPI_TASK_BACKEND", "sync")

SOLAPI_TEMPLATES = getattr(
    django_settings,
    "SOLAPI_TEMPLATES",
    {
        "verification": "[{app_name}] 인증번호는 [{code}]입니다. {expires_minutes}분 내로 입력해주세요.",
        "login_notification": "[{app_name}] [{username}]님이 로그인 하였습니다.",
        "welcome": "[{app_name}] 회원가입을 환영합니다.",
        "analysis_complete": "[{app_name}] 분석이 완료되었습니다.\n{report_url}",
    },
)

SOLAPI_SMS_LOG_MODEL = getattr(django_settings, "SOLAPI_SMS_LOG_MODEL", None)
SOLAPI_SMS_VERIFICATION_MODEL = getattr(django_settings, "SOLAPI_SMS_VERIFICATION_MODEL", None)

# Test mode: bypass SMS verification for specific phone/code pairs
# Format: {"phone_number": "verification_code"}
# Example: {"01022205736": "573648"}
SOLAPI_TEST_CREDENTIALS = getattr(django_settings, "SOLAPI_TEST_CREDENTIALS", {})
