"""
Automated Grant Fetching Scheduler
Runs daily at 3 AM UTC to fetch new grants
"""
import schedule
import time
import threading
import logging
import sys
from datetime import datetime

# Configure logging to ensure visibility
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(name)s: %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.running = False
        self.thread = None
        self.last_run = None
        self.next_run = None
        
    def fetch_grants_job(self):
        """Job that runs daily to fetch grants"""
        self.last_run = datetime.utcnow()
        print(f"🔄 SCHEDULER: Starting automated grant fetch at {self.last_run.isoformat()}")
        logger.info("Starting automated grant fetch...")
        
        try:
            from app.services.grant_fetcher import GrantFetcher
            fetcher = GrantFetcher()
            result = fetcher.fetch_all_grants(limit=100)
            
            print(f"✅ SCHEDULER: Fetch complete - {result.get('fetched', 0)} fetched, {result.get('stored', 0)} stored")
            logger.info(f"Automated fetch complete: {result}")
        except Exception as e:
            print(f"❌ SCHEDULER ERROR: {e}")
            logger.error(f"Automated fetch failed: {e}")
    
    def run_scheduler(self):
        """Run the scheduler in a loop"""
        print("🔄 SCHEDULER: Background thread started, checking every minute")
        logger.info("Scheduler thread started")
        
        while self.running:
            schedule.run_pending()
            
            # Update next run time
            jobs = schedule.get_jobs()
            if jobs:
                self.next_run = jobs[0].next_run
                
            time.sleep(60)  # Check every minute
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            print("⚠️ SCHEDULER: Already running")
            logger.warning("Scheduler already running")
            return
            
        # Schedule daily fetch at 3 AM UTC
        schedule.every().day.at("03:00").do(self.fetch_grants_job)
        
        # Calculate next run
        jobs = schedule.get_jobs()
        if jobs:
            self.next_run = jobs[0].next_run
            if self.next_run:
                print(f"📅 SCHEDULER: Next automated fetch at {self.next_run.strftime('%Y-%m-%d %H:%M UTC')}")
        
        print("✅ SCHEDULER: Daily grant fetching scheduled at 3:00 AM UTC")
        logger.info("Scheduled grant fetching at 3:00 AM UTC daily")
        
        # Start scheduler in background thread
        self.running = True
        self.thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.thread.start()
        
        print("✅ SCHEDULER: Service started successfully")
        logger.info("Scheduler service started successfully")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("🛑 SCHEDULER: Service stopped")
        logger.info("Scheduler service stopped")
    
    def get_status(self):
        """Get scheduler status"""
        return {
            'running': self.running,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None
        }
