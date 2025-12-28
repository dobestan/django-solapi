from __future__ import annotations

import logging
from typing import Any

from solapi import SolapiMessageService
from solapi.model import RequestMessage

from . import settings

logger = logging.getLogger(__name__)


class SolapiClient:
    """Thin wrapper around SOLAPI SDK."""

    def __init__(
        self, api_key: str | None = None, api_secret: str | None = None
    ) -> None:
        self.api_key = api_key or settings.SOLAPI_API_KEY
        self.api_secret = api_secret or settings.SOLAPI_API_SECRET
        self._client = SolapiMessageService(
            api_key=self.api_key, api_secret=self.api_secret
        )

    def send_message(self, to: str, text: str, sender: str | None = None) -> Any:
        message = RequestMessage(
            to=to,
            from_=sender or settings.SOLAPI_SENDER_PHONE,
            text=text,
        )
        return self._client.send(message)

    @staticmethod
    def serialize_response(response: Any) -> dict[str, Any]:
        if hasattr(response, "model_dump"):
            return response.model_dump(mode="json")  # type: ignore[no-any-return]
        if isinstance(response, dict):
            return response
        if hasattr(response, "__dict__"):
            return dict(response.__dict__)
        return {"raw_response": str(response)}
