# Web Scraping Lab: Multi-Strategy Data Collection Toolkit

A comprehensive demonstration of modern web scraping techniques using Python, showcasing four distinct approaches to data collection from REST APIs, static HTML, embedded JSON, and JavaScript-rendered websites.

## Overview

This project implements production-ready scraping patterns with proper error handling, rate limiting, and resume capabilities. Each script demonstrates best practices for different data source types commonly encountered in real-world web scraping projects.

**Total Scripts:** 4
**Lines of Code:** 485
**Status:** Fully functional with validated outputs

---

## Scripts & Features

### 1. REST API Scraping (`01_api_musicbrainz.py`)
**Target:** MusicBrainz REST API
**Complexity:** Advanced

**Features:**
- Multi-stage data pipeline (search → lookup → parse → save)
- Exponential backoff retry mechanism (handles transient failures)
- Resume capability (tracks completed lookups)
- Pagination support (configurable pages/limits)
- Rate limiting (1.05s delays)
- Dual output: CSV summaries + individual JSON files

**Output:**
- `musicbrainz_search.csv` - 100 recording search results
- `musicbrainz_details.csv` - Full metadata for each recording
- `details_json/` - 50+ individual JSON files

**Tech Stack:** `requests`, `pandas`, `dataclasses`

**Key Code Pattern:**
```python
@dataclass
class Config:
    base_url: str = "https://musicbrainz.org/ws/2"
    user_agent: str = "..."

def fetch_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = session.get(url)
            response.raise_for_status()
            return response.json()
        except RequestException:
            time.sleep(2 ** attempt)  # Exponential backoff
```

---

### 2. Static HTML Parsing (`02_static_html_quotes.py`)
**Target:** quotes.toscrape.com
**Complexity:** Basic

**Features:**
- CSS selector-based extraction
- Polite pagination via "Next" link following
- Session management with custom User-Agent
- Rate limiting (0.8s delays)
- Multi-page aggregation

**Output:**
- `quotes_static.csv` - 11 quotes with author and tags

**Tech Stack:** `requests`, `BeautifulSoup4`, `pandas`

**Key Code Pattern:**
```python
def parse_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    quotes = []
    for quote in soup.select('.quote'):
        quotes.append({
            'quote': quote.select_one('.text').get_text(),
            'author': quote.select_one('.author').get_text(),
            'tags': '|'.join([tag.get_text() for tag in quote.select('.tags .tag')])
        })
    return quotes
```

---

### 3. Embedded JSON Extraction (`03_xhr_json_deezer_api.py`)
**Target:** Deezer (embedded app state)
**Complexity:** Intermediate

**Features:**
- Manual JSON extraction from HTML `<script>` tags
- Brace-matching algorithm for nested JSON
- Environment-based configuration (cookies, session IDs)
- Comprehensive error handling with debug artifacts
- Supports initial state injection patterns (`window.__STATE__`)

**Output:**
- `deezer_page.json` - 138KB of extracted app state
- Debug artifacts on errors (error.html)

**Tech Stack:** `requests`, `json`, `pathlib`, environment variables

**Key Code Pattern:**
```python
def extract_json_from_html(html, target_var='__DZR_APP_STATE__'):
    start = html.find(f'{target_var} = ') + len(f'{target_var} = ')
    brace_count = 0
    for i, char in enumerate(html[start:], start):
        if char == '{': brace_count += 1
        elif char == '}': brace_count -= 1
        if brace_count == 0:
            return json.loads(html[start:i+1])
```

---

### 4. Browser Automation for JavaScript-Rendered Pages (`04_playwright_js_delayed.py`)
**Target:** quotes.toscrape.com/js-delayed/
**Complexity:** Advanced

**Features:**
- Headless Chromium browser control
- Async/await implementation
- Explicit waits for dynamic content (CSS selectors)
- DOM content loaded strategy
- Proper resource cleanup

**Output:**
- `quotes_playwright.csv` - 11 quotes from JS-rendered page

**Tech Stack:** `playwright`, `pandas`, `asyncio`

**Key Code Pattern:**
```python
async def scrape_js_delayed():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent="...")
        await page.goto(url, wait_until='domcontentloaded')
        await page.wait_for_selector('.quote', timeout=15000)

        quotes = await page.query_selector_all('.quote')
        for quote in quotes:
            text = await quote.query_selector('.text').inner_text()
```

---

## Installation & Usage

### Prerequisites
- Python 3.7+
- pip package manager

### Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd scrape_lab

