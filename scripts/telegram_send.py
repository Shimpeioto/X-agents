"""Telegram send helper for Marc agent.

Usage:
    python3 scripts/telegram_send.py "message text"
    python3 scripts/telegram_send.py --file path/to/file.txt

Auto-splits messages >4096 chars (Telegram limit).
Exit codes: 0=success, 1=failure
"""

import json
import sys
import urllib.request
import urllib.error
import urllib.parse

CONFIG_PATH = "config/accounts.json"
MAX_MSG_LEN = 4096


def load_config() -> tuple[str, str]:
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    bot_token = config["telegram"]["bot_token"]
    chat_id = config["telegram"]["chat_id"]
    return bot_token, chat_id


def send_message(bot_token: str, chat_id: str, text: str) -> bool:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            return result.get("ok", False)
    except urllib.error.HTTPError as e:
        print(f"ERROR: Telegram API returned {e.code}: {e.read().decode()}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return False


def send_long_message(bot_token: str, chat_id: str, text: str) -> bool:
    if len(text) <= MAX_MSG_LEN:
        return send_message(bot_token, chat_id, text)

    chunks = []
    while text:
        if len(text) <= MAX_MSG_LEN:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, MAX_MSG_LEN)
        if split_at == -1:
            split_at = MAX_MSG_LEN
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")

    for i, chunk in enumerate(chunks):
        if not send_message(bot_token, chat_id, chunk):
            print(f"ERROR: Failed to send chunk {i+1}/{len(chunks)}", file=sys.stderr)
            return False
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/telegram_send.py \"message\" | --file path", file=sys.stderr)
        sys.exit(2)

    bot_token, chat_id = load_config()

    if sys.argv[1] == "--file":
        if len(sys.argv) < 3:
            print("Usage: python3 scripts/telegram_send.py --file <path>", file=sys.stderr)
            sys.exit(2)
        with open(sys.argv[2]) as f:
            text = f.read()
    else:
        text = sys.argv[1]

    if not text.strip():
        print("ERROR: Empty message", file=sys.stderr)
        sys.exit(1)

    if send_long_message(bot_token, chat_id, text):
        print("OK: Message sent")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
