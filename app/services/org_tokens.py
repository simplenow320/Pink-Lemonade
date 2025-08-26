"""
Organization Tokens Service
Manages PCS codes, locations, and keywords for grant matching
"""
from typing import Dict, List, Optional
from app.services.candid_client import get_essentials_client


def get_org_tokens(org_id: int) -> Dict:
    """
    Get comprehensive tokens for organization matching.
    
    1. Try stored tokens from database
    2. If missing, attempt Essentials lookup 
    3. Return structured token dict
    
    Never invents values - returns empty lists if no data available.
    """
    try:
        from app import db
        from app.models import Organization
        
        # Get organization from database
        org = db.session.query(Organization).filter_by(id=org_id).first()
        if not org:
            return _empty_tokens()
        
        # Check if we have stored PCS tokens
        stored_tokens = _get_stored_tokens(org)
        if _tokens_complete(stored_tokens):
            return stored_tokens
        
        # Attempt Essentials lookup if missing data and we have name/EIN
        essentials_tokens = _fetch_essentials_tokens(org)
        if essentials_tokens:
            # Merge with stored data, preferring stored values
            merged_tokens = _merge_tokens(stored_tokens, essentials_tokens)
            # Store the new tokens for future use
            _store_tokens(org, merged_tokens)
            return merged_tokens
        
        # Return whatever we have (may be incomplete)
        return stored_tokens
        
    except Exception as e:
        # Log error but don't crash - return empty tokens
        print(f"Error getting org tokens for {org_id}: {str(e)}")
        return _empty_tokens()


def _empty_tokens() -> Dict:
    """Return empty token structure"""
    return {
        'pcs_subject_codes': [],
        'pcs_population_codes': [],
        'locations': [],
        'keywords': []
    }


def _get_stored_tokens(org) -> Dict:
    """Extract tokens from stored organization data"""
    tokens = {
        'pcs_subject_codes': [],
        'pcs_population_codes': [],
        'locations': [],
        'keywords': []
    }
    
    # Get PCS codes if stored (check custom_fields first, then direct fields)
    custom_fields = org.custom_fields or {}
    
    # PCS Subject codes
    pcs_subjects = custom_fields.get('pcs_subject_codes')
    if not pcs_subjects and hasattr(org, 'pcs_subject_codes'):
        pcs_subjects = getattr(org, 'pcs_subject_codes', None)
    if isinstance(pcs_subjects, list):
        tokens['pcs_subject_codes'] = pcs_subjects
    
    # PCS Population codes  
    pcs_populations = custom_fields.get('pcs_population_codes')
    if not pcs_populations and hasattr(org, 'pcs_population_codes'):
        pcs_populations = getattr(org, 'pcs_population_codes', None)
    if isinstance(pcs_populations, list):
        tokens['pcs_population_codes'] = pcs_populations
    
    # Locations from geographic fields
    locations = []
    if org.primary_city:
        locations.append(org.primary_city)
    if org.primary_state:
        locations.append(org.primary_state)
    if org.counties_served:
        locations.extend(org.counties_served)
    if org.states_served:
        locations.extend(org.states_served)
    
    # Remove duplicates and add to tokens
    tokens['locations'] = list(set(locations))
    
    # Keywords from multiple sources
    keywords = []
    
    # Direct keywords field
    if org.keywords and isinstance(org.keywords, list):
        keywords.extend(org.keywords)
    elif org.keywords and isinstance(org.keywords, str):
        keywords.extend([kw.strip() for kw in org.keywords.split(',') if kw.strip()])
    
    # Extract from focus areas
    if org.primary_focus_areas:
        keywords.extend(org.primary_focus_areas)
    if org.secondary_focus_areas:
        keywords.extend(org.secondary_focus_areas)
    
    # Extract from target demographics
    if org.target_demographics:
        keywords.extend(org.target_demographics)
    
    # Extract from mission statement (basic keyword extraction)
    if org.mission:
        mission_keywords = _extract_mission_keywords(org.mission)
        keywords.extend(mission_keywords)
    
    # Extract from programs/services
    if org.programs_services:
        program_keywords = _extract_mission_keywords(org.programs_services)
        keywords.extend(program_keywords)
    
    # Clean and deduplicate keywords
    tokens['keywords'] = _clean_keywords(keywords)
    
    return tokens


