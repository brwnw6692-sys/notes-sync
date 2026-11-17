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


_SAFETY = [{"category": c, "threshold": "BLOCK_NONE"} for c in (
    "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
    "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT")]


def call_gemini(prompt: str, api_key: str, model: str) -> str:
    """Send the prompt to Gemini and return its text. Network lives only here. Safety filters are set
    to BLOCK_NONE — conflict reporting would otherwise be refused — and errors are explicit so a failed
    run says why. The error strings never contain the API key (it is only in the URL, never logged)."""
    import time
    import httpx
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = {"contents": [{"parts": [{"text": prompt}]}], "safetySettings": _SAFETY,
            "generationConfig": {"temperature": 0.4}}
    r = None
    for attempt in range(4):                    # the free model is often briefly overloaded (429/503)
        r = httpx.post(url, json=body, timeout=180)
        if r.status_code in (429, 500, 503) and attempt < 3:
            time.sleep(8 * (attempt + 1))
            continue
        break
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:400]}")
    data = r.json()
    cands = data.get("candidates") or []
    if not cands:
        raise RuntimeError(f"no candidates (promptFeedback={str(data.get('promptFeedback'))[:300]})")
    parts = (cands[0].get("content") or {}).get("parts") or []
    if not parts:
        raise RuntimeError(f"no parts (finishReason={cands[0].get('finishReason')})")
    return parts[0].get("text", "")


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
        msg = f"{type(e).__name__}: {e}"[:500]
        print(f"analyst: model call failed — {msg}", file=sys.stderr)
        # store the reason (encrypted) so we can diagnose without the Actions log
        save_assessment({"generated_at": now.isoformat(), "actors": [], "summary": "", "error": msg}, key, root)
        check_tree(root)
        return 0

    assessment = parse_assessment(text)
    assessment["generated_at"] = now.isoformat()
    save_assessment(assessment, key, root)
    check_tree(root)                            # refuse to leave any non-encrypted file for the push
    print(f"analyst: actors={len(assessment.get('actors', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
