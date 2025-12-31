from solapi_sms.utils import format_phone, mask_phone, normalize_phone


class TestNormalizePhone:
    def test_removes_dashes(self) -> None:
        assert normalize_phone("010-1234-5678") == "01012345678"

    def test_removes_spaces(self) -> None:
        assert normalize_phone("010 1234 5678") == "01012345678"

    def test_already_normalized(self) -> None:
        assert normalize_phone("01012345678") == "01012345678"

    def test_empty_string(self) -> None:
        assert normalize_phone("") == ""

    def test_none_value(self) -> None:
        assert normalize_phone(None) == ""  # type: ignore[arg-type]


class TestMaskPhone:
    def test_11_digits(self) -> None:
        assert mask_phone("01012345678") == "010****5678"

    def test_10_digits(self) -> None:
        assert mask_phone("0111234567") == "011***4567"

    def test_with_dashes(self) -> None:
        assert mask_phone("010-1234-5678") == "010****5678"


class TestFormatPhone:
    def test_mobile_11_digits(self) -> None:
        assert format_phone("01012345678") == "010-1234-5678"

    def test_mobile_10_digits(self) -> None:
        assert format_phone("0111234567") == "011-123-4567"

    def test_already_formatted(self) -> None:
        assert format_phone("010-1234-5678") == "010-1234-5678"

    def test_with_spaces(self) -> None:
        assert format_phone("010 1234 5678") == "010-1234-5678"

    def test_seoul_9_digits(self) -> None:
        assert format_phone("021234567") == "02-123-4567"

    def test_seoul_10_digits(self) -> None:
        assert format_phone("0212345678") == "02-1234-5678"

    def test_local_10_digits(self) -> None:
        assert format_phone("0311234567") == "031-123-4567"

    def test_local_11_digits(self) -> None:
        assert format_phone("03112345678") == "031-1234-5678"

    def test_empty_string(self) -> None:
        assert format_phone("") == ""

    def test_invalid_returns_original(self) -> None:
        assert format_phone("12345") == "12345"

    def test_international_returns_original(self) -> None:
        assert format_phone("+821012345678") == "+821012345678"
