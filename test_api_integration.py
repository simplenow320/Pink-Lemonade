#!/usr/bin/env python
"""Test API integrations to verify they're working"""

from app.services.matching_service import assemble_results, build_tokens
from app.models import Organization
from app import db, create_app

# Create app context
app = create_app()
with app.app_context():
    # Get an organization
    org = Organization.query.first()
    if org:
        print(f"Testing with organization: {org.name}")
        tokens = build_tokens(org.id)
        print(f"Tokens: {tokens}")
        
        # Assemble results from all sources
        results = assemble_results(tokens)
        
        print(f"\nResults summary:")
        print(f"Federal grants: {len(results.get('federal', []))}")
        print(f"Foundation news: {len(results.get('news', []))}")
        
        # Show first federal grant
        if results.get('federal'):
            print(f"\nFirst federal grant:")
            grant = results['federal'][0]
            print(f"  Title: {grant.get('title', 'N/A')[:80]}")
            print(f"  Funder: {grant.get('funder', 'N/A')}")
            
        # Show first news item
        if results.get('news'):
            print(f"\nFirst foundation news:")
            news = results['news'][0]
            print(f"  Title: {news.get('title', 'N/A')[:80]}")
            print(f"  Publisher: {news.get('publisher', 'N/A')}")
    else:
        print("No organization found in database")