# Install dependencies
pip install requests pandas beautifulsoup4 playwright

# Install Playwright browsers
python -m playwright install
```

### Running Scripts

```bash
# Run individual scripts
python3 01_api_musicbrainz.py      # REST API scraping
python3 02_static_html_quotes.py   # Static HTML parsing
python3 03_xhr_json_deezer_api.py  # Embedded JSON extraction
python3 04_playwright_js_delayed.py # Browser automation

# Outputs will be saved to outputs/ directory
ls outputs/
```

---

## Project Structure

```
scrape_lab/
├── 01_api_musicbrainz.py       # REST API with retry/resume (210 LOC)
├── 02_static_html_quotes.py    # Static HTML scraping (80 LOC)
├── 03_xhr_json_deezer_api.py   # Embedded JSON extraction (130 LOC)
├── 04_playwright_js_delayed.py # Browser automation (65 LOC)
├── outputs/                    # Generated data files
│   ├── musicbrainz_search.csv
│   ├── musicbrainz_details.csv
│   ├── details_json/
│   ├── quotes_static.csv
│   ├── quotes_playwright.csv
│   └── deezer_page.json
└── README.md
```

---

## Technical Highlights

### Best Practices Implemented

1. **Rate Limiting & Politeness**
   - All scripts implement delays between requests (0.8-1.05s)
   - Respects server resources and prevents IP bans

2. **Error Handling**
   - Network errors with exponential backoff (Script 1)
   - Defensive parsing with `.get()` for nested data
   - Debug artifact saving for troubleshooting (Script 3)

3. **Session Management**
   - Reusable `requests.Session` objects
   - Custom User-Agent headers
   - Cookie and session ID support

4. **Resume Capability**
   - Tracks completed downloads (Script 1)
   - Prevents redundant API requests
   - Saves progress incrementally

5. **Code Organization**
   - `@dataclass` configuration pattern
   - Clear function separation (fetch/parse/save)
   - Type hints for complex returns

### Common Patterns

All scripts follow consistent architecture:

```python
@dataclass
class Config:
    # Configuration with defaults

def build_session(user_agent: str) -> requests.Session:
    # Session setup

def fetch_data(url: str) -> dict:
    # Data retrieval with error handling

def parse_data(raw_data) -> List[dict]:
    # Extraction logic

def save_data(data, output_path):
    # Persistence

if __name__ == '__main__':
    # Main workflow
```

---

## Output Examples

### MusicBrainz Search Results
```csv
mbid,title,artist,length_ms,score
1dc23cbc-cccc-4275-8db5-813591ff4f65,True Love Waits,Radiohead,369000.0,100
```

### Quotes Data
```csv
quote,author,tags
"The world as we have created it is a process of our thinking...",Albert Einstein,change|deep-thoughts|thinking
```

### Deezer JSON Extract
```json
{
  "APP_STATE": {
    "user": {...},
    "tracks": [...],
    "playlists": [...]
  }
}
```

---

## Skills Demonstrated

### Web Scraping Techniques
- REST API interaction with authentication
- HTML parsing with CSS selectors
- JSON extraction from HTML sources
- Browser automation for dynamic content

### Python Programming
- Modern dataclass patterns
- Type hints and annotations
- Async/await programming
- Error handling strategies
- Session management

### Software Engineering
- Modular function design
- Configuration management
- Rate limiting implementation
- Resume/checkpoint capabilities
- Code organization and documentation

### HTTP & Web Protocols
- User-Agent spoofing
- Session persistence
- Cookie handling
- Retry logic with exponential backoff

---

## Dependencies

```
requests>=2.28.0        # HTTP client
pandas>=1.5.0          # Data manipulation
beautifulsoup4>=4.11.0 # HTML parsing
playwright>=1.30.0     # Browser automation
```

---

## Use Cases

This toolkit demonstrates techniques applicable to:

- **Market Research:** Price monitoring, competitor analysis
- **Content Aggregation:** News scraping, blog post collection
- **Data Science:** Training dataset collection
- **Monitoring:** Website change detection
- **Research:** Academic data gathering

---

## Ethical Considerations

All scripts in this project:
- Respect `robots.txt` guidelines
- Implement polite rate limiting
- Use appropriate User-Agent headers
- Target publicly accessible data only

Always ensure you have permission to scrape a website and comply with its terms of service.

---

## License

MIT License - Feel free to use and modify for educational purposes.

---

## Author

Created as a demonstration of web scraping best practices and modern Python techniques.
