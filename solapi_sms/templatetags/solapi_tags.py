from django import template

from solapi_sms.utils import format_phone as _format_phone
from solapi_sms.utils import mask_phone as _mask_phone

register = template.Library()


@register.filter
def format_phone(value: str | None) -> str:
    if not value:
        return ""
    return _format_phone(value)


@register.filter
def mask_phone(value: str | None) -> str:
    if not value:
        return ""
    return _mask_phone(value)
