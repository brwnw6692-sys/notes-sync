from collector.sources.directory_search import parse_results, search_url


def test_search_url_encodes_the_arabic_query():
    assert search_url("دير الزور").startswith("https://lyzem.com/search?q=")
    assert "type=channels" in search_url("x")


def test_extracts_handles_and_drops_noise():
    html = '''
      <a href="https://t.me/deralzoor">x</a>
      <a href="https://t.me/dz_monasara">y</a>
      <a href="https://t.me/lyzemcom">self</a>
      <a href="https://t.me/EditorPost_bot">bot</a>
      <a href="https://t.me/bivcjbcduhbxfunbmkdtgbmmkgcvjn">spam</a>
    '''
    out = parse_results(html)
    assert "deralzoor" in out and "dz_monasara" in out
    assert "lyzemcom" not in out            # lyzem's own
    assert "editorpost_bot" not in out      # a bot
    assert "bivcjbcduhbxfunbmkdtgbmmkgcvjn" not in out  # consonant-wall spam


def test_dedupes_and_caps():
    html = " ".join('<a href="https://t.me/chan_%d">x</a>' % i for i in range(30))
    assert len(parse_results(html, limit=15)) == 15
