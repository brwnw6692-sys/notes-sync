"""Local tool to manage the encrypted source registry on the data branch.

Usage (run on your own machine, with the key in .secrets/DATA_KEY.txt):
  python -m collector.addsource add <handle> --region <r> [--tier hot|quiet] [--canary]
  python -m collector.addsource remove <handle>
  python -m collector.addsource list

It fetches the data branch, applies the change to sources.bin, runs the guard, and pushes.
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from collector.keys import load_key
from collector.process.source_register import add_source, remove_source
from collector.store.guard import check_tree
from collector.store.state_store import load_sources, save_sources


def apply_change(root: Path, key: bytes, action: str, handle: str = "",
                 region: str = "", tier: str = "quiet", canary: bool = False,
                 lens: str = "", affiliation: str = ""):
    """Pure core: mutate the encrypted registry under `root`. Returns the list for `list`."""
    sources = load_sources(key, root)
    if action == "add":
        sources = add_source(sources, handle, region=region, tier=tier, canary=canary,
                             lens=lens, affiliation=affiliation)
        save_sources(sources, key, root)
    elif action == "remove":
        sources = remove_source(sources, handle)
        save_sources(sources, key, root)
    elif action == "list":
        return sources
    else:
        raise ValueError(f"unknown action: {action}")
    return sources


def _git(root: Path, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _parse(argv):
    # --repo is shared by every subcommand, so it is accepted in any position.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", help="git URL of the repo (for push); omit to only read local")
    p = argparse.ArgumentParser(prog="addsource", parents=[common])
    sub = p.add_subparsers(dest="action", required=True)
    a = sub.add_parser("add", parents=[common])
    a.add_argument("handle")
    a.add_argument("--region", required=True)
    a.add_argument("--tier", choices=["hot", "quiet"], default="quiet")
    a.add_argument("--canary", action="store_true")
    a.add_argument("--lens", default="", help="ar / fa / he — the source's reporting window")
    a.add_argument("--affiliation", default="", help="who it speaks for (regime, hezbollah, israeli, ...)")
    r = sub.add_parser("remove", parents=[common])
    r.add_argument("handle")
    sub.add_parser("list", parents=[common])
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = _parse(argv or sys.argv[1:])
    key = load_key()
    if key is None:
        print("No data key: set DATA_KEY or create .secrets/DATA_KEY.txt", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = args.repo
        if repo:
            _git(root, "init", "-q")
            try:
                _git(root, "fetch", "--depth=1", repo, "data")
                _git(root, "checkout", "-q", "FETCH_HEAD", "--", ".")
            except subprocess.CalledProcessError:
                pass  # data branch may not exist yet

        result = apply_change(root, key, args.action,
                              handle=getattr(args, "handle", ""),
                              region=getattr(args, "region", ""),
                              tier=getattr(args, "tier", "quiet"),
                              canary=getattr(args, "canary", False),
                              lens=getattr(args, "lens", ""),
                              affiliation=getattr(args, "affiliation", ""))

        if args.action == "list":
            print(f"{len(result)} source(s):")
            for s in result:
                flags = " canary" if s.get("canary") else ""
                print(f"  {s['id']}  [{s['region']}/{s['tier']}{flags}]")
            return 0

        check_tree(root)
        if repo:
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", "data: update source registry")
            _git(root, "push", "-f", repo, "HEAD:data")
        print(f"ok: {args.action} ({len(result)} source(s) now)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
