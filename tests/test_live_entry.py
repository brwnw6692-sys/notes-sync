import base64
import os

import pytest

from collector.live import load_data_key


def test_data_key_is_read_from_env_as_base64(monkeypatch):
    key = os.urandom(32)
    monkeypatch.setenv("DATA_KEY", base64.b64encode(key).decode())
    assert load_data_key() == key


def test_missing_key_fails_clearly(monkeypatch):
    monkeypatch.delenv("DATA_KEY", raising=False)
    with pytest.raises(SystemExit):
        load_data_key()


def test_wrong_length_key_is_rejected(monkeypatch):
    monkeypatch.setenv("DATA_KEY", base64.b64encode(b"tooshort").decode())
    with pytest.raises(SystemExit):
        load_data_key()
