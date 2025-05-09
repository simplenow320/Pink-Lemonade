"""
Mock implementations of AI service functions for testing.

These mocks simulate the behavior of the actual AI services
without making external API calls to OpenAI.
"""

from typing import Dict, Any, List, Optional
import json


def mock_extract_grant_info(text: str) -> Dict[str, Any]:
    """
    Mock implementation of extract_grant_info that returns predefined data.
    
    Args:
        text: The text to extract grant information from (ignored in mock)
        
    Returns:
        dict: Predefined grant information
    """
    return {
        "title": "Mock Education Initiative Grant",
        "funder": "Mock Foundation",
        "description": "Supporting educational programs in underserved communities",
        "amount": 25000.0,
        "due_date": "2025-08-15",
        "eligibility": "501(c)(3) organizations with focus on education",
        "website": "https://example.com/grants/education",
        "focus_areas": ["education", "youth development"],
        "contact_info": "grants@mockfoundation.org"
    }


def mock_extract_grant_info_from_url(url: str) -> Dict[str, Any]:
    """
    Mock implementation of extract_grant_info_from_url that returns predefined data.
    
    Args:
        url: The URL to extract grant information from (ignored in mock)
        
    Returns:
        dict: Predefined grant information
    """
    return {
        "title": "Mock Community Development Grant",
        "funder": "Mock Regional Foundation",
        "description": "Supporting community development initiatives",
        "amount": 50000.0,
        "due_date": "2025-09-30",
        "eligibility": "Nonprofit organizations serving the local region",
        "website": url,
        "focus_areas": ["community development", "housing", "health"],
        "contact_info": "community@mockregional.org"
    }


def mock_analyze_grant_match(grant: Dict[str, Any], organization: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mock implementation of analyze_grant_match that simulates match analysis.
    
    Args:
        grant: The grant information
        organization: The organization profile
        
    Returns:
        dict: Match analysis with score and explanation
    """
    # Calculate a simple match score based on focus areas overlap
    grant_focus = set(grant.get("focus_areas", []))
    org_focus = set(organization.get("focus_areas", []))
    
    if not grant_focus or not org_focus:
        score = 35.0  # Default score when no focus areas
        explanation = "Limited information available for matching."
    else:
        # Calculate overlap between focus areas
        overlap = len(grant_focus.intersection(org_focus))
        total = len(grant_focus.union(org_focus))
        
        if total > 0:
            score = (overlap / total) * 100
        else:
            score = 0.0
            
        if score > 80:
            explanation = "Excellent match based on mission alignment and focus areas."
        elif score > 60:
            explanation = "Good match with substantial focus area overlap."
        elif score > 40:
            explanation = "Moderate match with some focus area alignment."
        else:
            explanation = "Limited match with few common focus areas."
    
    return {
        "match_score": round(score, 1),
        "match_explanation": explanation
    }


def mock_generate_grant_narrative(
    grant: Dict[str, Any], 
    organization: Dict[str, Any], 
    case_for_support: str = ""
) -> str:
    """
    Mock implementation of generate_grant_narrative.
    
    Args:
        grant: The grant information
        organization: The organization profile
        case_for_support: Additional case for support text
        
    Returns:
        str: Generated narrative text
    """
    org_name = organization.get("name", "Organization")
    grant_title = grant.get("title", "Grant")
    funder = grant.get("funder", "Foundation")
    mission = organization.get("mission", "")
    
    narrative = f"""
# Grant Proposal: {grant_title}

## Executive Summary

{org_name} is seeking funding from {funder} to support our mission: {mission}

## Organization Background

{org_name} has a proven track record of success in our focus areas, which include {', '.join(organization.get('focus_areas', []))}.

## Project Description

This project will address community needs by leveraging our expertise in {', '.join(organization.get('focus_areas', [])[:2])}.

## Budget

The total requested amount is ${grant.get('amount', 0):,.2f}.

## Expected Outcomes

Our project will directly impact the community through measurable outcomes aligned with both our mission and the funder's priorities.

## Conclusion

We appreciate your consideration of our proposal and look forward to potential partnership.
"""
    return narrative