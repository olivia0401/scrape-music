"""
Real-time Scheduler for Automated Scraping
Demonstrates: 24/7 automation, job scheduling, error recovery
Simple and production-ready - directly answers "Spinning up automated scraping operations"
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Callable
import json

# Optional: APScheduler for production scheduling
try:
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False

# Simple logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleScheduler:
    """
    Lightweight scheduler for automated scraping

    Production features:
    - Cron-based scheduling (hourly, daily, etc.)
    - Basic error recovery
    - Execution tracking
    """

    def __init__(self):
        if not SCHEDULER_AVAILABLE:
            raise ImportError("Install: pip install apscheduler")

        self.scheduler = BlockingScheduler()
        self.metrics_file = Path("outputs/scheduler_metrics.json")
        self.metrics_file.parent.mkdir(exist_ok=True)

        # Track job execution
        self.job_count = 0
        self.success_count = 0

        logger.info("✅ Scheduler initialized")

    def add_job(self, func: Callable, job_id: str, cron_expr: str):
        """
        Add a scheduled job

        Examples:
            cron_expr="0 * * * *"  -> Every hour
            cron_expr="*/15 * * * *"  -> Every 15 minutes
            cron_expr="0 9 * * *"  -> Daily at 9 AM
        """
        trigger = CronTrigger.from_crontab(cron_expr)

        # Wrap function to track metrics
        def wrapped_job():
            try:
                logger.info(f"🏃 Running job: {job_id}")
                func()
                self.success_count += 1
                logger.info(f"✅ Job completed: {job_id}")
            except Exception as e:
                logger.error(f"❌ Job failed: {job_id} - {e}")
            finally:
                self.job_count += 1
                self._save_metrics()

        self.scheduler.add_job(wrapped_job, trigger, id=job_id)
        logger.info(f"📅 Scheduled job '{job_id}': {cron_expr}")

    def _save_metrics(self):
        """Save simple metrics"""
        metrics = {
            'total_jobs': self.job_count,
            'successful': self.success_count,
            'success_rate': f"{self.success_count/self.job_count*100:.1f}%" if self.job_count > 0 else "N/A",
            'last_run': datetime.now().isoformat()
        }

        with open(self.metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)

    def start(self):
        """Start the scheduler (blocking)"""
        logger.info("🚀 Scheduler started - Press Ctrl+C to stop")
        try:
            self.scheduler.start()
        except KeyboardInterrupt:
            logger.info("⏹️  Scheduler stopped")


# ========== Example Jobs ==========

def scrape_musicbrainz():
    """Example: Run MusicBrainz scraper"""
    logger.info("🎵 Scraping MusicBrainz...")
    # In production: import and run actual scraper
    # from 01_api_musicbrainz import main; main()
    time.sleep(1)  # Simulate work
    logger.info("✅ MusicBrainz complete")


def scrape_quotes():
    """Example: Run quotes scraper"""
    logger.info("📜 Scraping quotes...")
    # from 02_static_html_quotes import main; main()
    time.sleep(0.5)
    logger.info("✅ Quotes complete")


# ========== Main ==========

def main():
    """
    Simple scheduler setup for automated scraping

    Production deployment:
    1. Run on AWS EC2 with: nohup python scheduler.py &
    2. Or use systemd for auto-restart
    3. Monitor logs with: tail -f outputs/scheduler_metrics.json
    """

    if not SCHEDULER_AVAILABLE:
        print("⚠️  Install APScheduler: pip install apscheduler")
        return

    scheduler = SimpleScheduler()

    # Schedule jobs
    scheduler.add_job(scrape_musicbrainz, 'musicbrainz_hourly', '0 * * * *')
    scheduler.add_job(scrape_quotes, 'quotes_every_30min', '*/30 * * * *')

    # Start (runs forever until Ctrl+C)
    scheduler.start()


if __name__ == '__main__':
    main()
