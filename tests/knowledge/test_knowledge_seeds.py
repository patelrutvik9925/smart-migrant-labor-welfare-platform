"""
Knowledge base validation tests.
Verifies that knowledge seed data is properly structured and references valid official sources.
"""

def test_knowledge_seeds():
    """Validate that all knowledge seeds have required fields."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    
    from knowledge.seeds.initial_knowledge import KNOWLEDGE_SEEDS
    
    required_fields = ["version_number", "category", "title", "content", "source_name", "source_url", "source_type", "tags"]
    
    print(f"\nValidating {len(KNOWLEDGE_SEEDS)} knowledge seeds...")
    
    all_passed = True
    for i, seed in enumerate(KNOWLEDGE_SEEDS):
        for field in required_fields:
            if field not in seed:
                print(f"  FAIL: Seed {i} missing field '{field}' — Title: {seed.get('title', 'N/A')}")
                all_passed = False
        
        # Verify source URLs are official government domains
        url = seed.get("source_url", "")
        official_domains = [".gov.in", ".nic.in", "eshram.gov.in", "labour.gov.in", "labour.gujarat.gov.in"]
        if not any(domain in url for domain in official_domains):
            print(f"  WARN: Seed {i} may not use official government source: {url}")
        
        # Verify content is not empty
        if len(seed.get("content", "")) < 50:
            print(f"  FAIL: Seed {i} content too short — Title: {seed.get('title', 'N/A')}")
            all_passed = False
    
    if all_passed:
        print(f"  PASS: All {len(KNOWLEDGE_SEEDS)} seeds validated successfully")
    else:
        print(f"  Some seeds failed validation — see above")
    
    return all_passed


if __name__ == "__main__":
    result = test_knowledge_seeds()
    print("\nKnowledge validation:", "PASSED" if result else "FAILED")
