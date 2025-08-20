#!/usr/bin/env python
"""Load organizations from CSV or JSON for production use"""

import os
import sys
import json
import csv
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Organization

def load_organizations_from_json(filepath):
    """Load organizations from JSON file"""
    app = create_app()
    
    with app.app_context():
        try:
            with open(filepath, 'r') as f:
                orgs_data = json.load(f)
            
            loaded = 0
            for org_data in orgs_data:
                # Check if org already exists
                existing = Organization.query.filter_by(
                    ein=org_data.get('ein')
                ).first() if org_data.get('ein') else None
                
                if not existing:
                    org = Organization()
                    org.name = org_data.get('name')
                    org.legal_name = org_data.get('legal_name', org_data.get('name'))
                    org.ein = org_data.get('ein')
                    org.mission = org_data.get('mission')
                    org.description = org_data.get('description')
                    org.website = org_data.get('website')
                    org.email = org_data.get('email')
                    org.phone = org_data.get('phone')
                    org.address = org_data.get('address')
                    org.city = org_data.get('city')
                    org.state = org_data.get('state')
                    org.zip_code = org_data.get('zip_code')
                    org.year_founded = org_data.get('year_founded')
                    org.annual_budget = org_data.get('annual_budget')
                    org.staff_size = org_data.get('staff_size')
                    org.tax_status = org_data.get('tax_status', '501c3')
                    org.focus_areas = json.dumps(org_data.get('focus_areas', []))
                    org.keywords = json.dumps(org_data.get('keywords', []))
                    
                    db.session.add(org)
                    loaded += 1
            
            db.session.commit()
            print(f"✅ Loaded {loaded} organizations successfully")
            return loaded
            
        except FileNotFoundError:
            print(f"❌ File not found: {filepath}")
            return 0
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            return 0
        except Exception as e:
            print(f"❌ Error loading organizations: {e}")
            db.session.rollback()
            return 0

def load_organizations_from_csv(filepath):
    """Load organizations from CSV file"""
    app = create_app()
    
    with app.app_context():
        try:
            loaded = 0
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Check if org already exists
                    existing = Organization.query.filter_by(
                        ein=row.get('ein')
                    ).first() if row.get('ein') else None
                    
                    if not existing:
                        org = Organization()
                        org.name = row.get('name', '').strip()
                        org.legal_name = row.get('legal_name', row.get('name', '')).strip()
                        org.ein = row.get('ein', '').strip()
                        org.mission = row.get('mission', '').strip()
                        org.website = row.get('website', '').strip()
                        org.email = row.get('email', '').strip()
                        org.phone = row.get('phone', '').strip()
                        org.address = row.get('address', '').strip()
                        org.city = row.get('city', '').strip()
                        org.state = row.get('state', '').strip()
                        org.zip_code = row.get('zip_code', '').strip()
                        org.annual_budget = int(row.get('annual_budget', 0)) if row.get('annual_budget') else None
                        org.staff_size = int(row.get('staff_size', 0)) if row.get('staff_size') else None
                        org.year_founded = int(row.get('year_founded', 0)) if row.get('year_founded') else None
                        org.tax_status = row.get('tax_status', '501c3').strip()
                        
                        # Handle focus areas (comma-separated in CSV)
                        focus_areas = row.get('focus_areas', '').split(',') if row.get('focus_areas') else []
                        org.focus_areas = json.dumps([f.strip() for f in focus_areas if f.strip()])
                        
                        db.session.add(org)
                        loaded += 1
                
                db.session.commit()
                print(f"✅ Loaded {loaded} organizations from CSV")
                return loaded
                
        except FileNotFoundError:
            print(f"❌ File not found: {filepath}")
            return 0
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            db.session.rollback()
            return 0

def create_sample_import_files():
    """Create sample import files for reference"""
    
    # Sample JSON format
    sample_json = [
        {
            "name": "Example Foundation",
            "legal_name": "Example Foundation Inc.",
            "ein": "12-3456789",
            "mission": "Supporting education and community development",
            "website": "https://example.org",
            "email": "info@example.org",
            "phone": "(555) 123-4567",
            "address": "123 Main Street",
            "city": "Detroit",
            "state": "MI",
            "zip_code": "48201",
            "year_founded": 2010,
            "annual_budget": 500000,
            "staff_size": 10,
            "tax_status": "501c3",
            "focus_areas": ["Education", "Community Development"],
            "keywords": ["youth", "urban", "education"]
        }
    ]
    
    with open('sample_organizations.json', 'w') as f:
        json.dump(sample_json, f, indent=2)
    
    # Sample CSV format
    csv_header = [
        "name", "legal_name", "ein", "mission", "website", "email", 
        "phone", "address", "city", "state", "zip_code", "year_founded",
        "annual_budget", "staff_size", "tax_status", "focus_areas"
    ]
    
    with open('sample_organizations.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(csv_header)
        writer.writerow([
            "Example Foundation", "Example Foundation Inc.", "12-3456789",
            "Supporting education and community development", "https://example.org",
            "info@example.org", "(555) 123-4567", "123 Main Street",
            "Detroit", "MI", "48201", "2010", "500000", "10", "501c3",
            "Education,Community Development"
        ])
    
    print("📁 Created sample import files:")
    print("  - sample_organizations.json")
    print("  - sample_organizations.csv")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Load organizations into the platform')
    parser.add_argument('--file', help='Path to JSON or CSV file with organizations')
    parser.add_argument('--create-samples', action='store_true', 
                       help='Create sample import files')
    
    args = parser.parse_args()
    
    if args.create_samples:
        create_sample_import_files()
    elif args.file:
        if args.file.endswith('.json'):
            count = load_organizations_from_json(args.file)
        elif args.file.endswith('.csv'):
            count = load_organizations_from_csv(args.file)
        else:
            print("❌ Unsupported file format. Use .json or .csv")
            sys.exit(1)
        
        if count > 0:
            print(f"\n✅ Successfully loaded {count} organizations")
            print("Organizations can now register users and access the platform")
    else:
        print("Usage:")
        print("  python load_organizations.py --file organizations.json")
        print("  python load_organizations.py --file organizations.csv")
        print("  python load_organizations.py --create-samples")
        print("\nNo file specified. Use --create-samples to generate templates.")