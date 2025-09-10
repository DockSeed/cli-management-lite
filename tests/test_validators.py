import pathlib
import sys

import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from modules.validators import ItemValidator


def test_validate_amount():
    assert ItemValidator.validate_amount("5") == 5
    with pytest.raises(ValueError):
        ItemValidator.validate_amount("-1")


def test_validate_status():
    assert ItemValidator.validate_status("bestellt") == "bestellt"
    with pytest.raises(ValueError):
        ItemValidator.validate_status("falsch")


def test_validate_name():
    assert ItemValidator.validate_name("  Test ") == "Test"
    with pytest.raises(ValueError):
        ItemValidator.validate_name("")


def test_validate_date():
    assert ItemValidator.validate_date("2020-01-01") == "2020-01-01"
    assert ItemValidator.validate_date("01.01.2020") == "01.01.2020"
    with pytest.raises(ValueError):
        ItemValidator.validate_date("20200101")
