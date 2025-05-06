import os
import logging
import threading
import time
from datetime import datetime, timedelta
import schedule
from app.services.scraper_service import run_scraping_job
from app.models.scraper import ScraperHistory
from app import db

logger = logging.getLogger(__name__)

# Flag to control the scheduler thread
scheduler_running = False
scheduler_thread = None

def initialize_scheduler():
    """Initialize the scheduler for background tasks"""
    global scheduler_running, scheduler_thread
    
    # Stop existing scheduler if running
    if scheduler_running and scheduler_thread and scheduler_thread.is_alive():
        scheduler_running = False
        scheduler_thread.join(timeout=5)
    
    # Set up twice-monthly scraping (1st and 15th of each month)
    schedule.clear()
    
    # Schedule scraping jobs for 1st and 15th of each month at 2 AM
    schedule.every().month.on(1).at("02:00").do(scheduled_scraping_job)
    schedule.every().month.on(15).at("02:00").do(scheduled_scraping_job)
    
    # Start the scheduler thread
    scheduler_running = True
    scheduler_thread = threading.Thread(target=scheduler_loop)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    logger.info("Scheduler initialized with scraping jobs on 1st and 15th of each month")
    
    return {
        "status": "success",
        "message": "Scheduler initialized",
        "next_run": get_next_scheduled_run()
    }

def scheduler_loop():
    """Run the scheduler loop in a separate thread"""
    global scheduler_running
    
    logger.info("Scheduler thread started")
    
    while scheduler_running:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
    
    logger.info("Scheduler thread stopped")

def scheduled_scraping_job():
    """Run the scraping job and record the history"""
    from app import create_app
    
    try:
        # Create app context for database operations
        app = create_app()
        
        with app.app_context():
            logger.info("Running scheduled scraping job")
            
            # Run the scraping job
            result = run_scraping_job()
            
            # Record the scraping history
            history = ScraperHistory(
                start_time=result['start_time'],
                end_time=result['end_time'],
                sources_scraped=result['sources_scraped'],
                grants_found=result['grants_found'],
                grants_added=result['grants_added'],
                status=result['status'],
                error_message=result.get('error_message', '')
            )
            
            db.session.add(history)
            db.session.commit()
            
            logger.info(f"Scheduled scraping job completed: {result['grants_added']} grants added")
            
            return result
    
    except Exception as e:
        logger.error(f"Error in scheduled scraping job: {str(e)}")
        return {"error": str(e), "status": "failed"}

def get_next_scheduled_run():
    """Get the next scheduled run time"""
    next_run = schedule.next_run()
    
    if next_run:
        return next_run.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return "No scheduled runs"

def stop_scheduler():
    """Stop the scheduler thread"""
    global scheduler_running, scheduler_thread
    
    if scheduler_running and scheduler_thread and scheduler_thread.is_alive():
        logger.info("Stopping scheduler thread")
        scheduler_running = False
        scheduler_thread.join(timeout=5)
        
        return {
            "status": "success",
            "message": "Scheduler stopped"
        }
    else:
        return {
            "status": "warning",
            "message": "Scheduler was not running"
        }
