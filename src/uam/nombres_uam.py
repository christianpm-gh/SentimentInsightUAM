import asyncio
from bs4 import BeautifulSoup
from src.core.browser import browser_ctx

UAM_DIR = "https://sistemas.azc.uam.mx/Somos/Directorio/"


async def get_prof_names() -> list[dict]:
    async with browser_ctx() as ctx:
        page = await ctx.new_page()
        await page.goto(UAM_DIR, wait_until="domcontentloaded", timeout=45000)
        html = await page.content()
        soup = BeautifulSoup(html, "lxml")
        # TODO: localizar sección "Profesorado" y extraer enlaces/nombres.
        return []  # devolver [{"name": "..."}]

