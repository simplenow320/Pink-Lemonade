"""
Mock API responses for testing API integrations without real credentials
"""

import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Any

# Mock successful responses for different API sources
MOCK_GRANTS_GOV_RESPONSE = {
    "results": [
        {
            "opportunityNumber": "TEST-GRANT-001",
            "opportunityTitle": "Test Education Grant Program",
            "cfda": "84.215",
            "agencyCode": "ED",
            "agencyName": "Department of Education",
            "synopsis": "Federal grant to support innovative education programs in underserved communities.",
            "eligibilityCategories": ["Public/State Controlled Institution of Higher Education"],
            "postDate": "2025-01-01",
            "closeDate": "2025-03-15",
            "awardFloor": 50000,
            "awardCeiling": 500000,
            "totalProgramFunding": 10000000,
            "expectedNumberOfAwards": 20,
            "opportunityStatus": "Posted",
            "links": {
                "self": "https://www.grants.gov/grantsws/rest/opportunity/TEST-GRANT-001"
            }
        },
        {
            "opportunityNumber": "TEST-GRANT-002", 
            "opportunityTitle": "Community Health Innovation Fund",
            "cfda": "93.079",
            "agencyCode": "HHS",
            "agencyName": "Department of Health and Human Services",
            "synopsis": "Supporting innovative approaches to community health challenges.",
            "eligibilityCategories": ["Nonprofits having a 501(c)(3) status"],
            "postDate": "2025-01-05",
            "closeDate": "2025-04-01",
            "awardFloor": 25000,
            "awardCeiling": 300000,
            "totalProgramFunding": 5000000,
            "expectedNumberOfAwards": 15,
            "opportunityStatus": "Posted"
        }
    ],
    "totalRecordsCount": 2,
    "pageNumber": 1,
    "pageSize": 25
}

MOCK_FEDERAL_REGISTER_RESPONSE = {
    "results": [
        {
            "title": "Notice of Funding Opportunity for Environmental Research",
            "html_url": "https://www.federalregister.gov/documents/2025/01/15/test-environmental-funding",
            "publication_date": "2025-01-15",
            "abstract": "EPA announces funding availability for environmental research projects focusing on climate adaptation strategies.",
            "document_number": "2025-00123",
            "type": "Notice",
            "agencies": [{"name": "Environmental Protection Agency"}]
        },
        {
            "title": "Small Business Innovation Research Program Notice",
            "html_url": "https://www.federalregister.gov/documents/2025/01/20/test-sbir-funding",
            "publication_date": "2025-01-20", 
            "abstract": "Notice of funding opportunity for small business research and development projects.",
            "document_number": "2025-00456",
            "type": "Notice",
            "agencies": [{"name": "Small Business Administration"}]
        }
    ],
    "count": 2,
    "total_pages": 1
}

MOCK_SAM_GOV_OPPORTUNITIES_RESPONSE = {
    "links": {
        "self": "https://api.sam.gov/opportunities/v2/search"
    },
    "page": {
        "size": 10,
        "totalElements": 2,
        "totalPages": 1,
        "number": 0
    },
    "embedded": {
        "opportunities": [
            {
                "noticeId": "test-notice-001",
                "title": "Information Technology Services Contract",
                "solicitationNumber": "TEST-IT-2025-001",
                "department": "Department of Defense",
                "subTier": "Army",
                "office": "Army Corps of Engineers",
                "postedDate": "2025-01-10",
                "type": "Combined Synopsis/Solicitation",
                "baseType": "Contract Opportunity",
                "archiveType": "auto15",
                "archiveDate": "2025-02-10",
                "typeOfSetAsideDescription": "Total Small Business",
                "typeOfSetAside": "SBA",
                "description": "The Army Corps of Engineers seeks qualified contractors for IT infrastructure services.",
                "organizationType": "OFFICE",
                "naicsCode": "541512",
                "classificationCode": "D",
                "active": "Yes",
                "award": {
                    "number": None,
                    "date": None,
                    "amount": None
                },
                "pointOfContact": [
                    {
                        "fax": None,
                        "type": "primary",
                        "email": "contracting@usace.army.mil",
                        "phone": "555-123-4567",
                        "title": "Contracting Officer",
                        "fullName": "John Smith"
                    }
                ],
                "placeOfPerformance": {
                    "city": {"code": "12345", "name": "Washington"},
                    "state": {"code": "DC", "name": "District of Columbia"},
                    "zip": "20314",
                    "country": {"code": "USA", "name": "UNITED STATES"}
                },
                "additionalInfoLink": "https://sam.gov/opp/test-notice-001"
            }
        ]
    }
}

