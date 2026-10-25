"""Source lifecycle: candidate -> active -> retired, with revival. Keeps the network alive, not bloated."""
from collector.config import CONFIG


def next_status(source: dict) -> dict:
    """Return the source with its status advanced for this run. Pure: does not mutate the input."""
    status = source["status"]
    out = dict(source)

    if status == "candidate":
        vet = source.get("vet")
        if vet == "promote":
            out["status"] = "active"
        elif vet == "reject":
            out["status"] = "retired"
        # "pending" or unknown: stay a candidate
        return out

    if status == "active":
        if source.get("health") == "dead" or \
                source.get("irrelevant_streak_days", 0) >= CONFIG.retire_after_irrelevant_days:
            out["status"] = "retired"
        return out

    if status == "retired":
        if source.get("recent_relevant"):
            out["status"] = "active"
        return out

    return out


def lifecycle_stats(sources) -> dict:
    stats = {"promoted": 0, "retired": 0, "revived": 0, "unchanged": 0}
    for s in sources:
        before, after = s["status"], next_status(s)["status"]
        if before == after:
            stats["unchanged"] += 1
        elif after == "active" and before == "candidate":
            stats["promoted"] += 1
        elif after == "active" and before == "retired":
            stats["revived"] += 1
        elif after == "retired":
            stats["retired"] += 1
    return stats
