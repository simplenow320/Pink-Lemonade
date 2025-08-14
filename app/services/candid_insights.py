"""
Candid Insights Service for Transaction Analysis
"""
from typing import Optional, Dict, List
from app.services.candid_client import get_candid_client

def transactions_snapshot(topic: str, geo: str) -> Optional[Dict]:
    """
    Get transaction snapshot for a topic and geography
    
    Args:
        topic: Topic/keyword to search for
        geo: Geographic location/region
        
    Returns:
        Dictionary with award statistics or None if no data
    """
    try:
        client = get_candid_client()
        
        # Search for transactions matching topic and geo
        query = f"{topic} AND {geo}" if topic and geo else topic or geo
        if not query:
            return None
            
        result = client.search_transactions(query, page=1, size=100)
        
        # Check for errors or empty results
        if "error" in result or not result.get("transactions"):
            return None
            
        transactions = result.get("transactions", [])
        if not transactions:
            return None
            
        # Extract award amounts (never invent numbers)
        amounts = []
        funders = set()
        
        for txn in transactions:
            # Safely extract amount
            amount = txn.get("amount") or txn.get("award_amount")
            if amount and isinstance(amount, (int, float)) and amount > 0:
                amounts.append(amount)
                
            # Collect funder names
            funder = txn.get("funder") or txn.get("funder_name") or txn.get("foundation")
            if funder:
                funders.add(str(funder))
        
        # Return None if no valid data
        if not amounts:
            return None
            
        # Calculate statistics
        amounts.sort()
        median_idx = len(amounts) // 2
        
        snapshot = {
            "award_count": len(amounts),
            "median_award": amounts[median_idx] if amounts else None,
            "recent_funders": list(funders)[:5],  # Top 5 funders
            "source_notes": f"Based on {len(transactions)} transactions matching '{query}'"
        }
        
        return snapshot
        
    except Exception as e:
        # Return None on any error - never invent data
        print(f"Error in transactions_snapshot: {e}")
        return None