# 02_static_html_quotes.py
import time
from pathlib import Path
import requests
import pandas as pd
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional


@dataclass
class Config:
    base_url: str = "https://quotes.toscrape.com"
    user_agent: str = "scrape-lab/0.1 (contact: you@example.com)"
    pages_to_fetch: int = 5
    out_dir: Path = Path("outputs")
    out_csv: Path = out_dir / "quotes_static.csv"

    def __post_init__(self):
        self.out_dir.mkdir(exist_ok=True)


def build_session(user_agent: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": user_agent})
    return s


def fetch(session: requests.Session, url: str) -> str:
    r = session.get(url, timeout=20)
    r.raise_for_status()
    return r.text


def parse(html: str, base_url: str) -> Tuple[List[Dict[str, str]], Optional[str]]:
    """Parses a page HTML, returns rows and the next page URL."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for q in soup.select(".quote"):
        text = q.select_one(".text").get_text(strip=True)
        author = q.select_one(".author").get_text(strip=True)
        tags = [t.get_text(strip=True) for t in q.select(".tags .tag")]
        rows.append({"quote": text, "author": author, "tags": "|".join(tags)})

    next_a = soup.select_one("li.next a")
    next_url = (base_url + next_a["href"]) if next_a else None
    return rows, next_url


def save(df: pd.DataFrame, path: Path):
    df.to_csv(path, index=False, encoding="utf-8")
    print(df.head())
    print(f"Saved -> {path}  rows={len(df)}")


def main():
    cfg = Config()
    session = build_session(cfg.user_agent)
    
    url: Optional[str] = cfg.base_url + "/"
    all_rows = []

    for _ in range(cfg.pages_to_fetch):
        if not url:
            break
        
        print(f"Fetching {url}...")
        html = fetch(session, url)
        rows, next_url = parse(html, cfg.base_url)
        all_rows.extend(rows)

        url = next_url
        time.sleep(0.8)

    df = pd.DataFrame(all_rows)
    save(df, cfg.out_csv)


if __name__ == "__main__":
    main()
