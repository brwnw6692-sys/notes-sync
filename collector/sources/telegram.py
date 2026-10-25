"""Parser for the public t.me/s/<channel> web preview. Pure: HTML in, CollectResult out."""
from selectolax.parser import HTMLParser

from collector.core.contract import CollectResult, Cursor, Item

_MESSAGE = ".tgme_widget_message"
_CHANNEL_HEADER = ".tgme_channel_info"


def parse_page(html: str, channel: str, cursor: Cursor | None) -> CollectResult:
    tree = HTMLParser(html)
    nodes = tree.css(_MESSAGE)
    if not nodes and tree.css_first(_CHANNEL_HEADER) is None:
        # Neither messages nor channel header: the page format is unknown. Never report "quiet".
        return CollectResult(fetch_ok=True, structure_ok=False, error_kind="structure_changed")

    last_seen = cursor.last_native_id if cursor else 0
    parsed = []
    for n in nodes:
        post = n.attributes.get("data-post") or ""
        tail = post.rsplit("/", 1)[-1]
        if "/" not in post or not tail.isdigit():
            continue
        mid = int(tail)
        if mid > last_seen:
            parsed.append((mid, _to_item(n, channel, post, mid)))
    parsed.sort(key=lambda p: p[0])

    ids = [mid for mid, _ in parsed]
    gaps = 0
    if ids:
        prev = last_seen if last_seen else ids[0]
        for mid in ids:
            gaps += max(0, mid - prev - 1)
            prev = mid
    new_last = ids[-1] if ids else last_seen
    return CollectResult(
        items=[it for _, it in parsed],
        new_cursor=Cursor(last_native_id=new_last),
        fetch_ok=True, structure_ok=True, gaps_detected=gaps)


def _to_item(node, channel: str, post: str, mid: int) -> Item:
    text = node.css_first(".tgme_widget_message_text")
    time = node.css_first("time")
    return Item.make(
        source_id=channel, native_id=str(mid), url=f"https://t.me/{post}",
        text_raw=text.text(strip=True) if text else "",
        posted_at=(time.attributes.get("datetime") or "") if time else "",
        forwarded_from=_forward_handle(node))


def _forward_handle(node) -> str | None:
    link = node.css_first("a.tgme_widget_message_forwarded_from_name")
    if link is None:
        return None
    href = (link.attributes.get("href") or "").rstrip("/")
    if "t.me/" in href:
        return href.split("t.me/", 1)[1].split("/", 1)[0] or None
    return link.text(strip=True) or None
