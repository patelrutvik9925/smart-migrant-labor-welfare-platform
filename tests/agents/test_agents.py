"""
Phase 12 — Agent smoke tests
Tests individual agent responses via watsonx Orchestrate chat API.
"""
import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Test cases — (agent_name, message, expected_keywords)
AGENT_TESTS = [
    (
        "migrant_welfare_coordinator",
        "I am a construction worker in Gujarat earning Rs 300 per day. Is my wage fair?",
        ["wage", "minimum", "Gujarat", "labour"],
    ),
    (
        "migrant_welfare_coordinator",
        "What is the e-Shram portal and how can I register?",
        ["e-Shram", "eshram.gov.in", "register", "UAN"],
    ),
    (
        "migrant_welfare_coordinator",
        "My employer is not paying me wages for 2 months. What should I do?",
        ["complaint", "Labour", "helpline"],
    ),
    (
        "migrant_welfare_coordinator",
        "मैं गुजरात में काम कर रहा हूँ। मुझे कौन सी सरकारी योजनाएं मिल सकती हैं?",
        ["e-Shram", "योजना"],
    ),
    (
        "welfare_scheme_agent",
        "Tell me about BOCW welfare board for construction workers in Gujarat",
        ["BOCW", "construction", "Gujarat", "register"],
    ),
    (
        "wage_fairness_agent",
        "I earn Rs 250 per day as an unskilled worker in Gujarat. Is this fair?",
        ["minimum wage", "Gujarat", "labour"],
    ),
    (
        "safety_grievance_agent",
        "My employer is physically abusing workers. What should I do?",
        ["100", "police", "CRITICAL"],
    ),
]


def run_agent_tests():
    """
    Run agent smoke tests. Requires active Orchestrate environment.
    Uses the MCP chat tool pattern (run manually or via CI with env configured).
    """
    print("\n" + "="*60)
    print("PHASE 12 — AGENT SMOKE TESTS")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for agent_name, message, expected_keywords in AGENT_TESTS:
        print(f"\nTesting: {agent_name}")
        print(f"  Message: {message[:80]}...")
        print(f"  Expected keywords: {expected_keywords}")
        print(f"  [MANUAL] Chat with agent '{agent_name}' using message above")
        print(f"  [MANUAL] Verify response contains keywords: {expected_keywords}")
        print(f"  Status: REQUIRES_MANUAL_VERIFICATION")
    
    print("\n" + "="*60)
    print("Automated agent chat tests require running with active Orchestrate")
    print("session. Use the watsonx Orchestrate UI or the MCP chat tool to")  
    print("manually verify each test case above.")
    print("="*60)


if __name__ == "__main__":
    run_agent_tests()
