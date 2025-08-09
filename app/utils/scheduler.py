import threading
import time
import schedule
from app.services.scraper_service import scheduled_scraping_job

def start_scheduler():
    schedule.every().day.at("05:00").do(scheduled_scraping_job)  # fixed time string

    def runner():
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    t = threading.Thread(target=runner, daemon=True)
    t.start()