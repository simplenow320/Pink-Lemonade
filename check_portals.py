from app import create_app

app = create_app()

with app.app_context():
    from app.models.scraper import ScraperSource
    
    # Check for grant portal websites using LIKE queries
    portals = []
    for name in ['Grants.gov', 'GrantWatch', 'Foundation Directory', 'GrantStation',
                'FundsforNGOs', 'Foundation List', 'Instrumentl', 'GrantList',
                'USGrants', 'CD Publications']:
        sources = ScraperSource.query.filter(ScraperSource.name.like(f'%{name}%')).all()
        portals.extend(sources)
    
    print(f"Found {len(portals)} grant portal websites:")
    for portal in portals:
        print(f"- {portal.name} ({portal.url})")
