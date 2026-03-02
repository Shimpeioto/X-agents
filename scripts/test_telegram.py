import json, asyncio, os
from telegram import Bot

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(PROJECT, "config/accounts.json")) as f:
    config = json.load(f)

async def main():
    bot = Bot(token=config["telegram"]["bot_token"])
    msg = await bot.send_message(
        chat_id=config["telegram"]["chat_id"],
        text="🤖 AI Beauty Agent System — Test message\n\nTelegram is working!"
    )
    print(f"✅ Telegram OK — Message ID: {msg.message_id}")

asyncio.run(main())