MOCK_GOVINFO_RESPONSE = {
    "nextPage": "https://api.govinfo.gov/search?collection=FR&pageSize=25&offsetMark=next",
    "previousPage": None,
    "count": 25,
    "packages": [
        {
            "packageId": "FR-2025-01-15",
            "title": "Federal Register Volume 90, Number 10 (Friday, January 15, 2025)",
            "dateIssued": "2025-01-15",
            "lastModified": "2025-01-15T10:00:00Z",
            "packageLink": "https://api.govinfo.gov/packages/FR-2025-01-15",
            "docClass": "fr",
            "dateIngested": "2025-01-15T10:00:00Z"
        }
    ]
}

# Error responses for testing error handling
MOCK_ERROR_RESPONSES = {
    "401_unauthorized": {
        "status_code": 401,
        "content": {"error": "Unauthorized", "message": "Invalid API key"},
        "headers": {"Content-Type": "application/json"}
    },
    "403_forbidden": {
        "status_code": 403,
        "content": {"error": "Forbidden", "message": "Access denied"},
        "headers": {"Content-Type": "application/json"}
    },
    "429_rate_limit": {
        "status_code": 429,
        "content": {"error": "Rate limit exceeded", "message": "Too many requests"},
        "headers": {
            "Content-Type": "application/json",
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "3600"
        }
    },
    "500_server_error": {
        "status_code": 500,
        "content": {"error": "Internal server error", "message": "Service temporarily unavailable"},
        "headers": {"Content-Type": "application/json"}
    },
    "502_bad_gateway": {
        "status_code": 502,
        "content": {"error": "Bad gateway", "message": "Upstream server error"},
        "headers": {"Content-Type": "application/json"}
    },
    "503_service_unavailable": {
        "status_code": 503,
        "content": {"error": "Service unavailable", "message": "Service is down for maintenance"},
        "headers": {"Content-Type": "application/json"}
    },
    "timeout": {
        "status_code": 408,
        "content": {"error": "Request timeout", "message": "Request timed out"},
        "headers": {"Content-Type": "application/json"}
    }
}

# Source-specific mock data mapping
SOURCE_MOCK_RESPONSES = {
    "grants_gov": {
        "success": MOCK_GRANTS_GOV_RESPONSE,
        "empty": {"results": [], "totalRecordsCount": 0, "pageNumber": 1, "pageSize": 25}
    },
    "federal_register": {
        "success": MOCK_FEDERAL_REGISTER_RESPONSE,
        "empty": {"results": [], "count": 0, "total_pages": 0}
    },
    "sam_gov_opportunities": {
        "success": MOCK_SAM_GOV_OPPORTUNITIES_RESPONSE,
        "empty": {
            "links": {"self": "https://api.sam.gov/opportunities/v2/search"},
            "page": {"size": 10, "totalElements": 0, "totalPages": 0, "number": 0},
            "embedded": {"opportunities": []}
        }
    },
    "govinfo": {
        "success": MOCK_GOVINFO_RESPONSE,
        "empty": {"nextPage": None, "previousPage": None, "count": 0, "packages": []}
    },
    "foundation_directory": {
        "success": {
            "foundations": [
                {
                    "id": "mock-foundation-001",
                    "name": "Mock Education Foundation",
                    "description": "Supporting educational initiatives nationwide",
                    "assets": 50000000,
                    "giving_amount": 2500000,
                    "location": {"city": "New York", "state": "NY"},
                    "focus_areas": ["education", "youth development"],
                    "website": "https://mockeducationfoundation.org"
                }
            ],
            "total": 1
        },
        "empty": {"foundations": [], "total": 0}
    },
    "candid": {
        "success": {
            "grants": [
                {
                    "id": "candid-grant-001",
                    "funder_name": "Mock Health Foundation",
                    "grant_amount": 75000,
                    "purpose": "Community health program support",
                    "recipient": "Local Health Initiative",
                    "year": 2025,
                    "focus_area": "health"
                }
            ],
            "total_results": 1
        },
        "empty": {"grants": [], "total_results": 0}
    }
}

