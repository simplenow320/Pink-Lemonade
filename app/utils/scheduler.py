import os
import logging
import threading
import time
import traceback
from datetime import datetime, timedelta
import schedule
from app.services.scraper_service import run_scraping_job
from app.models.scraper import ScraperHistory
from app import db
from typing import Dict, Any, Optional, Union, List

# Configure logger with appropriate level
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Flag to control the scheduler thread
scheduler_running = False
scheduler_thread = None

def initialize_scheduler() -> Dict[str, Any]:
    """
    Initialize the scheduler for background tasks.
    
    This function sets up the scheduler to run the scraping job daily at 
    midnight EST (5 AM UTC). It handles stopping any existing scheduler
    thread before starting a new one.
    
    Returns:
        Dict[str, Any]: Status information about the scheduler initialization.
            - status: "success" or "error"
            - message: Description of the action taken
            - next_run: Timestamp of the next scheduled run
            - error: Error message (only included if status is "error")
    """
    global scheduler_running, scheduler_thread
    
    logger.info("Initializing scheduler")
    
    try:
        # Stop existing scheduler if running
        if scheduler_running and scheduler_thread and scheduler_thread.is_alive():
            logger.info("Stopping existing scheduler thread")
            scheduler_running = False
            scheduler_thread.join(timeout=5)
            if scheduler_thread.is_alive():
                logger.warning("Failed to gracefully stop existing scheduler thread - proceeding anyway")
        
        # Clear all existing scheduled jobs
        logger.debug("Clearing existing scheduled jobs")
        schedule.clear()
        
        # Schedule scraping job to run every day at midnight EST (5 AM UTC)
        logger.info("Scheduling daily scraping job for 05:00 UTC (midnight EST)")
        schedule.every().day.at("05:00").do(scheduled_scraping_job)
        
        # Log details about the next scheduled run
        next_run = get_next_scheduled_run()
        logger.info(f"Next scheduled scraping job: {next_run}")
        
        # Start the scheduler thread
        logger.info("Starting scheduler thread")
        scheduler_running = True
        scheduler_thread = threading.Thread(target=scheduler_loop, name="SchedulerThread")
        scheduler_thread.daemon = True
        scheduler_thread.start()
        
        logger.info("Scheduler successfully initialized")
        
        return {
            "status": "success",
            "message": "Scheduler initialized successfully",
            "next_run": next_run
        }
    
    except Exception as e:
        error_msg = f"Failed to initialize scheduler: {str(e)}"
        logger.error(error_msg)
        logger.debug(f"Traceback: {traceback.format_exc()}")
        
        return {
            "status": "error",
            "message": "Failed to initialize scheduler",
            "error": str(e),
            "next_run": "Unknown"
        }

