"""
Candid Essentials API client for organization lookups
"""
import os
import requests
import time
from typing import Dict, List, Optional, Any


class CandidEssentialsClient:
    """Client for Candid Essentials API v3 with rate limiting"""
    
    BASE = "https://api.candid.org/essentials/v3"
    
    def __init__(self):
        # Rate limiting: minimum 1 second between calls
        self.last_call_time = 0
        self.min_interval = 1.0  # seconds
    
    def _rate_limit(self):
        """Enforce rate limiting to prevent quota waste"""
        now = time.time()
        time_since_last = now - self.last_call_time
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)
        self.last_call_time = time.time()
    
    def headers(self) -> Dict[str, str]:
        """Get required headers for API requests"""
        return {
            "Subscription-Key": os.getenv("CANDID_ESSENTIALS_KEY", ""),
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def search_by_ein(self, ein: str, limit: int = 1) -> Optional[Dict[str, Any]]:
        """
        Search for organization by EIN
        
        Args:
            ein: Employer Identification Number
            limit: Maximum results to return (default 1)
            
        Returns:
            First matching record or None
        """
        # Circuit breaker: disable Candid calls if DEMO_MODE
        if os.environ.get('DEMO_MODE', 'false').lower() == 'true':
            return None
            
        # Rate limiting to prevent quota waste
        self._rate_limit()
            
        try:
            # Clean EIN (remove dashes/spaces)
            clean_ein = ein.replace("-", "").replace(" ", "").strip()
            
            # Build search request using search_terms for v3 API
            url = self.BASE
            payload = {
                "search_terms": clean_ein,  # Use search_terms for EIN in v3
                "limit": limit
            }
            
            # Make request
            response = requests.post(
                url,
                json=payload,
                headers=self.headers(),
                timeout=20
            )
            
            # Check for auth/rate limit issues
            if response.status_code in [401, 403, 429]:
                print(f"Candid API auth/rate limit issue: {response.status_code}")
                return None
            
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # v3 API returns hits array with nested organization data
            if data and isinstance(data, dict):
                hits = data.get("hits", [])
                if hits and len(hits) > 0:
                    # Verify EIN match (API might return fuzzy matches)
                    for hit in hits:
                        org_data = hit.get("organization", {})
                        if org_data.get("ein", "").replace("-", "") == clean_ein:
                            # Return the full hit which includes organization, geography, etc.
                            return hit
                    # If no exact match, return first result
                    return hits[0] if hits else None
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Candid API network error: {str(e)[:100]}")
            return None
        except Exception as e:
            print(f"Candid API error: {str(e)[:100]}")
            return None
    
    def search_by_name(self, name: str, limit: int = 1) -> Optional[Dict[str, Any]]:
        """
        Search for organization by name
        
        Args:
            name: Organization name to search
            limit: Maximum results to return (default 1)
            
        Returns:
            First matching record or None
        """
        # Circuit breaker: disable Candid calls if DEMO_MODE
        if os.environ.get('DEMO_MODE', 'false').lower() == 'true' or os.environ.get('CANDID_ENABLED', 'true').lower() == 'false':
            return None
            
        # Rate limiting to prevent quota waste
        self._rate_limit()
            
        try:
            # Build search request using search_terms for v3 API
            url = self.BASE
            payload = {
                "search_terms": name.strip(),  # Use search_terms for name search in v3
                "limit": limit
            }
            
            # Make request
            response = requests.post(
                url,
                json=payload,
                headers=self.headers(),
                timeout=20
            )
            
            # Check for auth/rate limit issues
            if response.status_code in [401, 403, 429]:
                print(f"Candid API auth/rate limit issue: {response.status_code}")
                return None
            
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # v3 API returns hits array with nested organization data
            if data and isinstance(data, dict):
                hits = data.get("hits", [])
                if hits and len(hits) > 0:
                    # Return the full hit which includes organization, geography, etc.
                    return hits[0]
            
            return None
            
        except requests.exceptions.RequestException:
            # Network error - return None
            return None
        except Exception:
            # Any other error - return None
            return None
    
    def extract_tokens(self, record: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract useful tokens from a Candid organization record
        
        Args:
            record: Candid API record (v3 hit structure)
            
        Returns:
            Dictionary with extracted tokens
        """
        result = {
            "pcs_subject_codes": [],
            "pcs_population_codes": [],
            "locations": [],
            "mission": None,
            "website": None,
            "ein": None,
            "organization_name": None
        }
        
        if not record or not isinstance(record, dict):
            return result
        
        # v3 API nests data under organization, taxonomies, geography sections
        org_data = record.get("organization", {})
        taxonomies = record.get("taxonomies", {})
        geography = record.get("geography", {})
        
        # Extract basic organization info
        if org_data.get("ein"):
            result["ein"] = org_data["ein"]
        if org_data.get("organization_name"):
            result["organization_name"] = org_data["organization_name"]
        
        # Extract mission
        if org_data.get("mission"):
            result["mission"] = str(org_data["mission"])
        
        # Extract website
        if org_data.get("website_url"):
            result["website"] = str(org_data["website_url"])
        
        # Extract PCS codes from taxonomies
        if taxonomies.get("pcs_subject_codes"):
            codes = taxonomies["pcs_subject_codes"]
            if isinstance(codes, list):
                result["pcs_subject_codes"] = [str(c) for c in codes if c]
        
        if taxonomies.get("pcs_population_codes"):
            codes = taxonomies["pcs_population_codes"]
            if isinstance(codes, list):
                result["pcs_population_codes"] = [str(c) for c in codes if c]
        
        # Extract locations from geography
        locations = []
        
        # Primary location
        if geography.get("city") and geography.get("state"):
            locations.append(f"{geography['city']}, {geography['state']}")
        elif geography.get("city"):
            locations.append(geography["city"])
        elif geography.get("state"):
            locations.append(geography["state"])
        
        if geography.get("country"):
            locations.append(geography["country"])
        
        # Service areas
        if geography.get("service_areas"):
            service_areas = geography["service_areas"]
            if isinstance(service_areas, list):
                for area in service_areas:
                    if isinstance(area, str):
                        locations.append(area)
        
        result["locations"] = list(set(locations))  # Remove duplicates
        
        return result


# Create singleton instance
candid_client = CandidEssentialsClient()

# Export convenience functions
def search_by_ein(ein: str, limit: int = 1) -> Optional[Dict[str, Any]]:
    """Search for organization by EIN"""
    return candid_client.search_by_ein(ein, limit)

def search_by_name(name: str, limit: int = 1) -> Optional[Dict[str, Any]]:
    """Search for organization by name"""
    return candid_client.search_by_name(name, limit)

def extract_tokens(record: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract useful tokens from a Candid organization record"""
    return candid_client.extract_tokens(record)