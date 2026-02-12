class SolapiSMSConfigError(RuntimeError):
    """Raised when SOLAPI configuration is missing."""


class SolapiSMSSendError(RuntimeError):
    """Raised when SOLAPI send fails."""


class SolapiKakaoConfigError(RuntimeError):
    """Raised when Kakao (Infotalk/Brand Message) configuration is missing."""


class SolapiKakaoSendError(RuntimeError):
    """Raised when Kakao message send fails."""


class SolapiRCSConfigError(RuntimeError):
    """Raised when RCS configuration is missing."""


class SolapiRCSSendError(RuntimeError):
    """Raised when RCS message send fails."""
