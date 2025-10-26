import asyncio
from src.core.browser import browser_ctx
from src.mp.parser import parse_profile, parse_reviews


async def find_and_scrape(name: str) -> dict:
    async with browser_ctx() as ctx:
        page = await ctx.new_page()
        # TODO: navegar a /Buscar, localizar resultado por nombre, abrir perfil
        html = await page.content()
        prof = parse_profile(html)
        prof["reviews"] = parse_reviews(html)
        return prof

