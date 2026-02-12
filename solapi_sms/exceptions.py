class SolapiSMSConfigError(RuntimeError):
    """Raised when SOLAPI configuration is missing."""


class SolapiSMSSendError(RuntimeError):
    """Raised when SOLAPI send fails."""


class SolapiKakaoConfigError(RuntimeError):
    """Raised when Kakao (Alimtalk/Brand Message) configuration is missing."""


class SolapiKakaoSendError(RuntimeError):
    """Raised when Kakao message send fails."""
