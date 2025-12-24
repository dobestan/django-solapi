import re
import secrets

PHONE_REGEX = re.compile(r"^01[0-9]{8,9}$")


def normalize_phone(phone: str) -> str:
    """Normalize phone number to digits only (01012345678)."""
    return re.sub(r"[^0-9]", "", phone or "")


def is_valid_phone(phone: str) -> bool:
    """Validate phone number format for KR mobile numbers."""
    return bool(PHONE_REGEX.match(phone or ""))


def mask_phone(phone: str) -> str:
    """Mask phone number for logs."""
    phone = normalize_phone(phone)
    if len(phone) == 11:
        return f"{phone[:3]}****{phone[-4:]}"
    if len(phone) == 10:
        return f"{phone[:3]}***{phone[-4:]}"
    return phone


def generate_verification_code() -> str:
    """Generate a 6-digit verification code."""
    return "".join(str(secrets.randbelow(10)) for _ in range(6))


def build_message(template: str, **kwargs) -> str:
    """Format a template with safe defaults."""
    safe_kwargs = {k: v for k, v in kwargs.items()}
    return template.format(**safe_kwargs)
