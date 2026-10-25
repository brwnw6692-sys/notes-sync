import os

import pytest

from collector.store.crypto import (HEADER, CryptoError, decrypt, encrypt, pad,
                                    unpad, unwrap_key, wrap_key)

PASS = "correct horse battery staple donkey"


def test_roundtrip():
    key = os.urandom(32)
    blob = encrypt(b"hello world", key)
    assert blob.startswith(HEADER)
    assert decrypt(blob, key) == b"hello world"


def test_same_plaintext_encrypts_differently_each_time():
    key = os.urandom(32)
    assert encrypt(b"same", key) != encrypt(b"same", key)


def test_tamper_fails():
    key = os.urandom(32)
    blob = bytearray(encrypt(b"data", key))
    blob[-1] ^= 0x01
    with pytest.raises(CryptoError):
        decrypt(bytes(blob), key)


def test_wrong_key_fails():
    blob = encrypt(b"data", os.urandom(32))
    with pytest.raises(CryptoError):
        decrypt(blob, os.urandom(32))


def test_bad_header_fails_cleanly():
    with pytest.raises(CryptoError):
        decrypt(b"XXXX" + os.urandom(64), os.urandom(32))


def test_key_envelope_roundtrip():
    data_key = os.urandom(32)
    assert unwrap_key(wrap_key(data_key, PASS), PASS) == data_key


def test_wrong_passphrase_fails():
    wrapped = wrap_key(os.urandom(32), PASS)
    with pytest.raises(CryptoError):
        unwrap_key(wrapped, "wrong passphrase")


def test_padding_hides_size_in_power_of_two_buckets():
    assert len(pad(b"x" * 10)) == 4096
    assert len(pad(b"x" * 5000)) == 8192
    assert unpad(pad(b"abc")) == b"abc"
