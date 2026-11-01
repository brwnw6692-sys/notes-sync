"""The analyst layer (pure parts): turn collected events into a prompt, and parse the assessment back.

The network call to the model lives at the edge (analyze.py). Here we only build the digest we send,
write the instruction that keeps the model grounded, and parse its JSON answer — all testable offline.
"""
import json
from datetime import datetime, timezone


def _age_hours(posted_at, now):
    try:
        t = datetime.fromisoformat((posted_at or "").replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    n = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    return (n - t).total_seconds() / 3600


def build_digest(items, now, lens_of=None, affiliation_of=None, window_hours=168, max_items=180,
                 snippet_chars=240) -> str:
    """A compact, recent, located slice of the feed for the model to reason over — newest first.
    Carries time, place coords, lens and affiliation, and a text snippet; capped to stay small."""
    lens_of = lens_of or {}
    affiliation_of = affiliation_of or {}
    rows = []
    for it in items:
        if it.get("lat") is None or it.get("lon") is None:
            continue
        age = _age_hours(it.get("posted_at"), now)
        if age is None or age < 0 or age > window_hours:
            continue
        rows.append((age, it))
    rows.sort(key=lambda r: r[0])                 # newest first
    lines = []
    for age, it in rows[:max_items]:
        src = it.get("source_id", "")
        tags = []
        if lens_of.get(src):
            tags.append(lens_of[src])
        if affiliation_of.get(src):
            tags.append(affiliation_of[src])
        tag = f"[{'/'.join(tags)}]" if tags else "[?]"
        text = " ".join((it.get("text_raw") or "").split())[:snippet_chars]
        lines.append(f"- {age:.0f}h ago @({it['lat']:.2f},{it['lon']:.2f}) {tag} {text}")
    return "\n".join(lines)


def analyst_prompt(digest: str, now) -> str:
    """The instruction: cross-reference actors/allies/statements/movements, name open and hidden
    interests, and stay grounded — observed vs inferred, with confidence, never invented."""
    return f"""You are a Middle East intelligence analyst. Below is a time-stamped, geolocated slice of
open-source reports (public Telegram channels), newest first. Each line: hours-ago, (lat,lon),
[lens and/or affiliation of the reporting source], and a text snippet (Arabic/Hebrew/Persian).

Today is {now.date().isoformat()}. Cross-reference across the reports: who is active where, which
actors align or clash, notable statements, and troop/activity movements. Then, per major actor
(states and organizations — e.g. Israel, Iran/IRGC, Hezbollah, Hamas, Syrian factions, PMF, SDF,
Houthis, Turkey, Gulf states), assess their interests.

Rules — follow strictly:
- Base every claim on the data below. Quote or reference the evidence.
- Separate OBSERVED (seen in the data) from INFERRED (your reading between the lines).
- Give each inference a confidence: low / medium / high.
- Where the data is thin, say "insufficient data". Never invent events, actors, or quotes.

Return ONLY JSON of this shape:
{{"generated_for_date":"{now.date().isoformat()}",
 "actors":[{{"actor":"","observed":["..."],"allies":["..."],"tensions":["..."],
   "open_interests":["..."],"hidden_interests":[{{"claim":"","confidence":"low|medium|high"}}],
   "movements":["..."]}}],
 "summary":""}}

DATA:
{digest}
"""


def parse_assessment(response_text: str) -> dict:
    """Parse the model's JSON answer; tolerate code fences and surrounding prose. Falls back to raw."""
    s = (response_text or "").strip()
    if "```" in s:
        parts = s.split("```")
        for p in parts:
            p = p.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            if p.startswith("{"):
                s = p
                break
    start, end = s.find("{"), s.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(s[start:end + 1])
        except json.JSONDecodeError:
            pass
    return {"actors": [], "summary": "", "raw": (response_text or "")[:4000]}
