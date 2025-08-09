import threading
import time
import schedule
from app.services.scraper_service import scheduled_scraping_job
from app.services.mode import enforce_live_mode

# Ensure scraping only runs in LIVE mode
@enforce_live_mode()
def live_scheduled_scraping_job():
    return scheduled_scraping_job()

def start_scheduler():
    schedule.every().day.at("05:00").do(live_scheduled_scraping_job)

    def runner():
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    t = threading.Thread(target=runner, daemon=True)
    t.start()