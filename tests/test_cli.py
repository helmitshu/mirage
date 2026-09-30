"""Tests for the Mirage CLI."""
import pytest

from mirage import __version__
from mirage.cli import main


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_missing_input_errors():
    with pytest.raises(SystemExit) as e:
        main([])
    assert e.value.code == 2
