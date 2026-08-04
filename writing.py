import logging
import pathlib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, List

import requests

MAX_ITEMS = 5
root = pathlib.Path(__file__).parent.resolve()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

ENTRY_ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16">
                        <path fill-rule="evenodd" d="M2.5 3.5c0-.133.058-.318.282-.55.227-.237.592-.484 1.1-.708C4.899 1.795 6.354 1.5 8 1.5c1.647 0 3.102.295 4.117.742.51.224.874.47 1.101.707.224.233.282.418.282.551 0 .133-.058.318-.282.55-.227.237-.592.484-1.1.708C11.101 5.205 9.646 5.5 8 5.5c-1.647 0-3.102-.295-4.117-.742-.51-.224-.874-.47-1.101-.707-.224-.233-.282-.418-.282-.551zM1 3.5c0-.626.292-1.165.7-1.59.406-.422.956-.767 1.579-1.041C4.525.32 6.195 0 8 0c1.805 0 3.475.32 4.722.869.622.274 1.172.62 1.578 1.04.408.426.7.965.7 1.591v9c0 .626-.292 1.165-.7 1.59-.406.422-.956.767-1.579 1.041C11.476 15.68 9.806 16 8 16c-1.805 0-3.475-.32-4.721-.869-.623-.274-1.173-.62-1.579-1.04-.408-.426-.7-.965-.7-1.591v-9z"/>
                    </svg>"""

HEADER_ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="20" height="20">
                        <path fill-rule="evenodd" d="M1.75 0A1.75 1.75 0 000 1.75v12.5C0 15.216.784 16 1.75 16h12.5A1.75 1.75 0 0016 14.25V1.75A1.75 1.75 0 0014.25 0H1.75zM1.5 1.75a.25.25 0 01.25-.25h12.5a.25.25 0 01.25.25v12.5a.25.25 0 01-.25.25H1.75a.25.25 0 01-.25-.25V1.75zM4 4.75a.75.75 0 01.75-.75h6.5a.75.75 0 010 1.5h-6.5A.75.75 0 014 4.75zm0 3a.75.75 0 01.75-.75h6.5a.75.75 0 010 1.5h-6.5A.75.75 0 014 7.75zm0 3a.75.75 0 01.75-.75h3.5a.75.75 0 010 1.5h-3.5a.75.75 0 01-.75-.75z"/>
                    </svg>"""


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def format_date(date_str: str) -> str:
    try:
        d = datetime.fromisoformat(date_str)
    except ValueError:
        return date_str
    return d.strftime("%b %-d, %Y")


def fetch_writing(url: str) -> List[Dict[str, str]]:
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
    for item in items:
        entries.append({
            "title": (item.findtext("title") or "No Title").strip(),
            "url": (item.findtext("link") or "").strip(),
            "group": (item.findtext("group") or "").strip(),
            "date": (item.findtext("datePublished") or "").strip(),
        })

    entries.sort(key=lambda e: e["date"], reverse=True)
    return entries[:MAX_ITEMS]


def build_svg(entries: List[Dict[str, str]]) -> str:
    fields = ""
    for e in entries:
        title = escape_xml(e["title"])
        meta_parts = [p for p in [e["group"], format_date(e["date"])] if p]
        meta = escape_xml(" • ".join(meta_parts))
        link = escape_xml(e["url"])
        fields += f"""
                <div class="field">
                    {ENTRY_ICON}
                    <a href="{link}" target="_blank" class="entry-text">
                        <span class="entry-title">{title}</span>
                        <span class="entry-meta">{meta}</span>
                    </a>
                </div>"""

    updated = datetime.now(timezone.utc).strftime("%-d %b %Y, %H:%M:%S")
    height = 90 + len(entries) * 54

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="{height}" class="">
    <defs>
        <style/>
    </defs>
    <style>@keyframes animation-rainbow{{0%,to{{color:#7f00ff;fill:#7f00ff}}14%{{color:#a933ff;fill:#a933ff}}29%{{color:#007fff;fill:#007fff}}43%{{color:#00ff7f;fill:#00ff7f}}57%{{color:#ff0;fill:#ff0}}71%{{color:#ff7f00;fill:#ff7f00}}86%{{color:red;fill:red}}}}svg{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji;font-size:14px;color:#777}}h1,h2,h3{{margin:8px 0 2px;padding:0;color:#0366d6}}h1 svg,h2 svg,h3 svg{{fill:currentColor}}h1{{font-size:20px;font-weight:700}}h2{{font-size:16px;font-weight:400}}section&gt;.field{{margin-left:5px;margin-right:5px}}.field{{display:flex;align-items:flex-start;margin-bottom:10px;white-space:normal}}.field svg{{margin:2px 8px 0 0;fill:#959da5;flex-shrink:0}}.entry-text{{display:flex;flex-direction:column}}.entry-title{{color:#24292e;font-weight:600;line-height:1.35}}.entry-title:hover{{color:#0366d6}}.entry-meta{{color:#6a737d;font-size:12px;margin-top:2px}}a{{text-decoration:none}}footer{{margin-top:8px;font-size:10px;font-style:italic;color:#666;text-align:right;padding:0 4px}}</style>
    <style/>
    <foreignObject x="0" y="0" width="100%" height="100%">
        <div xmlns="http://www.w3.org/1999/xhtml" xmlns:xlink="http://www.w3.org/1999/xlink" class="items-wrapper">
            <section>
                <h1 class="field">
                    {HEADER_ICON}
                    <span>Latest writing</span>
                </h1>
            </section>
            <section>{fields}
            </section>
            <footer>
                <span>Last updated {updated} (timezone UTC)</span>
            </footer>
        </div>
        <div xmlns="http://www.w3.org/1999/xhtml" id="writing-end"></div>
    </foreignObject>
</svg>
"""


if __name__ == "__main__":
    url = "https://www.kyraezikeuzor.com/writing.xml"
    output = root / "writing.svg"

    entries = fetch_writing(url)
    svg = build_svg(entries)
    output.write_text(svg)
    print(f"Wrote {len(entries)} entries to {output}")
