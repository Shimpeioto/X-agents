import asyncio, os
from playwright.async_api import async_playwright

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

async def setup_profile(account_name, profile_dir):
    full_path = os.path.join(PROJECT, profile_dir)
    print(f"\n{'='*50}")
    print(f"Setting up browser profile for {account_name}")
    print(f"1. Log into X with your {account_name} account")
    print(f"2. Close the browser window when done")
    print(f"{'='*50}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            full_path, headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await browser.new_page()
        await page.goto("https://x.com/login")
        try:
            await browser.wait_for_event("close", timeout=300000)
        except:
            await browser.close()
    print(f"✅ {account_name} profile saved!")

async def main():
    await setup_profile("EN", "browser_profiles/en_profile")
    await setup_profile("JP", "browser_profiles/jp_profile")

asyncio.run(main())