def scheduler_loop() -> None:
    """
    Run the scheduler loop in a separate thread.
    
    This function runs in a background thread and checks for scheduled jobs
    every minute. It continues running until the scheduler_running flag is set
    to False.
    """
    global scheduler_running
    
    logger.info("Scheduler thread started")
    loop_count = 0
    
    try:
        while scheduler_running:
            try:
                # Run any pending scheduled jobs
                pending_jobs = len(schedule.get_jobs())
                logger.debug(f"Checking for pending jobs (Count: {pending_jobs})")
                schedule.run_pending()
                
                # Log heartbeat every hour (60 iterations)
                loop_count += 1
                if loop_count >= 60:
                    logger.info(f"Scheduler heartbeat - Next run: {get_next_scheduled_run()}")
                    loop_count = 0
                
                # Sleep for a minute before checking again
                time.sleep(60)
            
            except Exception as e:
                # Catch exceptions in the loop itself to prevent thread termination
                logger.error(f"Error in scheduler loop iteration: {str(e)}")
                logger.debug(f"Traceback: {traceback.format_exc()}")
                time.sleep(60)  # Sleep and continue the loop
    
    except Exception as e:
        # This should only happen if there's a critical error that breaks the loop
        logger.critical(f"Scheduler loop terminated unexpectedly: {str(e)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
    
    finally:
        logger.info("Scheduler thread stopped")

def scheduled_scraping_job() -> Dict[str, Any]:
    """
    Run the scraping job and record the history.
    
    This function is executed by the scheduler at the scheduled time.
    It creates a new app context, runs the scraping job, and records
    the results in the database.
    
    Returns:
        Dict[str, Any]: Results of the scraping job.
    """
    from app import create_app
    job_id = datetime.now().strftime("%Y%m%d%H%M%S")
    
    logger.info(f"Starting scheduled scraping job [{job_id}]")
    start_time = datetime.now()
    history = None
    
    try:
        # Create app context for database operations
        logger.debug(f"Creating app context for job [{job_id}]")
        app = create_app()
        
        with app.app_context():
            logger.info(f"Running scraping job [{job_id}]")
            
            # Run the scraping job (with internet-wide grant search)
            result = run_scraping_job(include_web_search=True)
            logger.info(f"Scraping job completed [{job_id}]: {result['status']} (including internet-wide search)")
            logger.debug(f"Scraping result details: {result}")
            
            # Record the scraping history
            logger.debug(f"Recording scraping history for job [{job_id}]")
            try:
                history = ScraperHistory(
                    start_time=result.get('start_time', start_time),
                    end_time=result.get('end_time', datetime.now()),
                    sources_scraped=result.get('sources_scraped', 0),
                    grants_found=result.get('grants_found', 0),
                    grants_added=result.get('grants_added', 0),
                    status=result.get('status', 'unknown'),
                    error_message=result.get('error_message', '')
                )
                
                db.session.add(history)
                db.session.commit()
                logger.info(f"Scraping history recorded [{job_id}]: ID {history.id if history else 'unknown'}")
            
            except Exception as db_error:
                logger.error(f"Failed to record scraping history [{job_id}]: {str(db_error)}")
                logger.debug(f"Traceback: {traceback.format_exc()}")
                if db.session.is_active:
                    db.session.rollback()
            
            summary = (f"Scheduled scraping job [{job_id}] completed: "
                      f"{result.get('grants_added', 0)} grants added, "
                      f"{result.get('sources_scraped', 0)} sources scraped")
            logger.info(summary)
            
            return result
    
    except Exception as e:
        end_time = datetime.now()
        error_msg = f"Error in scheduled scraping job [{job_id}]: {str(e)}"
        logger.error(error_msg)
        logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Try to record the failure in the database if possible
        try:
            if 'app' in locals():
                with app.app_context():
                    failure_history = ScraperHistory(
                        start_time=start_time,
                        end_time=end_time,
                        sources_scraped=0,
                        grants_found=0,
                        grants_added=0,
                        status="failed",
                        error_message=str(e)
                    )
                    
                    db.session.add(failure_history)
                    db.session.commit()
                    logger.info(f"Recorded failure for job [{job_id}]")
        except Exception as db_error:
            logger.error(f"Failed to record job failure [{job_id}]: {str(db_error)}")
        
        return {
            "start_time": start_time,
            "end_time": end_time,
            "sources_scraped": 0,
            "grants_found": 0,
            "grants_added": 0,
            "status": "failed",
            "error_message": str(e)
        }

def get_next_scheduled_run() -> str:
    """
    Get the next scheduled run time.
    
    Returns:
        str: Formatted timestamp of the next scheduled run, or a message
             indicating no scheduled runs.
    """
    try:
        next_run = schedule.next_run()
        
        if next_run:
            formatted_time = next_run.strftime("%Y-%m-%d %H:%M:%S UTC")
            logger.debug(f"Next scheduled run: {formatted_time}")
            return formatted_time
        else:
            logger.warning("No scheduled runs found")
            return "No scheduled runs"
    
    except Exception as e:
        error_msg = f"Error determining next scheduled run: {str(e)}"
        logger.error(error_msg)
        return "Error determining next run time"

def stop_scheduler() -> Dict[str, Any]:
    """
    Stop the scheduler thread.
    
    This function stops the scheduler thread by setting the scheduler_running
    flag to False and waiting for the thread to terminate.
    
    Returns:
        Dict[str, Any]: Status information about the scheduler stopping.
            - status: "success", "warning", or "error"
            - message: Description of the action taken
            - error: Error message (only included if status is "error")
    """
    global scheduler_running, scheduler_thread
    
    logger.info("Request to stop scheduler received")
    
    try:
        if scheduler_running and scheduler_thread and scheduler_thread.is_alive():
            logger.info("Stopping scheduler thread")
            scheduler_running = False
            
            # Wait for the thread to terminate
            scheduler_thread.join(timeout=5)
            
            # Check if the thread actually terminated
            if scheduler_thread.is_alive():
                logger.warning("Scheduler thread did not terminate gracefully within timeout")
                return {
                    "status": "warning",
                    "message": "Scheduler marked for shutdown but thread did not terminate within timeout"
                }
            else:
                logger.info("Scheduler thread successfully stopped")
                return {
                    "status": "success",
                    "message": "Scheduler stopped successfully"
                }
        else:
            logger.info("No active scheduler thread to stop")
            return {
                "status": "warning",
                "message": "Scheduler was not running"
            }
    
    except Exception as e:
        error_msg = f"Error stopping scheduler: {str(e)}"
        logger.error(error_msg)
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "message": "Failed to stop scheduler",
            "error": str(e)
        }
