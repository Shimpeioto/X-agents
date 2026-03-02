"""
Generate user-level OAuth 1.0a tokens for an X account.
Run once per account (EN, JP) to get access_token + access_token_secret.

Usage:
    python3 scripts/generate_tokens.py
"""

import json, os, tweepy

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(PROJECT, "config/accounts.json")) as f:
    config = json.load(f)

consumer_key = config["x_api"]["consumer_key"]
consumer_secret = config["x_api"]["consumer_secret"]

# Step 1: Get authorization URL
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
try:
    redirect_url = auth.get_authorization_url()
except tweepy.TweepyException as e:
    print(f"❌ Failed to get authorization URL: {e}")
    raise

print("=" * 60)
print("  X API — Generate User-Level Tokens")
print("=" * 60)
print()
print("1. Open this URL in your browser:")
print(f"   {redirect_url}")
print()
print("2. Log in with the account you want to authorize (EN or JP)")
print("3. Click 'Authorize app'")
print("4. Copy the PIN code shown on the page")
print()

pin = input("Enter the PIN: ").strip()

try:
    auth.get_access_token(pin)
    print()
    print("✅ Success! Here are your tokens:")
    print(f"   access_token:        {auth.access_token}")
    print(f"   access_token_secret: {auth.access_token_secret}")
    print()
    print("Copy these into config/accounts.json under the correct account (EN or JP).")
except tweepy.TweepyException as e:
    print(f"❌ Failed to get access token: {e}")
