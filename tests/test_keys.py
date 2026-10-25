import base64
import os

from collector.keys import parse_key


def test_standard_base64_roundtrip():
    key = os.urandom(32)
    assert parse_key(base64.b64encode(key).decode()) == key


def test_whitespace_anywhere_is_ignored():
    key = os.urandom(32)
    b64 = base64.b64encode(key).decode()
    assert parse_key("  " + b64[:10] + "\n" + b64[10:] + "  ") == key


def test_urlsafe_alphabet_accepted():
    key = os.urandom(32)
    assert parse_key(base64.urlsafe_b64encode(key).decode()) == key


def test_empty_is_none():
    assert parse_key("") is None


def test_wrong_length_is_none():
    assert parse_key(base64.b64encode(b"short").decode()) is None


def test_garbage_is_none():
    assert parse_key("!!!!not base64!!!!") is None
