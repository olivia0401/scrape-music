# 02_static_html_quotes.py
import time
from pathlib import Path

import requests
import pandas as pd
from bs4 import BeautifulSoup

BASE = "https://quotes.toscrape.com"
UA = "scrape-lab/0.1 (contact: you@example.com)"

OUT_DIR = Path("outputs")
OUT_DIR.mkdir(exist_ok=True)

s = requests.Session()
s.headers.update({"User-Agent": UA})


def fetch_html(url: str) -> str:
    r = s.get(url, timeout=20)
    r.raise_for_status()
    return r.text


def parse_quotes(html: str):
    """解析一页 HTML，返回 rows + next_url(没有则 None)"""
    soup = BeautifulSoup(html, "html.parser")

    rows = []
    for q in soup.select(".quote"):
        text = q.select_one(".text").get_text(strip=True)
        author = q.select_one(".author").get_text(strip=True)
        tags = [t.get_text(strip=True) for t in q.select(".tags .tag")]
        rows.append({"quote": text, "author": author, "tags": "|".join(tags)})

    next_a = soup.select_one("li.next a")
    next_url = (BASE + next_a["href"]) if next_a else None
    return rows, next_url


def main():
    url = BASE + "/"
    all_rows = []

    pages_to_fetch = 5
    for _ in range(pages_to_fetch):
        html = fetch_html(url)
        rows, next_url = parse_quotes(html)
        all_rows.extend(rows)

        if not next_url:
            break
        url = next_url
        time.sleep(0.8)  # 礼貌限速

    df = pd.DataFrame(all_rows)
    out = OUT_DIR / "quotes_static.csv"
    df.to_csv(out, index=False, encoding="utf-8")
    print(df.head())
    print(f"Saved -> {out}  rows={len(df)}")


if __name__ == "__main__":
    main()
