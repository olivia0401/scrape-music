"""
LLM-Powered Trend Analysis Engine
Demonstrates: Agentic coding tools, LLM integration, automated insights
Skills: OpenAI API, prompt engineering, data enrichment with AI
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

# LLM integration (install: pip install openai)
try:
    import openai
except ImportError:
    print("⚠️  Install openai: pip install openai")
    openai = None


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMTrendAnalyzer:
    """
    Use LLMs to analyze scraped data and extract insights

    This demonstrates "agentic coding" - using AI to automate:
    1. Data cleaning and normalization
    2. Trend identification
    3. Insight generation
    4. Anomaly detection
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize LLM client

        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model: Model to use (gpt-4o-mini is cost-effective)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model

        if openai and self.api_key:
            openai.api_key = self.api_key
            self.enabled = True
            logger.info(f"✅ LLM analyzer initialized (model: {model})")
        else:
            self.enabled = False
            logger.warning("⚠️  LLM disabled (missing API key or openai package)")

    def generate_insights(self, data: pd.DataFrame, max_samples: int = 20) -> Dict:
        """
        Use LLM to analyze scraped data and generate insights

        Args:
            data: Scraped data (e.g., from MusicBrainz, quotes, etc.)
            max_samples: Number of samples to send to LLM (cost control)

        Returns:
            Dictionary with insights, trends, and recommendations
        """
        if not self.enabled:
            return {'error': 'LLM not available'}

        # Prepare data summary for LLM
        data_summary = self._prepare_data_summary(data, max_samples)

        # Prompt engineering for trend analysis
        prompt = f"""
You are a data analyst specializing in trend identification and insight generation.

Analyze this scraped data and provide:
1. **Key Trends**: What patterns do you observe?
2. **Anomalies**: Any unusual or surprising data points?
3. **Predictions**: Based on this data, what might happen next?
4. **Recommendations**: Actions to take based on these insights

Data Summary:
{json.dumps(data_summary, indent=2)}

Format your response as JSON with keys: trends, anomalies, predictions, recommendations
"""

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data analyst expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )

            insights_text = response.choices[0].message['content']

            # Parse JSON response
            # Handle cases where LLM wraps JSON in markdown
            if '```json' in insights_text:
                insights_text = insights_text.split('```json')[1].split('```')[0].strip()
            elif '```' in insights_text:
                insights_text = insights_text.split('```')[1].split('```')[0].strip()

            insights = json.loads(insights_text)

            logger.info("✅ LLM insights generated")
            return insights

        except Exception as e:
            logger.error(f"❌ LLM analysis failed: {e}")
            return {'error': str(e)}

    def clean_data_with_llm(self, raw_text: str) -> str:
        """
        Use LLM for intelligent data cleaning

        Example: Normalize artist names, fix typos, standardize formats
        """
        if not self.enabled:
            return raw_text

        prompt = f"""
Clean and normalize this text data:
- Fix typos and misspellings
- Standardize formatting
- Remove duplicates
- Maintain original meaning

Input: {raw_text}

Return only the cleaned text.
"""

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )

            return response.choices[0].message['content'].strip()

        except Exception as e:
            logger.error(f"❌ Data cleaning failed: {e}")
            return raw_text

    def detect_viral_potential(self, content: str, metadata: Dict) -> Dict:
        """
        Predict if content has viral potential using LLM

        Args:
            content: Text content (song lyrics, post text, etc.)
            metadata: Additional context (artist, genre, timestamp, etc.)

        Returns:
            Viral score and reasoning
        """
        if not self.enabled:
            return {'score': 0, 'reasoning': 'LLM not available'}

        prompt = f"""
Analyze this content for viral potential on social media.

Content: {content}
Metadata: {json.dumps(metadata)}

Consider:
- Emotional resonance
- Relatability
- Timing/relevance
- Shareability factors
- Novelty/uniqueness

Provide:
1. Viral score (0-100)
2. Key factors (positive and negative)
3. Recommendations to increase virality

Format as JSON: {{"score": 0-100, "factors": [...], "recommendations": [...]}}
"""

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=400
            )

            result_text = response.choices[0].message['content']

            # Extract JSON
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()

            return json.loads(result_text)

        except Exception as e:
            logger.error(f"❌ Viral prediction failed: {e}")
            return {'score': 0, 'reasoning': str(e)}

    def _prepare_data_summary(self, data: pd.DataFrame, max_samples: int) -> Dict:
        """Prepare concise data summary for LLM"""
        summary = {
            'total_records': len(data),
            'columns': list(data.columns),
            'sample_data': data.head(max_samples).to_dict(orient='records'),
            'statistics': {}
        }

        # Add basic statistics for numeric columns
        numeric_cols = data.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            summary['statistics'][col] = {
                'mean': float(data[col].mean()),
                'median': float(data[col].median()),
                'std': float(data[col].std())
            }

        return summary


