import tweepy, json, sys, os

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(PROJECT, "config/accounts.json")) as f:
    config = json.load(f)

xapi = config["x_api"]
account = sys.argv[1] if len(sys.argv) > 1 else "EN"
acc = xapi["accounts"][account]

# Test user-level auth (OAuth 1.0a)
auth_client = tweepy.Client(
    consumer_key=xapi["consumer_key"], consumer_secret=xapi["consumer_secret"],
    access_token=acc["access_token"], access_token_secret=acc["access_token_secret"]
)
me = auth_client.get_me()
if me.data:
    print(f"✅ Auth OK — @{me.data.username} (user_id: {me.data.id})")
else:
    print(f"❌ Auth FAILED")
    sys.exit(1)

# Test read via user auth
user = auth_client.get_user(username=acc["handle"].lstrip("@"))
if user.data:
    print(f"✅ Read OK — {account}: @{user.data.username}")
else:
    print(f"❌ Read FAILED")

# Test bearer token separately
try:
    bearer_client = tweepy.Client(bearer_token=xapi["bearer_token"])
    bearer_user = bearer_client.get_user(username=acc["handle"].lstrip("@"))
    print(f"✅ Bearer token OK" if bearer_user.data else "❌ Bearer token FAILED")
except Exception as e:
    print(f"⚠️  Bearer token FAILED — {e}")
    print(f"   → Re-copy bearer token from Developer Portal (no URL-encoding)")
