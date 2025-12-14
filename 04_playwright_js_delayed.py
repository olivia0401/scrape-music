# 04_playwright_js_delayed.py
import asyncio
from pathlib import Path

import pandas as pd
from playwright.async_api import async_playwright

URL = "https://quotes.toscrape.com/js-delayed/"
UA = "scrape-lab/0.1 (contact: you@example.com)"

OUT_DIR = Path("outputs")
OUT_DIR.mkdir(exist_ok=True)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent=UA)

        await page.goto(URL, wait_until="domcontentloaded")

        # 关键：等渲染后的元素出现
        await page.wait_for_selector(".quote", timeout=15000)

        cards = await page.query_selector_all(".quote")
        rows = []
        for c in cards:
            text_el = await c.query_selector(".text")
            author_el = await c.query_selector(".author")
            tag_els = await c.query_selector_all(".tags .tag")

            text = (await text_el.inner_text()).strip() if text_el else ""
            author = (await author_el.inner_text()).strip() if author_el else ""
            tags = [(await t.inner_text()).strip() for t in tag_els]

            rows.append({"quote": text, "author": author, "tags": "|".join(tags)})

        await browser.close()

    df = pd.DataFrame(rows)
    out = OUT_DIR / "quotes_playwright.csv"
    df.to_csv(out, index=False, encoding="utf-8")
    print(df.head())
    print(f"Saved -> {out}  rows={len(df)}")


if __name__ == "__main__":
    asyncio.run(main())
