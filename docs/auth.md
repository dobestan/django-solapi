# Auth Helpers

`solapi_sms.auth` provides standardized helpers for SMS verification flows.

```python
from solapi_sms.auth import send_verification_code, verify_code

send_result = send_verification_code("01012345678")
if send_result["success"]:
    verification = send_result["verification"]

verify_result = verify_code("01012345678", "123456")
```

## Rate Limit

```python
SOLAPI_VERIFICATION_RATE_LIMIT_COUNT = 5
SOLAPI_VERIFICATION_RATE_LIMIT_WINDOW_SECONDS = 3600
```
