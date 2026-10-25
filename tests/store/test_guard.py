import os

import pytest

from collector.store.crypto import encrypt
from collector.store.guard import check_tree, is_encrypted


def test_plaintext_rejected(tmp_path):
    p = tmp_path / "a.bin"
    p.write_bytes(b"plain text leak")
    assert not is_encrypted(p)


def test_fake_header_with_plaintext_rejected(tmp_path):
    p = tmp_path / "a.bin"
    p.write_bytes(b"FNC1" + b"A" * 5000)
    assert not is_encrypted(p)


def test_short_plaintext_with_key_header_rejected(tmp_path):
    p = tmp_path / "k.bin"
    p.write_bytes(b"FNK1" + b"channel_one,channel_two,channel_three" + b"x" * 39)
    assert not is_encrypted(p)


def test_real_wrapped_key_accepted(tmp_path):
    from collector.store.crypto import wrap_key
    p = tmp_path / "wrapped_key.bin"
    p.write_bytes(wrap_key(os.urandom(32), "a long test passphrase here"))
    assert is_encrypted(p)


def test_encrypted_accepted(tmp_path):
    p = tmp_path / "a.bin"
    p.write_bytes(encrypt(b"secret", os.urandom(32)))
    assert is_encrypted(p)


def test_check_tree_blocks_any_plaintext_file_of_any_extension(tmp_path):
    (tmp_path / "ok.bin").write_bytes(encrypt(b"x", os.urandom(32)))
    (tmp_path / "notes.json").write_text('{"channel": "leak"}')
    with pytest.raises(SystemExit):
        check_tree(tmp_path)


def test_check_tree_passes_when_all_encrypted(tmp_path):
    (tmp_path / "s").mkdir()
    (tmp_path / "s" / "0a3f.bin").write_bytes(encrypt(b"x", os.urandom(32)))
    check_tree(tmp_path)


def test_check_tree_ignores_git_dir(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/data")
    (tmp_path / "ok.bin").write_bytes(encrypt(b"x", os.urandom(32)))
    check_tree(tmp_path)
