# Web Scraping Lab: Production-Grade Data Intelligence System

A comprehensive demonstration of modern web scraping techniques with **real-time automation**, **AWS deployment**, and **LLM-powered analytics**. This project showcases the complete pipeline from creative data acquisition to production infrastructure and AI-driven insights.

## 🎯 What This Demonstrates

**For Data Scientist Roles:**
- ✅ Creative scraping techniques for hard-to-reach data sources
- ✅ Production infrastructure (AWS EC2, S3, CloudWatch)
- ✅ Real-time automated data collection (24/7 operation)
- ✅ LLM integration for agentic data workflows
- ✅ Monitoring & alerting systems

## Overview

**Core Scrapers:** 4 production-ready scripts
**Infrastructure:** AWS deployment + real-time scheduling
**AI Integration:** LLM-powered trend analysis
**Total Code:** 1,200+ lines
**Status:** Production-ready with cloud deployment capabilities

### 🚀 New Production Features

| Feature | File | Description |
|---------|------|-------------|
| **Real-Time Scheduling** | `scheduler.py` | APScheduler with job monitoring, metrics tracking, and automated alerts |
| **AWS Deployment** | `aws_deploy.py` | EC2 provisioning, S3 storage, CloudWatch monitoring setup |
| **LLM Analytics** | `llm_trends.py` | AI-powered trend analysis, viral prediction, automated insights |

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

## 🚀 Production Features Deep Dive

### Real-Time Scheduling (`scheduler.py`)

Automated 24/7 scraping operations with production-grade reliability:

```python
from scheduler import ScraperScheduler

scheduler = ScraperScheduler()

# Schedule hourly scraping
scheduler.add_job(
    scrape_musicbrainz,
    job_id='musicbrainz_hourly',
    cron_expression='0 * * * *',  # Every hour
    max_instances=1
)

scheduler.start()  # Runs until stopped
```

**Features:**
- ✅ Cron-based scheduling (every 15 min, hourly, daily)
- ✅ Automatic error recovery with exponential backoff
- ✅ Execution metrics tracking (success rate, timing)
- ✅ Alert system for high failure rates
- ✅ Job history persistence (last 100 executions)
- ✅ Health monitoring

**Use Cases:**
- Real-time music trend tracking
- Social media viral content detection
- Continuous price monitoring

---

### AWS Deployment (`aws_deploy.py`)

One-click deployment to AWS cloud infrastructure:

```python
from aws_deploy import AWSDeploymentManager

manager = AWSDeploymentManager(region='us-east-1')

# 1. Create S3 bucket for data storage
manager.create_data_bucket('scraper-data-2025')

# 2. Launch EC2 instance with auto-setup
instance_id = manager.launch_scraper_instance(
    instance_name='scraper-production',
    instance_type='t2.micro'  # Free tier
)

# 3. Set up CloudWatch monitoring
manager.setup_monitoring(instance_id)

# 4. Upload data to S3
manager.upload_to_s3(local_file, bucket, s3_key)
```

**Features:**
- ✅ EC2 instance provisioning with user data scripts
- ✅ S3 data storage with lifecycle policies (auto-archive after 90 days)
- ✅ CloudWatch alarms (CPU, disk usage)
- ✅ IAM role management
- ✅ Security group configuration
- ✅ Automatic dependency installation

**Infrastructure:**
- EC2 t2.micro (free tier eligible)
- S3 with versioning enabled
- CloudWatch metrics & alarms
- Auto-scaling ready

---

### LLM-Powered Analytics (`llm_trends.py`)

AI-driven insights and automated data analysis:

```python
from llm_trends import LLMTrendAnalyzer

analyzer = LLMTrendAnalyzer(model='gpt-4o-mini')

# Analyze scraped data
insights = analyzer.generate_insights(df)
# Returns: {
#   'trends': [...],
#   'anomalies': [...],
#   'predictions': [...],
#   'recommendations': [...]
# }

# Predict viral potential
viral_score = analyzer.detect_viral_potential(
    content="Amazing new song lyrics...",
    metadata={'artist': 'Artist Name', 'genre': 'Pop'}
)
# Returns: {'score': 85, 'factors': [...], 'recommendations': [...]}
```

**Agentic Capabilities:**
- ✅ Automated trend identification
- ✅ Anomaly detection
- ✅ Viral potential prediction
- ✅ Intelligent data cleaning (fix typos, normalize formats)
- ✅ Insight generation for business decisions

**Integration:**
- GPT-4 / GPT-4o-mini
- Prompt engineering for data analysis
- Cost-optimized (sample limiting)

---

## Skills Demonstrated

### 🎯 Data Collection & Engineering
- **Creative Scraping:** Beyond standard APIs (embedded JSON extraction, brace-matching algorithms)
- **Real-Time Systems:** 24/7 automated collection with job scheduling
- **Hard-to-Reach Data:** Custom solutions for non-standard data sources
- **Error Recovery:** Exponential backoff, resume capabilities, health monitoring

### ☁️ Cloud & Infrastructure
- **AWS Deployment:** EC2, S3, CloudWatch integration
- **Infrastructure as Code:** Automated provisioning with boto3
- **Monitoring & Alerts:** CloudWatch alarms, custom metrics
- **Cost Optimization:** Free tier usage, lifecycle policies

### 🤖 AI/ML Integration
- **LLM Engineering:** GPT-4 integration for data analysis
- **Agentic Workflows:** AI-powered data cleaning and insights
- **Prompt Engineering:** Structured prompts for reliable outputs
- **Viral Prediction:** ML-driven content analysis

### 🐍 Python & Software Engineering
- **Production Code:** Error handling, logging, metrics tracking
- **Async Programming:** Concurrent operations (Playwright)
- **Design Patterns:** Factory, Strategy, Observer patterns
- **Code Quality:** Type hints, dataclasses, modular design

---

## Installation & Usage

### Quick Start (Basic Scrapers)

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install

# Run individual scrapers
python 01_api_musicbrainz.py
python 02_static_html_quotes.py
python 03_xhr_json_deezer_api.py
python 04_playwright_js_delayed.py
```

### Production Setup (Real-Time + AWS)

```bash
# 1. Set up environment variables
export OPENAI_API_KEY="your-key"  # For LLM analytics
export AWS_ACCESS_KEY_ID="your-key"  # For AWS deployment
export AWS_SECRET_ACCESS_KEY="your-secret"

# 2. Run scheduler for automated scraping
python scheduler.py

# 3. Deploy to AWS (one-time setup)
python aws_deploy.py

# 4. Analyze data with LLM
python llm_trends.py
```

---

## Dependencies

```bash
# Core scraping
requests>=2.28.0
pandas>=1.5.0
beautifulsoup4>=4.11.0
playwright>=1.30.0

# Production infrastructure
apscheduler>=3.10.0        # Real-time scheduling
boto3>=1.26.0              # AWS SDK

# LLM & AI
openai>=1.0.0              # AI-powered analysis

# See requirements.txt for full list
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
