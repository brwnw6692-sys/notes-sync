"""The hourly analyst run: read recent events, ask Gemini to cross-reference them, store the assessment.

Usage: python -m collector.analyze <data_dir>
Needs DATA_KEY (to read/write the encrypted store) and GEMINI_API_KEY (the free analyst model).
Only numbers reach stdout — Actions logs are public, so no content or source names are printed.
"""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from collector.analyst import analyst_prompt, build_digest, parse_assessment
from collector.config import CONFIG
from collector.keys import parse_key
from collector.store.guard import check_tree
from collector.store.state_store import load_recent_items, load_sources, save_assessment


def call_gemini(prompt: str, api_key: str, model: str) -> str:
    """Send the prompt to the Gemini API and return the model's text. Network lives only here."""
    import httpx
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    r = httpx.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    root = Path(argv[0]) if argv else Path("data_work")

    key = parse_key(os.environ.get("DATA_KEY", ""))
    if key is None:
        print("DATA_KEY missing or not a valid 32-byte base64 key", file=sys.stderr)
        return 2
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("GEMINI_API_KEY missing — skipping analysis", file=sys.stderr)
        return 0

    now = datetime.now(timezone.utc)
    srcs = load_sources(key, root)
    lens_of = {s["id"]: s.get("lens", "") for s in srcs}
    aff_of = {s["id"]: s.get("affiliation", "") for s in srcs}
    digest = build_digest(load_recent_items(key, root), now, lens_of=lens_of, affiliation_of=aff_of)
    if not digest.strip():
        print("analyst: no recent located items")
        return 0

    try:
        text = call_gemini(analyst_prompt(digest, now), api_key, CONFIG.gemini_model)
    except Exception as e:                      # never let the analyst crash the pipeline
        print(f"analyst: model call failed ({type(e).__name__})", file=sys.stderr)
        return 0

    assessment = parse_assessment(text)
    assessment["generated_at"] = now.isoformat()
    save_assessment(assessment, key, root)
    check_tree(root)                            # refuse to leave any non-encrypted file for the push
    print(f"analyst: actors={len(assessment.get('actors', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
