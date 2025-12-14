# 04_playwright_js_delayed.py
import asyncio
from pathlib import Path
import pandas as pd
from playwright.async_api import async_playwright, Page
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Config:
    url: str = "https://quotes.toscrape.com/js-delayed/"
    user_agent: str = "scrape-lab/0.1 (contact: you@example.com)"
    out_dir: Path = Path("outputs")
    out_csv: Path = out_dir / "quotes_playwright.csv"

    def __post_init__(self):
        self.out_dir.mkdir(exist_ok=True)


async def fetch(page: Page, url: str):
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_selector(".quote", timeout=15000)


async def parse(page: Page) -> List[Dict[str, str]]:
    rows = []
    cards = await page.query_selector_all(".quote")
    for c in cards:
        text_el = await c.query_selector(".text")
        author_el = await c.query_selector(".author")
        tag_els = await c.query_selector_all(".tags .tag")

        text = (await text_el.inner_text()).strip() if text_el else ""
        author = (await author_el.inner_text()).strip() if author_el else ""
        tags = [(await t.inner_text()).strip() for t in tag_els]

        rows.append({"quote": text, "author": author, "tags": "|".join(tags)})
    return rows


def save(df: pd.DataFrame, path: Path):
    df.to_csv(path, index=False, encoding="utf-8")
    print(df.head())
    print(f"Saved -> {path}  rows={len(df)}")


async def main():
    cfg = Config()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent=cfg.user_agent)

        await fetch(page, cfg.url)
        rows = await parse(page)
        
        await browser.close()

    df = pd.DataFrame(rows)
    save(df, cfg.out_csv)


if __name__ == "__main__":
    asyncio.run(main())
