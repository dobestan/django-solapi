"""Tests for retry with exponential backoff and batch error isolation."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from solapi_sms.client import SolapiClient, _is_retryable


class TestIsRetryable:
    """Test _is_retryable helper for classifying exceptions."""

    def test_timeout_error_is_retryable(self) -> None:
        assert _is_retryable(TimeoutError("timed out")) is True

    def test_connection_error_is_retryable(self) -> None:
        assert _is_retryable(ConnectionError("reset")) is True

    def test_os_error_is_retryable(self) -> None:
        assert _is_retryable(OSError("network unreachable")) is True

    def test_solapi_unknown_error_is_retryable(self) -> None:
        """SOLAPI SDK raises Exception('UnknownError', '...') for 5xx."""
        exc = Exception("UnknownError", "Internal Server Error")
        assert _is_retryable(exc) is True

    def test_solapi_auth_error_not_retryable(self) -> None:
        """Auth failures should not be retried."""
        exc = Exception("Unauthorized", "Invalid API key")
        assert _is_retryable(exc) is False

    def test_solapi_invalid_phone_not_retryable(self) -> None:
        exc = Exception("InvalidPhoneNumber", "Bad phone")
        assert _is_retryable(exc) is False

    def test_solapi_validation_error_not_retryable(self) -> None:
        exc = Exception("ValidationError", "Missing field")
        assert _is_retryable(exc) is False

    def test_solapi_not_enough_balance_not_retryable(self) -> None:
        exc = Exception("NotEnoughBalance", "Insufficient funds")
        assert _is_retryable(exc) is False

    def test_generic_value_error_not_retryable(self) -> None:
        assert _is_retryable(ValueError("bad value")) is False

    def test_generic_exception_no_args_not_retryable(self) -> None:
        assert _is_retryable(Exception()) is False


class TestSendWithRetry:
    """Test SolapiClient._send_with_retry exponential backoff."""

    @patch("solapi_sms.client.time.sleep")
    @patch("solapi_sms.client.SolapiMessageService")
    def test_succeeds_on_first_try(self, mock_svc_cls: Any, mock_sleep: Any) -> None:
        mock_svc = MagicMock()
        mock_svc.send.return_value = {"statusCode": "2000"}
        mock_svc_cls.return_value = mock_svc

        client = SolapiClient(api_key="k", api_secret="s")
        result = client.send_message("01012345678", "hello")

        assert result == {"statusCode": "2000"}
        mock_svc.send.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("solapi_sms.client.time.sleep")
    @patch("solapi_sms.client.SolapiMessageService")
    def test_retries_on_transient_failure(self, mock_svc_cls: Any, mock_sleep: Any) -> None:
        """Should retry on 5xx (UnknownError) and succeed on second attempt."""
        mock_svc = MagicMock()
        mock_svc.send.side_effect = [
            Exception("UnknownError", "500 Internal Server Error"),
            {"statusCode": "2000"},
        ]
        mock_svc_cls.return_value = mock_svc

        client = SolapiClient(api_key="k", api_secret="s")
        result = client.send_message("01012345678", "hello")

        assert result == {"statusCode": "2000"}
        assert mock_svc.send.call_count == 2
        mock_sleep.assert_called_once_with(1.0)

    @patch("solapi_sms.client.time.sleep")
    @patch("solapi_sms.client.SolapiMessageService")
    def test_exponential_backoff_delays(self, mock_svc_cls: Any, mock_sleep: Any) -> None:
        """Verify delay doubles: 1s, 2s, 4s."""
        mock_svc = MagicMock()
        mock_svc.send.side_effect = [
            Exception("UnknownError", "error"),
            Exception("UnknownError", "error"),
            Exception("UnknownError", "error"),
            {"statusCode": "2000"},
        ]
        mock_svc_cls.return_value = mock_svc

        client = SolapiClient(api_key="k", api_secret="s")
        result = client.send_message("01012345678", "hello")

        assert result == {"statusCode": "2000"}
        assert mock_svc.send.call_count == 4
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays == [1.0, 2.0, 4.0]

    @patch("solapi_sms.client.time.sleep")
    @patch("solapi_sms.client.SolapiMessageService")
    def test_raises_after_max_retries(self, mock_svc_cls: Any, mock_sleep: Any) -> None:
        """Should raise after exhausting all retries."""
        mock_svc = MagicMock()
        mock_svc.send.side_effect = Exception("UnknownError", "persistent error")
        mock_svc_cls.return_value = mock_svc

        client = SolapiClient(api_key="k", api_secret="s")
        with pytest.raises(Exception, match="UnknownError"):
            client.send_message("01012345678", "hello")

        # 1 initial + 3 retries = 4 total attempts
        assert mock_svc.send.call_count == 4
        assert mock_sleep.call_count == 3

    @patch("solapi_sms.client.time.sleep")
    @patch("solapi_sms.client.SolapiMessageService")
    def test_no_retry_on_auth_error(self, mock_svc_cls: Any, mock_sleep: Any) -> None:
        """Auth errors should fail immediately without retry."""
        mock_svc = MagicMock()
        mock_svc.send.side_effect = Exception("Unauthorized", "Invalid API key")
        mock_svc_cls.return_value = mock_svc

        client = SolapiClient(api_key="k", api_secret="s")
        with pytest.raises(Exception, match="Unauthorized"):
            client.send_message("01012345678", "hello")

        mock_svc.send.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("solapi_sms.client.time.sleep")
    @patch("solapi_sms.client.SolapiMessageService")
    def test_no_retry_on_invalid_phone(self, mock_svc_cls: Any, mock_sleep: Any) -> None:
        mock_svc = MagicMock()
        mock_svc.send.side_effect = Exception("InvalidPhoneNumber", "Bad number")
        mock_svc_cls.return_value = mock_svc

        client = SolapiClient(api_key="k", api_secret="s")
        with pytest.raises(Exception, match="InvalidPhoneNumber"):
            client.send_message("01012345678", "hello")

        mock_svc.send.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("solapi_sms.client.time.sleep")
    @patch("solapi_sms.client.SolapiMessageService")
    def test_retries_on_connection_error(self, mock_svc_cls: Any, mock_sleep: Any) -> None:
        mock_svc = MagicMock()
        mock_svc.send.side_effect = [
            ConnectionError("Connection refused"),
            {"statusCode": "2000"},
        ]
        mock_svc_cls.return_value = mock_svc

        client = SolapiClient(api_key="k", api_secret="s")
        result = client.send_message("01012345678", "hello")

        assert result == {"statusCode": "2000"}
        assert mock_svc.send.call_count == 2


@pytest.mark.django_db
class TestSendSmsBatch:
    """Test SMSService.send_sms_batch error isolation."""

    def test_batch_all_succeed(self, settings: Any) -> None:
        settings.DEBUG = True

        from solapi_sms.services import SMSService

        service = SMSService()
        results = service.send_sms_batch(
            [
                ("01012345678", "msg1"),
                ("01099998888", "msg2"),
            ]
        )

        assert len(results) == 2
        assert all(r["success"] for r in results)

    def test_batch_partial_failure(self, settings: Any) -> None:
        """If one message fails, others should still be sent."""
        settings.DEBUG = False

        from solapi_sms.services import SMSService

        service = SMSService(api_key="k", api_secret="s", sender="01000000000")

        with patch.object(service, "send_sms") as mock_send:
            mock_send.side_effect = [True, Exception("API error"), True]

            results = service.send_sms_batch(
                [
                    ("01011111111", "msg1"),
                    ("01022222222", "msg2"),
                    ("01033333333", "msg3"),
                ]
            )

        assert len(results) == 3
        assert results[0] == {"phone": "01011111111", "success": True}
        assert results[1]["phone"] == "01022222222"
        assert results[1]["success"] is False
        assert "API error" in results[1]["error"]
        assert results[2] == {"phone": "01033333333", "success": True}

    def test_batch_empty_list(self, settings: Any) -> None:
        from solapi_sms.services import SMSService

        service = SMSService()
        results = service.send_sms_batch([])
        assert results == []
