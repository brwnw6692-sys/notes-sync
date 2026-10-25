"""Set (or change) the map passphrase: wrap the data key with it and publish wrapped_key.bin.

The passphrase is the one secret that unlocks the map. It is typed here on your machine, wraps a
copy of the data key, and is never stored or sent anywhere. Changing it only rewrites wrapped_key.bin.

Usage (on your machine, with the data key in .secrets/DATA_KEY.txt):
    python -m collector.wrapkey --repo https://github.com/brwnw6692-sys/notes-sync.git
"""
import getpass
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from collector.keys import load_key
from collector.store.crypto import wrap_key
from collector.store.guard import check_tree


def write_wrapped(root: Path, data_key: bytes, passphrase: str) -> Path:
    path = Path(root) / "wrapped_key.bin"
    path.write_bytes(wrap_key(data_key, passphrase))
    return path


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _read_passphrase() -> str:
    env = os.environ.get("WRAP_PASSPHRASE")
    if env:
        return env
    p1 = getpass.getpass("New map passphrase (5+ words recommended): ")
    p2 = getpass.getpass("Repeat it: ")
    if p1 != p2:
        print("passphrases did not match", file=sys.stderr)
        raise SystemExit(2)
    if len(p1) < 8:
        print("passphrase too short", file=sys.stderr)
        raise SystemExit(2)
    return p1


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    repo = argv[argv.index("--repo") + 1] if "--repo" in argv else None
    data_key = load_key()
    if data_key is None:
        print("No data key: set DATA_KEY or create .secrets/DATA_KEY.txt", file=sys.stderr)
        return 2
    passphrase = _read_passphrase()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        if repo:
            _git(root, "init", "-q")
            try:
                _git(root, "fetch", "--depth=1", repo, "data")
                _git(root, "checkout", "-q", "FETCH_HEAD", "--", ".")
            except subprocess.CalledProcessError:
                pass
        write_wrapped(root, data_key, passphrase)
        check_tree(root)
        if repo:
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", "data: set map passphrase")
            _git(root, "push", "-f", repo, "HEAD:data")
    print("ok: map passphrase set")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
