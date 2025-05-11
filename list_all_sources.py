from app import create_app

app = create_app()

with app.app_context():
    from app.models.scraper import ScraperSource
    
    sources = ScraperSource.query.all()
    
    print(f"Total sources: {len(sources)}")
    for source in sources:
        print(f"- {source.name} ({source.url})")
