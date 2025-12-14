# Scrape Lab: Data Collection Scripts

This project is a collection of Python scripts demonstrating various web scraping and data collection techniques, covering scenarios from static HTML pages to dynamic, JavaScript-rendered websites and REST APIs.

## Scripts Overview

### 1. `01_api_musicbrainz.py`
- **Objective:** Fetches recording data from the MusicBrainz REST API.
- **Features:**
    - Interacts with a JSON-based REST API.
    - Implements pagination to retrieve a large number of records.
    - Includes a simple exponential backoff retry mechanism for handling transient network errors.
    - Supports resuming downloads by checking for already downloaded data, preventing redundant requests.
- **Tech:** `requests`, `pandas`

### 2. `02_static_html_quotes.py`
- **Objective:** Scrapes quotes from `quotes.toscrape.com`, a static HTML website.
- **Features:**
    - Parses HTML content using `BeautifulSoup`.
    - Navigates through multiple pages by extracting the "Next" page link.
    - Demonstrates a polite scraping approach with a fixed delay between requests.
- **Tech:** `requests`, `pandas`, `BeautifulSoup`

### 3. `03_xhr_json_deezer_api.py`
- **Objective:** Extracts structured JSON data embedded within a page's HTML source.
- **Features:**
    - Fetches the main page HTML from `deezer.com`.
    - Locates and parses a large JSON object (`window.__DZR_APP_STATE__`) embedded in a `<script>` tag.
    - This technique is useful for sites that load their initial state this way, bypassing the need for reverse-engineering internal APIs.
- **Tech:** `requests`, `json`

### 4. `04_playwright_js_delayed.py`
- **Objective:** Scrapes quotes from `quotes.toscrape.com/js-delayed/`, where content is rendered dynamically using JavaScript.
- **Features:**
    - Uses Playwright to control a headless browser, ensuring all JavaScript is executed.
    - Waits for specific CSS selectors to appear on the page before attempting to extract data.
    - A robust solution for modern, dynamic websites.
- **Tech:** `playwright`, `pandas`, `asyncio`

## How to Run

1.  **Install Dependencies:**
    ```bash
    pip install requests pandas beautifulsoup4 "playwright"
    python -m playwright install
    ```

2.  **Run a Script:**
    Each script can be run independently. The output data will be saved to the `outputs/` directory.
    ```bash
    # Example: Run the static HTML scraper
    python3 02_static_html_quotes.py

    # Example: Run the Playwright script for a JS-rendered page
    python3 04_playwright_js_delayed.py
    ```
