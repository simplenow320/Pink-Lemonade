"""
GrantFlow Import Agent

This script handles importing organization profiles and manual funders from JSON input,
extracting keywords, and saving to the appropriate files.
"""

import json
import os
import sys
import re
from typing import Dict, List, Any, Union, Set

def extract_keywords(org_profile: Dict[str, Any]) -> List[str]:
    """
    Extract keywords from organization profile.
    
    Args:
        org_profile: The organization profile dictionary
        
    Returns:
        A list of extracted keywords
    """
    keywords = set()
    
    # Check if keywords or catch_words already exist in the profile
    if "keywords" in org_profile and isinstance(org_profile["keywords"], list):
        keywords.update(org_profile["keywords"])
    
    if "catch_words" in org_profile and isinstance(org_profile["catch_words"], list):
        keywords.update(org_profile["catch_words"])
        
    # Extract from focus areas
    if "focus_areas" in org_profile and isinstance(org_profile["focus_areas"], list):
        keywords.update(org_profile["focus_areas"])
    
    # Extract from funding priorities
    if "funding_priorities" in org_profile and isinstance(org_profile["funding_priorities"], list):
        # For each priority, split into individual words and add significant ones
        for priority in org_profile["funding_priorities"]:
            if isinstance(priority, str):
                # Split by common separators and extract multi-word phrases
                words = re.findall(r'\b[A-Za-z][A-Za-z\s]*[A-Za-z]\b', priority)
                keywords.update([w.strip() for w in words if len(w.strip()) > 3])
    
    # Extract from mission and vision
    for field in ["mission", "vision"]:
        if field in org_profile and isinstance(org_profile[field], str):
            # Extract meaningful phrases (nouns, noun phrases)
            text = org_profile[field]
            # Look for capitalized phrases or words that might be important
            capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
            keywords.update(capitalized)
            
            # Also look for words after "focused on", "specializing in", etc.
            focus_phrases = [
                r'focus(?:ed)? on\s+([A-Za-z][A-Za-z\s]*[A-Za-z])',
                r'specializ(?:e|ing) in\s+([A-Za-z][A-Za-z\s]*[A-Za-z])',
                r'dedicated to\s+([A-Za-z][A-Za-z\s]*[A-Za-z])',
                r'commitment to\s+([A-Za-z][A-Za-z\s]*[A-Za-z])'
            ]
            
            for pattern in focus_phrases:
                matches = re.findall(pattern, text, re.IGNORECASE)
                keywords.update([m.strip() for m in matches if len(m.strip()) > 3])
    
    # Clean up and filter keywords
    cleaned_keywords = []
    for keyword in keywords:
        # Remove any trailing punctuation and convert to lowercase
        cleaned = keyword.strip().strip('.,;:').lower()
        if len(cleaned) > 3 and cleaned not in cleaned_keywords:
            cleaned_keywords.append(cleaned)
    
    return cleaned_keywords

def save_org_profile(org_profile: Dict[str, Any]) -> bool:
    """
    Save organization profile to org_profile.json
    
    Args:
        org_profile: The organization profile dictionary
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract and add keywords if not already present
        if "keywords" not in org_profile:
            org_profile["keywords"] = extract_keywords(org_profile)
        
        # Write to file
        with open("org_profile.json", "w") as f:
            json.dump(org_profile, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving organization profile: {str(e)}")
        return False

def save_manual_funders(manual_funders: List[Dict[str, str]]) -> Dict[str, int]:
    """
    Save manual funders to manual_sources.json, merging with existing entries
    
    Args:
        manual_funders: List of manual funder dictionaries
        
    Returns:
        Dictionary with counts of imported and skipped funders
    """
    result = {"imported": 0, "skipped": 0}
    
    try:
        # Load existing manual sources if file exists
        existing_funders = []
        if os.path.exists("manual_sources.json"):
            try:
                with open("manual_sources.json", "r") as f:
                    existing_funders = json.load(f)
                    if not isinstance(existing_funders, list):
                        existing_funders = []
            except json.JSONDecodeError:
                existing_funders = []
        
        # Create a set of existing URLs for efficient lookup
        existing_urls = {funder.get("url", "").lower() for funder in existing_funders}
        
        # Merge new funders, avoiding duplicates by URL
        for funder in manual_funders:
            if "url" in funder and "name" in funder:
                url = funder["url"].lower()
                if url in existing_urls:
                    result["skipped"] += 1
                else:
                    existing_funders.append(funder)
                    existing_urls.add(url)
                    result["imported"] += 1
        
        # Write merged list to file
        with open("manual_sources.json", "w") as f:
            json.dump(existing_funders, f, indent=2)
        
        return result
    
    except Exception as e:
        print(f"Error saving manual funders: {str(e)}")
        return {"imported": 0, "skipped": 0}

def process_import(input_json: str) -> Dict[str, Any]:
    """
    Process the import from JSON input
    
    Args:
        input_json: JSON string with org_profile and manual_funders
        
    Returns:
        Dictionary with import results
    """
    try:
        # Parse JSON input
        data = json.loads(input_json)
        
        # Validate required fields
        if not isinstance(data, dict):
            return {
                "status": "error",
                "message": "Input must be a JSON object"
            }
        
        # Validate org_profile
        if "org_profile" not in data:
            return {
                "status": "error",
                "message": "Input must contain 'org_profile' object"
            }
        
        org_profile = data["org_profile"]
        if not isinstance(org_profile, dict):
            return {
                "status": "error",
                "message": "'org_profile' must be an object"
            }
        
        # Check required fields in org_profile
        required_fields = ["name", "mission", "vision", "focus_areas", "funding_priorities"]
        missing_fields = [field for field in required_fields if field not in org_profile]
        
        if missing_fields:
            return {
                "status": "error",
                "message": f"Missing required fields in org_profile: {', '.join(missing_fields)}"
            }
        
        # Validate types for array fields
        for field in ["focus_areas", "funding_priorities"]:
            if not isinstance(org_profile[field], list):
                return {
                    "status": "error",
                    "message": f"'{field}' must be an array"
                }
        
        # Validate manual_funders
        manual_funders = data.get("manual_funders", [])
        if not isinstance(manual_funders, list):
            return {
                "status": "error",
                "message": "'manual_funders' must be an array"
            }
        
        # Validate each funder has required fields
        for i, funder in enumerate(manual_funders):
            if not isinstance(funder, dict):
                return {
                    "status": "error",
                    "message": f"Each manual funder must be an object (error at index {i})"
                }
            
            if "name" not in funder or "url" not in funder:
                return {
                    "status": "error",
                    "message": f"Each manual funder must have 'name' and 'url' (error at index {i})"
                }
        
        # Extract and add keywords
        keywords = extract_keywords(org_profile)
        org_profile["keywords"] = keywords
        
        # Save org_profile
        org_profile_saved = save_org_profile(org_profile)
        
        # Save manual_funders
        funder_results = save_manual_funders(manual_funders)
        
        # Return success response
        return {
            "status": "success",
            "org_profile_saved": org_profile_saved,
            "keywords": keywords,
            "manual_funders_imported": funder_results["imported"],
            "duplicates_skipped": funder_results["skipped"]
        }
    
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": "Invalid JSON format"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }

def main():
    """
    Main function to run the import agent from command line
    """
    # Read input JSON from stdin
    input_json = sys.stdin.read()
    
    # Process the import
    result = process_import(input_json)
    
    # Output the result
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()