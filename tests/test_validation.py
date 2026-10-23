import pytest

from red_spectrogram.validation import (
    ValidationError,
    is_height_optimal,
    validate_gain,
    validate_height,
    validate_time_format,
    validate_width,
    validate_z_range,
)


@pytest.mark.parametrize("value", ["100", "3000", "5000"])
def test_validate_width_accepts_valid_range(value):
    assert validate_width(value) == int(value)


@pytest.mark.parametrize("value", ["99", "5001", "-1", "abc", ""])
def test_validate_width_rejects_invalid(value):
    with pytest.raises(ValidationError):
        validate_width(value)


@pytest.mark.parametrize("value", ["20", "120", "180"])
def test_validate_z_range_accepts_valid_range(value):
    assert validate_z_range(value) == int(value)


@pytest.mark.parametrize("value", ["19", "181", "abc"])
def test_validate_z_range_rejects_invalid(value):
    with pytest.raises(ValidationError):
        validate_z_range(value)


@pytest.mark.parametrize("value", ["-20", "0", "20"])
def test_validate_gain_accepts_valid_range(value):
    assert validate_gain(value) == int(value)


@pytest.mark.parametrize("value", ["-21", "21", "abc"])
def test_validate_gain_rejects_invalid(value):
    with pytest.raises(ValidationError):
        validate_gain(value)


def test_validate_height_rejects_non_integer():
    with pytest.raises(ValidationError):
        validate_height("abc")


@pytest.mark.parametrize("value", ["0", "-1", "63"])
def test_validate_height_rejects_below_sox_minimum(value):
    with pytest.raises(ValidationError):
        validate_height(value)


@pytest.mark.parametrize("value", ["64", "513", "5000"])
def test_validate_height_accepts_valid(value):
    assert validate_height(value) == int(value)


@pytest.mark.parametrize("height,expected", [(513, True), (1025, True), (500, False), (129, True)])
def test_is_height_optimal(height, expected):
    assert is_height_optimal(height) is expected


@pytest.mark.parametrize("value,expected", [("1:00", True), ("0:02", True), ("100:00", True), ("1:0", False), ("1", False), ("abc", False)])
def test_validate_time_format(value, expected):
    assert validate_time_format(value) is expected