# ========== Example Usage with Existing Scrapers ==========

def analyze_musicbrainz_data():
    """Analyze MusicBrainz scraping results with LLM"""

    # Load scraped data
    csv_path = Path('outputs/musicbrainz_search.csv')
    if not csv_path.exists():
        logger.error("❌ No MusicBrainz data found. Run 01_api_musicbrainz.py first")
        return

    df = pd.read_csv(csv_path)
    logger.info(f"📊 Loaded {len(df)} MusicBrainz records")

    # Initialize LLM analyzer
    analyzer = LLMTrendAnalyzer()

    if not analyzer.enabled:
        logger.warning("⚠️  LLM analysis skipped (set OPENAI_API_KEY environment variable)")
        return

    # Generate insights
    insights = analyzer.generate_insights(df)

    # Save insights
    output_path = Path('outputs/llm_insights_musicbrainz.json')
    with open(output_path, 'w') as f:
        json.dump(insights, f, indent=2)

    logger.info(f"💡 Insights saved to {output_path}")

    # Print summary
    if 'trends' in insights:
        print("\n📈 Key Trends:")
        for i, trend in enumerate(insights.get('trends', []), 1):
            print(f"  {i}. {trend}")

    if 'recommendations' in insights:
        print("\n💡 Recommendations:")
        for i, rec in enumerate(insights.get('recommendations', []), 1):
            print(f"  {i}. {rec}")


def analyze_quotes_sentiment():
    """Analyze quotes data for themes and sentiment"""

    csv_path = Path('outputs/quotes_static.csv')
    if not csv_path.exists():
        logger.error("❌ No quotes data found. Run 02_static_html_quotes.py first")
        return

    df = pd.read_csv(csv_path)
    analyzer = LLMTrendAnalyzer()

    if not analyzer.enabled:
        return

    # Analyze each quote's viral potential
    results = []
    for _, row in df.head(5).iterrows():  # Limit to 5 for demo (cost control)
        viral_analysis = analyzer.detect_viral_potential(
            content=row['quote'],
            metadata={'author': row['author'], 'tags': row.get('tags', '')}
        )

        results.append({
            'quote': row['quote'][:50] + '...',
            'author': row['author'],
            'viral_score': viral_analysis.get('score', 0),
            'factors': viral_analysis.get('factors', [])
        })

    # Save results
    output_df = pd.DataFrame(results)
    output_path = Path('outputs/quotes_viral_analysis.csv')
    output_df.to_csv(output_path, index=False)

    logger.info(f"💡 Viral analysis saved to {output_path}")
    print(output_df[['author', 'viral_score']])


# ========== Main Execution ==========

def main():
    """
    Demonstrate LLM-powered data analysis

    This shows "agentic coding" capabilities:
    - Automated insight generation
    - Intelligent data cleaning
    - Predictive analysis
    """

    print("""
    🤖 LLM-Powered Trend Analyzer

    This demonstrates using LLMs for:
    1. Automated data analysis
    2. Trend identification
    3. Viral potential prediction
    4. Intelligent data cleaning

    Set OPENAI_API_KEY environment variable to enable.
    """)

    # Example 1: Analyze MusicBrainz data
    print("\n📊 Analyzing MusicBrainz data...")
    analyze_musicbrainz_data()

    # Example 2: Analyze quotes for viral potential
    print("\n💭 Analyzing quotes for viral potential...")
    analyze_quotes_sentiment()

    print("\n✨ Analysis complete!")


if __name__ == '__main__':
    main()
