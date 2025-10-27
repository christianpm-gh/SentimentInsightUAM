"""
Módulo para extraer nombres y datos de profesores del directorio UAM Azcapotzalco.

Este módulo utiliza web scraping con Playwright y BeautifulSoup para obtener
información de profesores desde el directorio oficial de la UAM.
"""
import asyncio
import json
from typing import List, Dict

from bs4 import BeautifulSoup
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from slugify import slugify
from ..core.browser import browser_ctx

UAM_DIR = "https://sistemas.azc.uam.mx/Somos/Directorio/"


async def get_prof_names() -> List[Dict[str, str]]:
    """
    Obtiene una lista de profesores del directorio UAM Azcapotzalco.

    Esta función navega al directorio UAM, hace clic repetidamente en el botón
    "Ver más Profesorado" hasta cargar todos los profesores, y luego extrae
    sus nombres y URLs.

    Returns:
        List[Dict[str, str]]: Lista de diccionarios con las claves:
            - 'name': Nombre completo del profesor
            - 'slug': Versión normalizada del nombre para URLs
            - 'url': URL completa del perfil del profesor

    Raises:
        RuntimeError: Si no se encuentra la sección Profesorado en la página
    """
    async with browser_ctx() as ctx:
        page = await ctx.new_page()
        await page.goto(UAM_DIR, wait_until="domcontentloaded", timeout=45000)

        # Clic repetido en "Ver más Profesorado"
        # Continúa haciendo clic hasta que el botón ya no esté disponible
        while True:
            try:
                boton = await page.wait_for_selector("span:has-text('Ver más Profesorado')", timeout=3000)
                await boton.click()
                await page.wait_for_timeout(700)
            except PlaywrightTimeoutError:
                # El botón ya no está disponible, todos los profesores se han cargado
                break

        html = await page.content()

    # ---- PARSEO HTML ----
    soup = BeautifulSoup(html, "lxml")

    # Buscar sección de profesorado por el texto del encabezado
    # Busca todos los h2 que contengan la palabra "Profesorado"
    prof_sections = soup.find_all("h2")
    prof_section = None
    for section in prof_sections:
        if section.string and "Profesorado" in section.string:
            prof_section = section
            break

    if not prof_section:
        raise RuntimeError("No se encontró la sección Profesorado")

    # Obtener el contenedor con las tarjetas de profesores
    container = prof_section.find_next("section")

    # Extraer todas las tarjetas de profesores (links con clase svelte)
    cards = container.find_all("a", href=True, class_=lambda c: c and "svelte" in c)

    results: List[Dict[str, str]] = []
    for card in cards:
        # Extraer nombre (h4) y apellido (h5) del profesor
        h4 = card.find("h4")
        h5 = card.find("h5")
        if not h4 or not h5:
            continue

        # Construir nombre completo y slug
        nombre = f"{h4.get_text(strip=True)} {h5.get_text(strip=True)}"
        href = card["href"]

        results.append({
            "name": nombre,
            "slug": slugify(nombre),
            "url": f"https://sistemas.azc.uam.mx{href}"
        })

    return results


if __name__ == "__main__":
    # Ejecutar la función y mostrar resultados en formato JSON
    out = asyncio.run(get_prof_names())
    print(json.dumps(out, ensure_ascii=False, indent=2))
