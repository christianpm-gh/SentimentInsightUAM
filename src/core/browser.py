from contextlib import asynccontextmanager
from dotenv import load_dotenv
from os import getenv
from playwright.async_api import async_playwright

load_dotenv()
HEADLESS = (getenv("HEADLESS", "true").lower() == "true")


@asynccontextmanager
async def browser_ctx():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        ctx = await browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/122 Safari/537.36")
        )
        try:
            yield ctx
        finally:
            await ctx.close()
            await browser.close()

