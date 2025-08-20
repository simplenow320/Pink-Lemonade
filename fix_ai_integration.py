#!/usr/bin/env python
"""Fix AI integration by ensuring OpenAI is properly connected"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

print("Checking OpenAI API key...")
api_key = os.environ.get('OPENAI_API_KEY')
if api_key:
    print(f"✅ OpenAI API key found: {api_key[:10]}...")
else:
    print("❌ OpenAI API key not found in environment")

# Test AI endpoint
import requests
app = create_app()

with app.app_context():
    with app.test_client() as client:
        # Test AI Grant Matching
        print("\nTesting AI Grant Matching...")
        response = client.post('/api/ai-grants/match/1')
        print(f"Response: {response.json}")
        
        # Test Smart Tools
        print("\nTesting Smart Tools...")
        response = client.get('/api/smart-tools/tools')
        print(f"Response: {response.json}")
        
        # Test Adaptive Discovery
        print("\nTesting Adaptive Discovery...")
        response = client.post('/api/adaptive-discovery/start', 
                              json={'initial_data': {}})
        print(f"Response: {response.json}")