def get_mock_response(source_name: str, response_type: str = "success") -> Dict[str, Any]:
    """
    Get mock response for a specific API source
    
    Args:
        source_name: Name of the API source
        response_type: Type of response ("success", "empty", "error")
    
    Returns:
        Mock response data
    """
    if response_type in MOCK_ERROR_RESPONSES:
        return MOCK_ERROR_RESPONSES[response_type]
    
    source_responses = SOURCE_MOCK_RESPONSES.get(source_name, {})
    return source_responses.get(response_type, {})

def create_standardized_grant(source_data: Dict[str, Any], source_name: str) -> Dict[str, Any]:
    """
    Convert source-specific mock data to standardized grant format
    """
    if source_name == "grants_gov":
        return {
            "id": source_data.get("opportunityNumber"),
            "title": source_data.get("opportunityTitle"),
            "funder": source_data.get("agencyName"),
            "description": source_data.get("synopsis"),
            "amount_min": source_data.get("awardFloor"),
            "amount_max": source_data.get("awardCeiling"),
            "due_date": source_data.get("closeDate"),
            "eligibility": ", ".join(source_data.get("eligibilityCategories", [])),
            "website": source_data.get("links", {}).get("self"),
            "source": "grants_gov",
            "status": "active"
        }
    elif source_name == "federal_register":
        return {
            "id": source_data.get("document_number"),
            "title": source_data.get("title"),
            "funder": source_data.get("agencies", [{}])[0].get("name", "Federal Government"),
            "description": source_data.get("abstract"),
            "website": source_data.get("html_url"),
            "source": "federal_register",
            "published_date": source_data.get("publication_date"),
            "status": "active"
        }
    elif source_name == "sam_gov_opportunities":
        return {
            "id": source_data.get("noticeId"),
            "title": source_data.get("title"),
            "funder": source_data.get("department"),
            "description": source_data.get("description"),
            "solicitation_number": source_data.get("solicitationNumber"),
            "due_date": source_data.get("archiveDate"),
            "website": source_data.get("additionalInfoLink"),
            "source": "sam_gov_opportunities",
            "status": "active"
        }
    else:
        # Generic format for other sources
        return {
            "id": source_data.get("id", f"mock-{source_name}-001"),
            "title": source_data.get("title", f"Mock Grant from {source_name}"),
            "funder": source_data.get("funder", f"Mock {source_name} Foundation"),
            "description": source_data.get("description", f"Mock grant description from {source_name}"),
            "source": source_name,
            "status": "active"
        }

# Test scenarios for credential handling
CREDENTIAL_TEST_SCENARIOS = {
    "missing_required": {
        "description": "Test with missing required credentials",
        "sources": ["sam_gov_opportunities", "sam_gov_entity", "foundation_directory", "grantwatch", "candid", "zyte_api"],
        "expected_behavior": "source_disabled"
    },
    "invalid_credentials": {
        "description": "Test with invalid credentials",
        "sources": ["sam_gov_opportunities", "foundation_directory", "candid"],
        "test_credentials": {
            "sam_gov_opportunities": "invalid-key-123",
            "foundation_directory": "invalid-fdo-key",
            "candid": "invalid-candid-key"
        },
        "expected_error": "401_unauthorized"
    },
    "partial_credentials": {
        "description": "Test with some valid and some invalid credentials",
        "scenarios": [
            {
                "valid_sources": ["grants_gov", "federal_register"],
                "invalid_sources": ["sam_gov_opportunities", "candid"],
                "expected": "valid_sources_work"
            }
        ]
    }
}