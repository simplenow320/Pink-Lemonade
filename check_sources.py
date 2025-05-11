from app import create_app

app = create_app()

with app.app_context():
    from app.models.scraper import ScraperSource
    
    # Check for grant portal websites
    grant_portals = ScraperSource.query.filter(
        ScraperSource.name.in_([
            'Grants.gov', 
            'GrantWatch', 
            'Foundation Directory Online (Candid)',
            'GrantStation',
            'FundsforNGOs',
            'Foundation List',
            'Instrumentl',
            'GrantList.org',
            'USGrants.org',
            'CD Publications'
        ])
    ).all()
    
    print(f"Found {len(grant_portals)} grant portal websites:")
    for portal in grant_portals:
        print(f"- {portal.name} ({portal.url})")
