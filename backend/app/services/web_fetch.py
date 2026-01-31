from html.parser import HTMLParser
import httpx

class _TextExtractor(HTMLParser):
  def __init__(self):
    super().__init__()
    self._parts: list[str] = []

  def handle_data(self, data: str) -> None:
    t = data.strip()
    if t:
      self._parts.append(t)

  def text(self) -> str:
    return "\n".join(self._parts)


async def fetch_url_text(url: str, *, timeout_seconds: float = 12.0) -> str:
  # Using a standard user agent to avoid being blocked by some sites
  headers = {
      "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
  }
  async with httpx.AsyncClient(follow_redirects=True, timeout=timeout_seconds, headers=headers) as client:
    resp = await client.get(url)
    resp.raise_for_status()
    html = resp.text
  
  parser = _TextExtractor()
  parser.feed(html)
  return parser.text()
