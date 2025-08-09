from typing import Dict, Any
# In production, pull real org data, programs, KPIs, budgets, stories, etc.
def build_data_pack(org_id: int) -> Dict[str, Any]:
    return {
        "org_profile": {"name":"Org "+str(org_id)},
        "programs": [],
        "kpis": [],
        "budget": [],
        "stories": [],
        "assets": []
    }