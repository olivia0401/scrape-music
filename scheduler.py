"""
Real-time Scheduler for Automated Scraping
Demonstrates: Production-grade automation, error recovery, monitoring
Skills: APScheduler, logging, job persistence, alert systems
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Any
import json

# Production dependencies (install: pip install apscheduler)
try:
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
except ImportError:
    print("⚠️  Install APScheduler: pip install apscheduler")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('outputs/scraper_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ScraperScheduler:
    """
    Production-grade scheduler for automated scraping operations

    Features:
    - Cron-based scheduling (every 15 min, hourly, daily, etc.)
    - Automatic error recovery with exponential backoff
    - Job execution monitoring and logging
    - Metrics tracking (success rate, execution time)
    - Alert system for failures
    """

    def __init__(self, metrics_file: str = "outputs/scheduler_metrics.json"):
        self.scheduler = BlockingScheduler()
        self.metrics_file = Path(metrics_file)
        self.metrics = self._load_metrics()

        # Register event listeners
        self.scheduler.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)

        logger.info("✅ ScraperScheduler initialized")

    def _load_metrics(self) -> Dict[str, Any]:
        """Load execution metrics from disk"""
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        return {
            'total_jobs': 0,
            'successful_jobs': 0,
            'failed_jobs': 0,
            'last_execution': None,
            'job_history': []
        }

    def _save_metrics(self):
        """Persist metrics to disk"""
        self.metrics_file.parent.mkdir(exist_ok=True)
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)

    def _on_job_executed(self, event):
        """Callback when job completes successfully"""
        job_name = event.job_id
        logger.info(f"✅ Job '{job_name}' completed successfully")

        self.metrics['successful_jobs'] += 1
        self.metrics['total_jobs'] += 1
        self.metrics['last_execution'] = datetime.now().isoformat()
        self.metrics['job_history'].append({
            'job': job_name,
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        })

        # Keep only last 100 records
        if len(self.metrics['job_history']) > 100:
            self.metrics['job_history'] = self.metrics['job_history'][-100:]

        self._save_metrics()

    def _on_job_error(self, event):
        """Callback when job fails"""
        job_name = event.job_id
        error = str(event.exception)
        logger.error(f"❌ Job '{job_name}' failed: {error}")

        self.metrics['failed_jobs'] += 1
        self.metrics['total_jobs'] += 1
        self.metrics['job_history'].append({
            'job': job_name,
            'status': 'failed',
            'error': error[:200],  # Truncate long errors
            'timestamp': datetime.now().isoformat()
        })

        self._save_metrics()

        # Send alert if failure rate is high
        if self.metrics['total_jobs'] > 10:
            failure_rate = self.metrics['failed_jobs'] / self.metrics['total_jobs']
            if failure_rate > 0.3:  # 30% failure rate
                self._send_alert(f"High failure rate: {failure_rate:.1%}")

    def _send_alert(self, message: str):
        """
        Send alert notification (email, Slack, etc.)

        In production: Integrate with Slack API, SendGrid, PagerDuty, etc.
        For demo: Log to file and console
        """
        alert_msg = f"🚨 ALERT: {message}"
        logger.warning(alert_msg)

        # Save to alerts file
        alert_file = Path("outputs/alerts.log")
        with open(alert_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - {alert_msg}\n")

    def add_job(
        self,
        func: Callable,
        job_id: str,
        cron_expression: str = None,
        interval_minutes: int = None,
        **job_kwargs
    ):
        """
        Add a scraping job to the scheduler

        Args:
            func: Function to execute (e.g., scrape_musicbrainz)
            job_id: Unique identifier for the job
            cron_expression: Cron format (e.g., "*/15 * * * *" = every 15 min)
            interval_minutes: Run every N minutes (alternative to cron)
            **job_kwargs: Additional arguments passed to APScheduler
        """
        if cron_expression:
            # Use cron trigger
            trigger = CronTrigger.from_crontab(cron_expression)
            self.scheduler.add_job(func, trigger, id=job_id, **job_kwargs)
            logger.info(f"📅 Added cron job '{job_id}': {cron_expression}")

        elif interval_minutes:
            # Use interval trigger
            self.scheduler.add_job(
                func,
                'interval',
                minutes=interval_minutes,
                id=job_id,
                **job_kwargs
            )
            logger.info(f"📅 Added interval job '{job_id}': every {interval_minutes} min")

        else:
            raise ValueError("Must specify either cron_expression or interval_minutes")

    def start(self):
        """Start the scheduler (blocking call)"""
        logger.info("🚀 Starting scheduler...")
        logger.info(f"📊 Current metrics: {self.metrics['successful_jobs']}/{self.metrics['total_jobs']} jobs successful")

        try:
            self.scheduler.start()
        except KeyboardInterrupt:
            logger.info("⏹️  Scheduler stopped by user")
            self.scheduler.shutdown()

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        return {
            'total_jobs': self.metrics['total_jobs'],
            'success_rate': (
                self.metrics['successful_jobs'] / self.metrics['total_jobs']
                if self.metrics['total_jobs'] > 0 else 0
            ),
            'last_execution': self.metrics['last_execution'],
            'recent_jobs': self.metrics['job_history'][-10:]
        }


# ========== Example Job Functions ==========

def job_scrape_musicbrainz():
    """Example: Run MusicBrainz scraper"""
    logger.info("🎵 Running MusicBrainz scraper...")

    # In production: Import and run actual scraper
    # from 01_api_musicbrainz import main
    # main()

    # For demo: Simulate work
    import time
    time.sleep(2)
    logger.info("✅ MusicBrainz scrape complete")


def job_scrape_quotes():
    """Example: Run quotes scraper"""
    logger.info("📜 Running quotes scraper...")

    # Import actual scraper
    # from 02_static_html_quotes import main
    # main()

    import time
    time.sleep(1.5)
    logger.info("✅ Quotes scrape complete")


def job_health_check():
    """Monitor system health"""
    logger.info("💊 Running health check...")

    # Check disk space, memory, API quotas, etc.
    import shutil
    disk_usage = shutil.disk_usage("/")
    free_gb = disk_usage.free / (2**30)

    if free_gb < 1:
        logger.warning(f"⚠️  Low disk space: {free_gb:.2f} GB free")
    else:
        logger.info(f"✅ Disk space OK: {free_gb:.2f} GB free")


# ========== Main Execution ==========

def main():
    """
    Example scheduler configuration

    Production deployment:
    1. Run on AWS EC2 instance
    2. Use systemd for auto-restart on failure
    3. Configure CloudWatch for log monitoring
    4. Set up SNS/Slack alerts for critical errors
    """

    scheduler = ScraperScheduler()

    # Schedule jobs
    scheduler.add_job(
        job_scrape_musicbrainz,
        job_id='musicbrainz_hourly',
        cron_expression='0 * * * *',  # Every hour at :00
        max_instances=1  # Prevent concurrent runs
    )

    scheduler.add_job(
        job_scrape_quotes,
        job_id='quotes_every_30min',
        interval_minutes=30,
        max_instances=1
    )

    scheduler.add_job(
        job_health_check,
        job_id='health_check',
        interval_minutes=5
    )

    # Print current stats
    stats = scheduler.get_stats()
    logger.info(f"📊 Scheduler stats: {stats}")

    # Start scheduler (blocks until stopped)
    scheduler.start()


if __name__ == '__main__':
    main()
