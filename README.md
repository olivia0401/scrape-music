# Web Scraping Scripts Collection

This project contains a collection of Python scripts demonstrating various web scraping techniques.

## Script Descriptions

-   `01_api_musicbrainz.py`
    -   **Functionality**: Fetches data from the MusicBrainz API. The script searches for recording information based on a specified artist name and saves the search results and recording details into separate CSV files within the `outputs/` directory.

-   `02_static_html_quotes.py`
    -   **Functionality**: Scrapes quotes and author information from the static HTML website `quotes.toscrape.com` and saves the results to `outputs/quotes_static.csv`.

-   `03_xhr_json_deezer_api.py`
    -   **Functionality**: Scrapes public chart data from the Deezer website. This script directly requests the charts page and then parses a JSON object named `__DZR_APP_STATE__` embedded in the HTML to extract the data, finally saving it to `outputs/deezer_page.json`.

-   `04_playwright_js_delayed.py`
    -   **Functionality**: Demonstrates how to use the Playwright library to scrape a webpage that loads content asynchronously (delayed loading) via JavaScript. It waits for the data to load before scraping and saves the results to `outputs/quotes_playwright.csv`.

## Environment Setup

It is recommended to install the required dependencies within a Python virtual environment.

1.  **Install Dependencies:**
    ```bash
    pip install requests pandas playwright
    ```

2.  **Install Playwright Browser Drivers:**
    ```bash
    playwright install
    ```

## How to Run

You can run each script directly using Python. Please ensure your current working directory is `scrape_lab`.

```bash
# Run MusicBrainz API scraping script
python 01_api_musicbrainz.py

# Run static HTML scraping script
python 02_static_html_quotes.py

# Run Deezer charts scraping script
python 03_xhr_json_deezer_api.py

# Run Playwright delayed JS loading scraping script
python 04_playwright_js_delayed.py
```

All scraped data and output files will be saved in the `outputs/` directory.