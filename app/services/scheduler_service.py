"""
Scheduled Jobs Service for Grant Fetching
"""
import schedule
import time
import threading
import logging
from datetime import datetime
from app.services.grant_fetcher import GrantFetcher

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.grant_fetcher = GrantFetcher()
        self.running = False

    def daily_grant_fetch(self):
        """Fetch grants daily at 3 AM UTC"""
        try:
            logger.info("Starting scheduled grant fetch")
            result = self.grant_fetcher.fetch_all_grants(limit=100)
            logger.info(f"Scheduled fetch complete: {result}")
        except Exception as e:
            logger.error(f"Scheduled fetch failed: {e}")

    def start(self):
        """Start the scheduler"""
        if self.running:
            return

        self.running = True

        # Schedule daily fetch at 3 AM UTC
        schedule.every().day.at("03:00").do(self.daily_grant_fetch)

        # Run in background thread
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(60)

        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
        logger.info("Scheduler started - daily fetch at 3 AM UTC")

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        schedule.clear()
        logger.info("Scheduler stopped")