def _tokens_complete(tokens: Dict) -> bool:
    """Check if we have sufficient tokens (not necessarily all fields filled)"""
    # Consider complete if we have PCS codes OR good location/keyword data
    has_pcs = tokens['pcs_subject_codes'] or tokens['pcs_population_codes']
    has_basic = tokens['locations'] and tokens['keywords']
    return has_pcs or has_basic


def _fetch_essentials_tokens(org) -> Optional[Dict]:
    """Attempt to fetch tokens from Candid Essentials API"""
    try:
        essentials_client = get_essentials_client()
        
        # Try EIN first, then name
        search_term = None
        if org.ein and org.ein.strip():
            search_term = org.ein
        elif org.name:
            search_term = org.name
        
        if not search_term:
            return None
        
        # Search for organization
        org_record = essentials_client.search_org(search_term)
        if not org_record:
            return None
        
        # Extract tokens from the record
        return essentials_client.extract_tokens(org_record)
        
    except Exception as e:
        print(f"Error fetching Essentials tokens: {str(e)}")
        return None


def _merge_tokens(stored: Dict, essentials: Dict) -> Dict:
    """Merge tokens, preferring stored values over imported ones"""
    merged = stored.copy()
    
    # Only add Essentials data if we don't have stored data for that field
    if not merged['pcs_subject_codes'] and essentials.get('pcs_subject_codes'):
        merged['pcs_subject_codes'] = essentials['pcs_subject_codes']
    
    if not merged['pcs_population_codes'] and essentials.get('pcs_population_codes'):
        merged['pcs_population_codes'] = essentials['pcs_population_codes']
    
    # For locations and keywords, merge (don't replace) if we have some data
    if essentials.get('locations'):
        all_locations = merged['locations'] + essentials['locations']
        merged['locations'] = list(set(all_locations))
    
    # Don't merge keywords from Essentials to avoid noise
    # Keywords are better sourced from mission/programs
    
    return merged


def _store_tokens(org, tokens: Dict) -> None:
    """Store tokens back to organization record"""
    try:
        from app import db
        
        # Store PCS codes in custom_fields
        if not org.custom_fields:
            org.custom_fields = {}
        
        # Update custom fields with new PCS data
        if tokens.get('pcs_subject_codes'):
            org.custom_fields['pcs_subject_codes'] = tokens['pcs_subject_codes']
        
        if tokens.get('pcs_population_codes'):
            org.custom_fields['pcs_population_codes'] = tokens['pcs_population_codes']
        
        # Store enhanced keywords if we have them  
        if tokens.get('keywords') and len(tokens['keywords']) > len(org.keywords or []):
            org.keywords = tokens['keywords']
        
        # Mark as modified
        org.updated_at = None  # Triggers automatic timestamp update
        
        db.session.commit()
        
    except Exception as e:
        print(f"Error storing tokens: {str(e)}")
        # Don't re-raise - we can still return the tokens


def _extract_mission_keywords(text: str) -> List[str]:
    """Extract meaningful keywords from mission/program text"""
    if not text:
        return []
    
    # Simple keyword extraction - look for meaningful terms
    # This is basic but avoids complex NLP dependencies
    common_nonprofit_keywords = {
        'education', 'health', 'healthcare', 'housing', 'youth', 'seniors', 
        'children', 'families', 'community', 'development', 'services',
        'advocacy', 'arts', 'culture', 'environment', 'poverty', 'hunger',
        'disabilities', 'veterans', 'women', 'minorities', 'immigrants',
        'research', 'mental', 'substance', 'abuse', 'violence', 'safety'
    }
    
    # Convert to lowercase and find matches
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in common_nonprofit_keywords:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    return found_keywords


def _clean_keywords(keywords: List[str]) -> List[str]:
    """Clean and deduplicate keyword list"""
    if not keywords:
        return []
    
    # Convert to lowercase, strip, remove empty, deduplicate
    cleaned = []
    seen = set()
    
    for kw in keywords:
        if isinstance(kw, str):
            clean_kw = kw.strip().lower()
            if clean_kw and len(clean_kw) > 2 and clean_kw not in seen:
                cleaned.append(clean_kw)
                seen.add(clean_kw)
    
    return cleaned[:20]  # Limit to 20 keywords to avoid noise