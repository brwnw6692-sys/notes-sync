"""Live Telegram adapter: fetch the public web preview, then hand the HTML to the pure parser."""
from collector.core.contract import Cursor
from collector.sources.telegram import parse_page


def channel_url(channel: str, cursor: Cursor | None) -> str:
    # Always fetch the channel's latest page; the parser keeps only messages newer than the cursor.
    # (?before=<id> pages backwards into history — the wrong direction for catching new posts.)
    return f"https://t.me/s/{channel}"


def fetch_channel(client, channel: str, cursor: Cursor | None):
    """client.get(url) -> FetchResult. Network failures become health signals, never exceptions."""
    res = client.get(channel_url(channel, cursor))
    if res.ok:
        return parse_page(res.text, channel=channel, cursor=cursor)

    from collector.core.contract import CollectResult
    return CollectResult(
        fetch_ok=False, structure_ok=False,
        http_status=res.status, error_kind=res.error_kind,
        new_cursor=cursor)
