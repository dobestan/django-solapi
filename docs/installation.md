# Installation

```bash
uv add git+https://github.com/dobestan/django-solapi.git
```

```python
INSTALLED_APPS = [
    ...
    "solapi_sms",
]
```

```python
SOLAPI_API_KEY = "your-api-key"
SOLAPI_API_SECRET = "your-api-secret"
SOLAPI_SENDER_PHONE = "01012345678"
SOLAPI_APP_NAME = "서비스명"
SOLAPI_VERIFICATION_RATE_LIMIT_COUNT = 5
SOLAPI_VERIFICATION_RATE_LIMIT_WINDOW_SECONDS = 3600
```
