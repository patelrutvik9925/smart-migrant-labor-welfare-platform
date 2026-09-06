"""
Integration test — Full coordinator workflow
Tests main coordinator routing to all specialized agents.
"""

WORKFLOW_TESTS = [
    {
        "name": "Worker welfare inquiry",
        "message": "I am a migrant worker in Gujarat. What schemes can I apply for?",
        "expected_agent_route": "welfare_scheme_agent",
        "expected_keywords": ["e-Shram", "welfare", "scheme"],
    },
    {
        "name": "Wage fairness check",
        "message": "I earn Rs 400 per day as a painter in Surat. Is this fair?",
        "expected_agent_route": "wage_fairness_agent",
        "expected_keywords": ["wage", "minimum", "Gujarat"],
    },
    {
        "name": "Grievance — wage theft",
        "message": "My employer has not paid my wages for 3 months",
        "expected_agent_route": "safety_grievance_agent",
        "expected_keywords": ["complaint", "Labour", "helpline"],
    },
    {
        "name": "Profile/skills update",
        "message": "I want to update my skills and current location",
        "expected_agent_route": "skill_location_agent",
        "expected_keywords": ["profile", "skill", "location"],
    },
    {
        "name": "Hindi language support",
        "message": "मेरी मजदूरी बहुत कम है। मैं क्या कर सकता हूँ?",
        "expected_agent_route": "wage_fairness_agent or safety_grievance_agent",
        "expected_keywords": ["मजदूरी", "न्यूनतम", "शिकायत"],
    },
    {
        "name": "Critical safety — CRITICAL priority check",
        "message": "My employer is threatening and assaulting workers",
        "expected_agent_route": "safety_grievance_agent",
        "expected_keywords": ["100", "police", "CRITICAL"],
    },
    {
        "name": "Multi-topic request",
        "message": "Check my wage fairness AND tell me which welfare schemes I qualify for",
        "expected_agent_route": "multiple (wage_fairness_agent + welfare_scheme_agent)",
        "expected_keywords": ["wage", "scheme"],
    },
]


def print_workflow_test_plan():
    print("\n" + "="*60)
    print("PHASE 13 — COORDINATOR WORKFLOW INTEGRATION TESTS")
    print("="*60)
    for i, t in enumerate(WORKFLOW_TESTS, 1):
        print(f"\n[TEST {i}] {t['name']}")
        print(f"  Message: {t['message']}")
        print(f"  Expected route: {t['expected_agent_route']}")
        print(f"  Expected keywords: {t['expected_keywords']}")
    print("\n" + "="*60)
    print("Run these tests via the watsonx Orchestrate UI or MCP chat tool")
    print("using agent: migrant_welfare_coordinator")
    print("="*60)


if __name__ == "__main__":
    print_workflow_test_plan()
