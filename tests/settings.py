SECRET_KEY = "test-secret-key"
DEBUG = True

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "solapi_sms",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

USE_TZ = True
TIME_ZONE = "Asia/Seoul"

SOLAPI_API_KEY = ""
SOLAPI_API_SECRET = ""
SOLAPI_SENDER_PHONE = ""
SOLAPI_APP_NAME = "테스트"
