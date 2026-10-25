"""AES-256-GCM per file, size padding, and a passphrase-wrapped data key (envelope)."""
import os
import struct

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

HEADER = b"FNC1"       # encrypted data file
KEY_HEADER = b"FNK1"   # wrapped data key
PBKDF2_ROUNDS = 600_000
_MIN_BUCKET = 4096


class CryptoError(Exception):
    pass


def pad(data: bytes) -> bytes:
    size = _MIN_BUCKET
    while size < len(data) + 4:
        size *= 2
    body = struct.pack(">I", len(data)) + data
    return body + b"\x00" * (size - len(body))


def unpad(body: bytes) -> bytes:
    n = struct.unpack(">I", body[:4])[0]
    if n > len(body) - 4:
        raise CryptoError("corrupt padding")
    return body[4:4 + n]


def encrypt(plaintext: bytes, key: bytes) -> bytes:
    nonce = os.urandom(12)
    return HEADER + nonce + AESGCM(key).encrypt(nonce, pad(plaintext), None)


def decrypt(blob: bytes, key: bytes) -> bytes:
    if blob[:4] != HEADER or len(blob) < 16 + 16:
        raise CryptoError("not an encrypted file")
    try:
        return unpad(AESGCM(key).decrypt(blob[4:16], blob[16:], None))
    except InvalidTag as e:
        raise CryptoError("authentication failed: wrong key or tampered file") from e


def _derive(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=PBKDF2_ROUNDS)
    return kdf.derive(passphrase.encode())


def wrap_key(data_key: bytes, passphrase: str) -> bytes:
    salt, nonce = os.urandom(16), os.urandom(12)
    kek = _derive(passphrase, salt)
    return KEY_HEADER + salt + nonce + AESGCM(kek).encrypt(nonce, data_key, None)


def unwrap_key(wrapped: bytes, passphrase: str) -> bytes:
    if wrapped[:4] != KEY_HEADER:
        raise CryptoError("not a wrapped key")
    salt, nonce, ct = wrapped[4:20], wrapped[20:32], wrapped[32:]
    try:
        return AESGCM(_derive(passphrase, salt)).decrypt(nonce, ct, None)
    except InvalidTag as e:
        raise CryptoError("wrong passphrase") from e
