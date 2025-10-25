#!/usr/bin/env python3
"""Test script for Clara /prompt endpoint with CLIPS integration."""

import requests
import json
import sys

def test_prompt_endpoint():
    """Test the /prompt endpoint."""

    BASE_URL = "http://127.0.0.1:8000"
    TOKEN = "mysecrettoken"

    # Test 1: Simple prompt without CLIPS
    print("=" * 60)
    print("Test 1: Simple prompt without CLIPS facts/rules")
    print("=" * 60)

    payload = {
        "query": "What is the meaning of life?",
        "use_clips": False
    }

    headers = {"Authorization": f"Bearer {TOKEN}"}

    try:
        response = requests.post(
            f"{BASE_URL}/clara/api/v1/prompt",
            json=payload,
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✓ Query: {result['query']}")
            print(f"✓ Response: {result['response']}")
            print(f"✓ Reasoning: {json.dumps(result['reasoning'], indent=2)}")
        else:
            print(f"✗ Request failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    # Test 2: Prompt with facts
    print("\n" + "=" * 60)
    print("Test 2: Prompt with facts")
    print("=" * 60)

    payload = {
        "query": "What color is the sky?",
        "facts": [
            "(weather clear)",
            "(time day)",
            "(property sky color blue)"
        ],
        "use_clips": True
    }

    try:
        response = requests.post(
            f"{BASE_URL}/clara/api/v1/prompt",
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✓ Query: {result['query']}")
            print(f"✓ Response: {result['response']}")
            if result.get('clips_output'):
                print(f"✓ CLIPS Output: {result['clips_output'][:200]}")
            print(f"✓ Reasoning: {json.dumps(result['reasoning'], indent=2)}")
        else:
            print(f"✗ Request failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server. Make sure:")
        print("  1. Clara server is running: python -m uvicorn app.main:app")
        print("  2. Clara Cerebrum API is running: cargo run --bin clara-api")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    # Test 3: Prompt with rules
    print("\n" + "=" * 60)
    print("Test 3: Prompt with rules")
    print("=" * 60)

    payload = {
        "query": "Is the person old?",
        "facts": [
            "(person alice)",
            "(age alice 85)"
        ],
        "rules": """
            (defrule determine-age-status
                (age ?name ?years)
                (test (>= ?years 65))
                =>
                (printout t ?name " is senior" crlf)
            )
        """,
        "use_clips": True
    }

    try:
        response = requests.post(
            f"{BASE_URL}/clara/api/v1/prompt",
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✓ Query: {result['query']}")
            print(f"✓ Response: {result['response']}")
            if result.get('clips_output'):
                print(f"✓ CLIPS Output:\n{result['clips_output']}")
            print(f"✓ Reasoning: {json.dumps(result['reasoning'], indent=2)}")
        else:
            print(f"✗ Request failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_prompt_endpoint()
    sys.exit(0 if success else 1)
