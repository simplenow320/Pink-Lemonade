"""
Geoname ID Mapping for US States
Used for Candid API location parameter
"""

# Geoname IDs for US States from Candid documentation
STATE_GEONAME_IDS = {
    'AL': 4829764,  # Alabama
    'AK': 5879092,  # Alaska
    'AZ': 5551752,  # Arizona
    'AR': 4099753,  # Arkansas
    'CA': 5332921,  # California
    'CO': 5417618,  # Colorado
    'CT': 4831725,  # Connecticut
    'DE': 4142224,  # Delaware
    'FL': 4155751,  # Florida
    'GA': 4197000,  # Georgia
    'HI': 5855797,  # Hawaii
    'ID': 5596512,  # Idaho
    'IL': 4896861,  # Illinois
    'IN': 4921868,  # Indiana
    'IA': 4862034,  # Iowa
    'KS': 4273857,  # Kansas
    'KY': 6254925,  # Kentucky
    'LA': 4331987,  # Louisiana
    'ME': 4971068,  # Maine
    'MD': 4361885,  # Maryland
    'MA': 6254926,  # Massachusetts
    'MI': 5001836,  # Michigan
    'MN': 5037779,  # Minnesota
    'MS': 4436296,  # Mississippi
    'MO': 4398678,  # Missouri
    'MT': 5667009,  # Montana
    'NE': 5073708,  # Nebraska
    'NV': 5509151,  # Nevada
    'NH': 5090174,  # New Hampshire
    'NJ': 5101760,  # New Jersey
    'NM': 5481136,  # New Mexico
    'NY': 5128638,  # New York
    'NC': 4482348,  # North Carolina
    'ND': 5690763,  # North Dakota
    'OH': 5165418,  # Ohio
    'OK': 4544379,  # Oklahoma
    'OR': 5744337,  # Oregon
    'PA': 6254927,  # Pennsylvania
    'RI': 5224323,  # Rhode Island
    'SC': 4597040,  # South Carolina
    'SD': 5769223,  # South Dakota
    'TN': 4662168,  # Tennessee
    'TX': 4736286,  # Texas
    'UT': 5549030,  # Utah
    'VT': 5242283,  # Vermont
    'VA': 6254928,  # Virginia
    'WA': 5815135,  # Washington
    'WV': 4826850,  # West Virginia
    'WI': 5279468,  # Wisconsin
    'WY': 5843591,  # Wyoming
    'DC': 4140963,  # District of Columbia
}

# Common state name variations
STATE_NAME_TO_CODE = {
    'alabama': 'AL',
    'alaska': 'AK',
    'arizona': 'AZ',
    'arkansas': 'AR',
    'california': 'CA',
    'colorado': 'CO',
    'connecticut': 'CT',
    'delaware': 'DE',
    'florida': 'FL',
    'georgia': 'GA',
    'hawaii': 'HI',
    'idaho': 'ID',
    'illinois': 'IL',
    'indiana': 'IN',
    'iowa': 'IA',
    'kansas': 'KS',
    'kentucky': 'KY',
    'louisiana': 'LA',
    'maine': 'ME',
    'maryland': 'MD',
    'massachusetts': 'MA',
    'michigan': 'MI',
    'minnesota': 'MN',
    'mississippi': 'MS',
    'missouri': 'MO',
    'montana': 'MT',
    'nebraska': 'NE',
    'nevada': 'NV',
    'new hampshire': 'NH',
    'new jersey': 'NJ',
    'new mexico': 'NM',
    'new york': 'NY',
    'north carolina': 'NC',
    'north dakota': 'ND',
    'ohio': 'OH',
    'oklahoma': 'OK',
    'oregon': 'OR',
    'pennsylvania': 'PA',
    'rhode island': 'RI',
    'south carolina': 'SC',
    'south dakota': 'SD',
    'tennessee': 'TN',
    'texas': 'TX',
    'utah': 'UT',
    'vermont': 'VT',
    'virginia': 'VA',
    'washington': 'WA',
    'west virginia': 'WV',
    'wisconsin': 'WI',
    'wyoming': 'WY',
    'district of columbia': 'DC',
    'washington dc': 'DC',
    'washington d.c.': 'DC'
}

def get_geoname_id(state_input: str) -> int:
    """
    Get geoname ID for a state
    
    Args:
        state_input: State code (MI) or name (Michigan)
    
    Returns:
        Geoname ID for the state, or None if not found
    """
    if not state_input:
        return None
    
    # Clean input
    state_str = state_input.strip().upper()
    
    # Check if it's already a state code
    if state_str in STATE_GEONAME_IDS:
        return STATE_GEONAME_IDS[state_str]
    
    # Try to convert state name to code
    state_lower = state_input.strip().lower()
    if state_lower in STATE_NAME_TO_CODE:
        state_code = STATE_NAME_TO_CODE[state_lower]
        return STATE_GEONAME_IDS.get(state_code)
    
    return None

def get_state_code(state_input: str) -> str:
    """
    Get state code from state name or return code if already a code
    
    Args:
        state_input: State code (MI) or name (Michigan)
    
    Returns:
        State code (e.g., 'MI') or None if not found
    """
    if not state_input:
        return None
    
    # Clean input
    state_str = state_input.strip().upper()
    
    # Check if it's already a state code
    if state_str in STATE_GEONAME_IDS:
        return state_str
    
    # Try to convert state name to code
    state_lower = state_input.strip().lower()
    return STATE_NAME_TO_CODE.get(state_lower)