"""
Candid Essentials API client for organization lookups
"""
import os
import requests
from typing import Dict, List, Optional, Any


class CandidEssentialsClient:
    """Client for Candid Essentials API v3"""
    
    BASE = "https://api.candid.org/essentials/v3"
    
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
        try:
            # Clean EIN (remove dashes/spaces)
            clean_ein = ein.replace("-", "").replace(" ", "").strip()
            
            # Build search request
            url = self.BASE
            payload = {
                "filters": {
                    "ein": clean_ein
                },
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
                # Don't log the secret, just return None
                return None
            
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Return first record if found
            if data and isinstance(data, dict) and "records" in data:
                records = data.get("records", [])
                if records and len(records) > 0:
                    return records[0]
            
            return None
            
        except requests.exceptions.RequestException:
            # Network error - return None
            return None
        except Exception:
            # Any other error - return None
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
        try:
            # Build search request
            url = self.BASE
            payload = {
                "filters": {
                    "name": name.strip()
                },
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
                # Don't log the secret, just return None
                return None
            
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Return first record if found
            if data and isinstance(data, dict) and "records" in data:
                records = data.get("records", [])
                if records and len(records) > 0:
                    return records[0]
            
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
            record: Candid API record
            
        Returns:
            Dictionary with extracted tokens
        """
        result = {
            "pcs_subject_codes": [],
            "pcs_population_codes": [],
            "locations": [],
            "mission": None,
            "website": None
        }
        
        if not record or not isinstance(record, dict):
            return result
        
        # Extract PCS subject codes
        if "pcs_subject_codes" in record:
            codes = record.get("pcs_subject_codes")
            if isinstance(codes, list):
                result["pcs_subject_codes"] = [str(c) for c in codes if c]
        
        # Extract PCS population codes
        if "pcs_population_codes" in record:
            codes = record.get("pcs_population_codes")
            if isinstance(codes, list):
                result["pcs_population_codes"] = [str(c) for c in codes if c]
        
        # Extract locations (city, state, country)
        locations = []
        
        # Check for address fields
        if "city" in record and record["city"]:
            city = record["city"]
            state = record.get("state", "")
            if state:
                locations.append(f"{city}, {state}")
            else:
                locations.append(city)
        elif "state" in record and record["state"]:
            locations.append(record["state"])
        
        if "country" in record and record["country"]:
            locations.append(record["country"])
        
        # Also check for nested address object
        if "address" in record and isinstance(record["address"], dict):
            addr = record["address"]
            city = addr.get("city", "")
            state = addr.get("state", "")
            if city and state:
                locations.append(f"{city}, {state}")
            elif city:
                locations.append(city)
            elif state:
                locations.append(state)
        
        result["locations"] = locations
        
        # Extract mission
        if "mission" in record and record["mission"]:
            result["mission"] = str(record["mission"])
        elif "description" in record and record["description"]:
            result["mission"] = str(record["description"])
        
        # Extract website
        if "website" in record and record["website"]:
            result["website"] = str(record["website"])
        elif "url" in record and record["url"]:
            result["website"] = str(record["url"])
        
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