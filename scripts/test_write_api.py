#!/usr/bin/env python3
"""Test 7 — Verify XApiWriteClient OAuth 1.0a auth for EN and JP accounts."""

import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from x_api import XApiWriteClient


def test_account(account: str) -> bool:
    try:
        client = XApiWriteClient(account)
        user_id = client.get_own_user_id()
        if user_id and isinstance(user_id, str) and user_id.isdigit():
            print(f"✅ {account} Auth OK — user_id: {user_id}")
            return True
        else:
            print(f"❌ {account} Auth FAILED — invalid user_id: {user_id}")
            return False
    except Exception as e:
        print(f"❌ {account} Auth FAILED — {e}")
        return False


if __name__ == "__main__":
    results = []
    for acct in ["EN", "JP"]:
        results.append(test_account(acct))

    if all(results):
        print("\n✅ Test 7 PASSED — both accounts authenticated")
    else:
        print("\n❌ Test 7 FAILED — see errors above")
        sys.exit(1)
