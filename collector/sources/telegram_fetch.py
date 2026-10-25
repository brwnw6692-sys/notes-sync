"""Live Telegram adapter: fetch the public web preview, then hand the HTML to the pure parser."""
from collector.core.contract import Cursor
from collector.sources.telegram import parse_page


def channel_url(channel: str, cursor: Cursor | None) -> str:
    base = f"https://t.me/s/{channel}"
    if cursor and cursor.last_native_id:
        # ?before=<id> pages backwards so we can fill a detected gap.
        return f"{base}?before={cursor.last_native_id + 1}"
    return base


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
