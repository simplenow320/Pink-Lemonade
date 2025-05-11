from app import create_app

app = create_app()

with app.app_context():
    from app.models.scraper import ScraperSource
    count = ScraperSource.query.count()
    print(f"Total foundation sources in database: {count}")
