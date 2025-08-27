#!/usr/bin/env python3
"""
Test the Impact Report API endpoint with real intake data
"""

import json
import requests
import sys

def test_impact_api():
    """Test the Impact Report generation API"""
    print("\n" + "="*50)
    print("Testing Impact Report API Endpoint")
    print("="*50 + "\n")
    
    # API endpoint
    url = "http://localhost:5000/api/smart-tools/impact/generate"
    
    # Request payload with grant_id to use intake data
    payload = {
        "org_id": 5,  # Nitrogen Network
        "grant_id": 9,  # Michigan Community Foundation Grant (has intake data)
        "period_start": "2024-01-01",
        "period_end": "2024-12-31",
        "metrics": {
            "grants_submitted": 15,
            "grants_won": 5,
            "funding_secured": 500000,
            "beneficiaries_served": 1200,
            "programs_delivered": 8,
            "volunteer_hours": 2400
        }
    }
    
    print("📮 Sending POST request to:", url)
    print("📦 Payload:", json.dumps(payload, indent=2))
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print("\n✅ API Response: SUCCESS")
                
                report = data.get('report', {})
                print("\n📊 Report Generated:")
                print(f"  • Impact Score: {report.get('impact_score', 0)}/100")
                print(f"  • Success Stories: {len(report.get('success_stories', []))}")
                print(f"  • Charts Generated: {len(report.get('charts', []))}")
                print(f"  • Source Notes: {report.get('source_notes', [])}")
                
                # Show executive summary preview
                exec_summary = report.get('executive_summary', '')
                if exec_summary:
                    print(f"\n📄 Executive Summary Preview:")
                    print(f"  {exec_summary[:200]}...")
                
                # Show financial summary
                financial = report.get('financial_summary', {})
                if financial:
                    print(f"\n💰 Financial Summary:")
                    print(f"  • Total Grant: ${financial.get('total_grant', 0):,}")
                    print(f"  • Spent to Date: ${financial.get('spent_to_date', 0):,}")
                    print(f"  • Remaining: ${financial.get('remaining', 0):,}")
                
                return True
            else:
                print(f"\n❌ API Error: {data.get('error')}")
                return False
        else:
            print(f"\n❌ HTTP Error: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n⚠️ Could not connect to API - ensure the Flask server is running")
        print("Start the server with: gunicorn --bind 0.0.0.0:5000 main:app")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    success = test_impact_api()
    
    if success:
        print("\n" + "="*50)
        print("✅ API TEST SUCCESSFUL")
        print("The Impact Report API is fully operational!")
        print("="*50)
        sys.exit(0)
    else:
        print("\n" + "="*50)
        print("❌ API TEST FAILED")
        print("="*50)
        sys.exit(1)