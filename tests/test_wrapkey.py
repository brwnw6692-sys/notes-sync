import os

from collector.wrapkey import write_wrapped
from collector.store.crypto import unwrap_key
from collector.store.guard import check_tree

DATA_KEY = os.urandom(32)


def test_wrapped_key_file_roundtrips_with_the_passphrase(tmp_path):
    write_wrapped(tmp_path, DATA_KEY, "correct horse battery staple donkey")
    blob = (tmp_path / "wrapped_key.bin").read_bytes()
    assert unwrap_key(blob, "correct horse battery staple donkey") == DATA_KEY


def test_wrapped_key_passes_the_guard(tmp_path):
    write_wrapped(tmp_path, DATA_KEY, "a long enough passphrase here")
    check_tree(tmp_path)


def test_wrong_passphrase_cannot_unwrap(tmp_path):
    import pytest
    from collector.store.crypto import CryptoError
    write_wrapped(tmp_path, DATA_KEY, "the real passphrase")
    blob = (tmp_path / "wrapped_key.bin").read_bytes()
    with pytest.raises(CryptoError):
        unwrap_key(blob, "the wrong passphrase")
