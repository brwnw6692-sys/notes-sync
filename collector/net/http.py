"""The thin real-network edge: a transport the PoliteClient drives. Identifies itself, reads only."""
import httpx

# A plain, honest identifier. We read public pages politely, like a browser, not anonymously.
USER_AGENT = "field-notes/0.1 (+https://github.com/; open-source monitoring; contact via repo)"


def make_transport(client: httpx.Client | None = None):
    """Returns transport(url, timeout) -> (status, text) for PoliteClient."""
    owned = client or httpx.Client(
        headers={"User-Agent": USER_AGENT, "Accept-Language": "ar,fa,en"},
        follow_redirects=True)

    def transport(url: str, timeout: float):
        resp = owned.get(url, timeout=timeout)
        return resp.status_code, resp.text

    return transport
