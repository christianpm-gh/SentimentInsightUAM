"""
Módulo para realizar scraping de perfiles y reseñas de profesores en MisProfesores.com

Este módulo utiliza Playwright para navegar y extraer información de profesores,
incluyendo sus calificaciones, etiquetas y reseñas de estudiantes.

Características:
- Caché inteligente: Detecta si el número de reseñas no ha cambiado
- Persistencia: Guarda HTML y JSON en disco
- Scraping eficiente: Evita re-scraping innecesario
"""
import asyncio
import json
import random
from pathlib import Path
from typing import Dict, Any, Optional
from slugify import slugify

from tenacity import retry, wait_random_exponential, stop_after_attempt
from ..core.browser import browser_ctx
from .parser import parse_profile, parse_reviews, page_count

# Importar funciones de persistencia
try:
    from ..db.repository import guardar_profesor_completo
    DB_ENABLED = True
except ImportError:
    DB_ENABLED = False
    print("⚠ Advertencia: Módulo de base de datos no disponible. Solo se guardará JSON.")

BASE = "https://www.misprofesores.com"

# Directorios de salida
HTML_OUTPUT_DIR = Path("data/outputs/html")
JSON_OUTPUT_DIR = Path("data/outputs/profesores")


def _get_cached_data(prof_name: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene datos cacheados de un profesor si existen.

    Args:
        prof_name: Nombre del profesor

    Returns:
        Dict con datos del profesor o None si no existe caché
    """
    slug = slugify(prof_name)
    json_file = JSON_OUTPUT_DIR / f"{slug}.json"

    if json_file.exists():
        try:
            return json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            return None
    return None


def _save_html(prof_name: str, html: str) -> Path:
    """
    Guarda el HTML de un profesor en disco.

    Args:
        prof_name: Nombre del profesor
        html: Contenido HTML a guardar

    Returns:
        Path del archivo guardado
    """
    HTML_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(prof_name)
    html_file = HTML_OUTPUT_DIR / f"{slug}.html"
    html_file.write_text(html, encoding="utf-8")
    return html_file


def _save_json(prof_name: str, data: Dict[str, Any]) -> Path:
    """
    Guarda los datos estructurados de un profesor en JSON.

    Args:
        prof_name: Nombre del profesor
        data: Datos a guardar

    Returns:
        Path del archivo guardado
    """
    JSON_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(prof_name)
    json_file = JSON_OUTPUT_DIR / f"{slug}.json"
    json_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    return json_file


async def open_with_backoff(page, url: str) -> None:
    """
    Abre una URL con un tiempo de espera aleatorio para evitar detección.

    Args:
        page: Instancia de página de Playwright
        url: URL a navegar
    """
    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    await page.wait_for_timeout(400 + int(600 * random.random()))

@retry(wait=wait_random_exponential(min=1, max=8), stop=stop_after_attempt(4))
async def fetch_prof_html(ctx, prof_url: str) -> str:
    """
    Obtiene el HTML de la página de un profesor con reintentos automáticos.

    Utiliza tenacity para reintentar la petición con backoff exponencial
    en caso de fallos temporales de red o timeouts.

    Args:
        ctx: Contexto del navegador de Playwright
        prof_url: URL del perfil del profesor

    Returns:
        str: Contenido HTML de la página

    Raises:
        Exception: Sí fallan todos los intentos después de 4 reintentos
    """
    page = await ctx.new_page()
    await page.goto(prof_url, wait_until="domcontentloaded", timeout=45000)
    html = await page.content()
    await page.close()
    return html

async def find_and_scrape(prof_name: str, school_hint: str = "UAM (Azcapotzalco)", force: bool = False) -> Dict[str, Any]:
    """
    Busca un profesor por nombre y extrae su perfil completo con todas sus reseñas.

    Implementa caché inteligente:
    - Si el profesor ya fue scrapeado y el número de reseñas no ha cambiado, retorna caché
    - Guarda HTML y JSON en disco para auditoría y análisis offline
    - Permite forzar re-scraping con el parámetro force

    Esta función realiza las siguientes operaciones:
    1. Verifica si existe caché del profesor
    2. Navega a la búsqueda de MisProfesores.com
    3. Busca al profesor por nombre
    4. Compara número de reseñas con caché (si existe)
    5. Si no hay cambios, retorna caché (eficiencia)
    6. Si hay cambios, extrae información completa
    7. Guarda HTML y JSON en disco

    Args:
        prof_name: Nombre completo del profesor a buscar
        school_hint: Escuela del profesor (por defecto "UAM (Azcapotzalco)")
                    Disponible para filtrado manual si es necesario
        force: Si True, fuerza re-scraping ignorando caché

    Returns:
        Dict con la estructura:
            - name: Nombre del profesor
            - overall_quality: Calificación general
            - difficulty: Nivel de dificultad
            - recommend_percent: Porcentaje de recomendación
            - tags: Lista de etiquetas con conteos
            - reviews: Lista completa de reseñas paginadas
            - cached: True si se usó caché, False si se scrapeó

    Raises:
        Exception: Si no se encuentra el profesor o hay errores de navegación
    """
    # 1) Verificar caché existente
    cached_data = None if force else _get_cached_data(prof_name)

    # school_hint está disponible para filtrado manual si se requiere en el futuro
    async with browser_ctx() as ctx:
        # 2) Buscar profesor en el sitio con búsqueda robusta
        page = await ctx.new_page()

        # --- Búsqueda mejorada con navegación por href ---
        import re
        import unicodedata

        def _norm(s: str) -> str:
            """Normaliza texto removiendo acentos, espacios extras y convirtiendo a minúsculas."""
            s = unicodedata.normalize("NFKD", s)
            s = "".join(c for c in s if not unicodedata.combining(c))
            return re.sub(r"\s+", " ", s).strip().lower()

        await page.goto(f"{BASE}/Buscar", wait_until="domcontentloaded", timeout=45000)

        search = page.locator("input[type='text'], input[role='combobox']").first
        await search.fill(prof_name)
        await page.keyboard.press("Enter")

        # Espera resultados de perfiles, sin networkidle
        await page.wait_for_selector("a[href*='/profesores/']", timeout=30000)
        cands = page.locator("a[href*='/profesores/']")

        # Match normalizado, fallback al primero
        idx = 0
        target = _norm(prof_name)
        count = await cands.count()
        for i in range(count):
            txt = (await cands.nth(i).inner_text()).strip()
            if _norm(txt) == target:
                idx = i
                break

        href = await cands.nth(idx).get_attribute("href")
        if not href:
            raise RuntimeError("No se encontró enlace de perfil.")
        if href.startswith("/"):
            href = f"{BASE}{href}"

        # Navegar directo al perfil y esperar contenedores del perfil
        await page.goto(href, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_selector("div.rating-breakdown, div.rating-filter.togglable", timeout=30000)
        # --- Fin búsqueda mejorada ---

        # 3) Extraer información del perfil
        profile_url = page.url
        html = await page.content()

        prof = parse_profile(html)
        pages = page_count(html)

        # Calcular número esperado de reseñas
        expected_reviews = pages * 5  # Aproximación (5 reseñas por página)

        # 4) Verificar si hay cambios respecto al caché
        if cached_data and not force:
            cached_reviews_count = len(cached_data.get("reviews", []))

            # Si el número de reseñas es el mismo, retornar caché
            if abs(cached_reviews_count - expected_reviews) <= 5:  # Tolerancia de ±5
                print(f"✓ Caché vigente para {prof_name} ({cached_reviews_count} reseñas)")
                cached_data["cached"] = True
                return cached_data
            else:
                print(f"✓ Detectados cambios para {prof_name}: {cached_reviews_count} → ~{expected_reviews} reseñas")

        # 5) Scraping completo (hay cambios o no hay caché)
        print(f"⚙ Scrapeando {prof_name} ({pages} páginas)...")
        all_reviews = []
        all_html_pages = []

        for p in range(1, pages + 1):
            url = profile_url if p == 1 else f"{profile_url}?pag={p}"
            if p > 1:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_selector("div.rating-filter.togglable table.tftable", timeout=30000)
                html = await page.content()

            all_html_pages.append(html)
            all_reviews += parse_reviews(html)

            # Agregar todas las reseñas al perfil
            prof["reviews"] = all_reviews
            prof["cached"] = False

            # 6) Guardar HTML y JSON
            # Guardar HTML de la primera página (más representativo)
            html_path = _save_html(prof_name, all_html_pages[0])
            json_path = _save_json(prof_name, prof)

            print(f"✓ Guardado: HTML en {html_path.name}, JSON en {json_path.name}")
            print(f"✓ Total reseñas extraídas: {len(all_reviews)}")
            
            # 7) Guardar en bases de datos (PostgreSQL + MongoDB)
            if DB_ENABLED:
                try:
                    print("\n💾 Guardando en bases de datos...")
                    profesor_id = await guardar_profesor_completo(prof, url_misprofesores=profile_url)
                    print(f"✅ Datos guardados en BD (Profesor ID={profesor_id})")
                except Exception as e:
                    print(f"⚠ Error al guardar en BD: {e}")
                    print("   Los datos JSON se mantienen como respaldo")

            return prof


if __name__ == "__main__":
    import sys

    # Obtener nombre del profesor desde argumentos de línea de comandos
    # Si no se proporciona, usa un nombre por defecto
    name = " ".join(sys.argv[1:]) or "Josue Padilla"

    # Ejecutar la búsqueda y scraping (con caché inteligente)
    data = asyncio.run(find_and_scrape(name))

    # Los archivos ya se guardaron automáticamente
    # Mostrar resultado en consola
    print("\n" + "="*60)
    print(f"Profesor: {data['name']}")
    print(f"Calidad: {data['overall_quality']}")
    print(f"Dificultad: {data['difficulty']}")
    print(f"Recomendación: {data['recommend_percent']}%")
    print(f"Total reseñas: {len(data['reviews'])}")
    print(f"Caché usado: {'Sí' if data.get('cached', False) else 'No'}")
    print("="*60)

