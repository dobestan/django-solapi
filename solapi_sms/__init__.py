"""
Django SOLAPI - SMS integration for SOLAPI

Provides:
- SMSService for sending SMS messages
- SMSLog model for logging sent messages
- SMSVerificationCode for phone verification
- Celery and Django 6 Tasks support

Requirements:
- Python 3.12+
- Django 5.0+ (Django 6.0+ recommended for Tasks)
"""

__version__ = "1.0.0"
__author__ = "Suchan An"
__all__ = ["__version__", "__author__"]
