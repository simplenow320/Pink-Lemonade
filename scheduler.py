"""
Scheduler Module for GrantFlow

This module sets up scheduled tasks using the schedule library.
"""

import logging
import threading
import time
import schedule
from app.services.scraper_service import run_scraping_job

# Configure logging
logger = logging.getLogger(__name__)

# Global variables to control the scheduler thread
scheduler_thread = None
scheduler_running = False

def scheduled_scraping_job():
    """
    Function to be called by the scheduler to run the scraping job.
    """
    logger.info("Running scheduled scraping job")
    result = run_scraping_job()
    logger.info(f"Scheduled scraping job completed: Found {result['grants_found']} grants, added {result['grants_added']} new grants")
    return result

def scheduler_loop():
    """
    Run the scheduler loop in a separate thread.
    """
    global scheduler_running
    logger.info("Scheduler thread started")
    
    try:
        while scheduler_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except Exception as e:
        logger.error(f"Error in scheduler loop: {str(e)}")
    
    logger.info("Scheduler thread stopped")

def init_scheduler():
    """
    Initialize the scheduler and set up scheduled jobs.
    """
    global scheduler_thread, scheduler_running
    
    # Clear any existing scheduled jobs
    schedule.clear()
    
    # Schedule the scraping job to run daily at midnight EST (5:00 AM UTC)
    schedule.every().day.at("05:00").do(scheduled_scraping_job)
    logger.info("Scheduling daily scraping job for 05:00 UTC (midnight EST)")
    
    # Start the scheduler thread if it's not already running
    if scheduler_thread is None or not scheduler_thread.is_alive():
        scheduler_running = True
        scheduler_thread = threading.Thread(target=scheduler_loop, name="SchedulerThread")
        scheduler_thread.daemon = True
        scheduler_thread.start()
        logger.info("Scheduler thread started")
    
    return {
        "status": "success",
        "message": "Scheduler initialized successfully"
    }

# Initialize the scheduler when this module is imported
scheduler_status = init_scheduler()