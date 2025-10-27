"""
Módulo para gestionar contextos de navegador con Playwright.

Proporciona un context manager asíncrono para crear instancias de navegador
Chromium con configuración personalizada, incluyendo user agent y modo headless
configurable por variables de entorno.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from dotenv import load_dotenv
from os import getenv
from playwright.async_api import async_playwright, BrowserContext

load_dotenv()
HEADLESS = (getenv("HEADLESS", "true").lower() == "true")


@asynccontextmanager
async def browser_ctx() -> AsyncGenerator[BrowserContext, None]:
    """
    Context manager asíncrono para gestionar el ciclo de vida del navegador.

    Crea un navegador Chromium con un user agent personalizado y lo cierra
    automáticamente al finalizar. El modo headless se configura mediante
    la variable de entorno HEADLESS (default: true).

    Yields:
        BrowserContext: Contexto del navegador de Playwright

    Example:
        async with browser_ctx() as ctx:
            page = await ctx.new_page()
            await page.goto("https://example.com")
    """
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

