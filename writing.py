import logging
from typing import Dict, List
import pathlib
import requests
import re
import xml.etree.ElementTree as ET

DEFAULT_N = 5
root = pathlib.Path(__file__).parent.resolve()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}


def fetch_feed(url: str) -> List[Dict[str, str]]:
    """Fetches and parses the writing.xml feed from the given URL."""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        root_el = ET.fromstring(response.content)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching the feed: {e}")
        return []
    except ET.ParseError as e:
        logging.error(f"Error parsing the feed XML: {e}")
        return []

    items = root_el.findall("item")
    if not items:
        logging.error("Malformed feed: no items found")
        return []

    entries = []
    for item in items[:DEFAULT_N]:
        entries.append({
            "title": (item.findtext("title") or "No Title").strip(),
            "url": (item.findtext("link") or "").strip(),
            "group": (item.findtext("group") or "").strip(),
            "date": (item.findtext("datePublished") or "").strip(),
        })
    return entries


def format_feed_entry(entry: Dict[str, str]) -> str:
    """Formats a feed entry as a markdown link, with the publication venue."""
    title = entry.get("title", "No Title")
    link = entry.get("url", "")
    group = entry.get("group", "")
    if not link:
        logging.warning(f"Feed entry '{title}' is missing a URL.")
    if group:
        return f"[{title}]({link}) — *{group}*"
    return f"[{title}]({link})"


def replace_chunk(content: str, marker: str, chunk: str, inline: bool = False) -> str:
    """Replaces a chunk of text between specified markers in the content."""
    pattern = f"<!-- {marker} start -->.*<!-- {marker} end -->"
    r = re.compile(pattern, re.DOTALL)
    if not inline:
        chunk = f"\n{chunk}\n"
    match = r.search(content)
    if match:
        return r.sub(f"<!-- {marker} start -->{chunk}<!-- {marker} end -->", content)
    else:
        logging.error(f"Marker '{marker}' not found in the content.")
        return content


if __name__ == "__main__":
    readme = root / "README.md"
    url = "https://www.kyraezikeuzor.com/writing.xml"
    feeds = fetch_feed(url)
    feeds_md = "\n\n".join([format_feed_entry(feed) for feed in feeds])
    readme_contents = readme.read_text()
    rewritten = replace_chunk(readme_contents, "writing", feeds_md)
    readme.write_text(rewritten)
    print(feeds_md)
