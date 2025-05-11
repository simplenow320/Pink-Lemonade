"""
Scheduler Module for GrantFlow

This module sets up scheduled tasks using APScheduler.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.scraper_service import run_scraping_job

# Configure logging
logger = logging.getLogger(__name__)

def init_scheduler():
    """
    Initialize the APScheduler and set up scheduled jobs.
    """
    scheduler = BackgroundScheduler()
    
    # Add job to run scrape_grants() every night at 2:00 AM
    scheduler.add_job(
        run_scraping_job,
        trigger='cron',
        hour=2,
        minute=0,
        id='nightly_scrape'
    )
    
    # Log that the job has been scheduled
    logger.info("Scheduled nightly scrape at 02:00")
    
    # Start the scheduler
    scheduler.start()
    
    return scheduler

# Initialize the scheduler when this module is imported
scheduler = init_scheduler()