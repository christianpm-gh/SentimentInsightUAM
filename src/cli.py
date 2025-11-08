"""
Interfaz de línea de comandos para SentimentInsightUAM.

Este módulo proporciona comandos para:
1. Obtener nombres de profesores del directorio UAM Azcapotzalco
2. Scrapear perfiles y reseñas de profesores desde MisProfesores.com
3. Scrapear todos los profesores con caché inteligente

Uso:
    python -m src.cli nombres-uam              # Obtener lista de profesores UAM
    python -m src.cli prof                     # Seleccionar profesor de menú interactivo
    python -m src.cli prof --name "Nombre"     # Scrapear profesor específico
    python -m src.cli scrape-all               # Scrapear todos los profesores
"""
import argparse
import asyncio
import json
from pathlib import Path
from typing import List, Any

from src.uam.nombres_uam import get_prof_names
from src.mp.scrape_prof import find_and_scrape

INPUT_FILE = Path("data/inputs/profesor_nombres.json")


def _normalize_names(data: List[Any]) -> List[str]:
    """
    Normaliza una lista de datos a una lista de nombres de profesores.

    Args:
        data: Lista que puede contener dicts con clave 'name' o strings directos

    Returns:
        Lista de strings con nombres de profesores
    """
    names: List[str] = []
    for item in data:
        if isinstance(item, dict) and "name" in item:
            names.append(str(item["name"]))
        elif isinstance(item, str):
            names.append(item)
    return names


def load_names() -> List[str]:
    """
    Carga nombres de profesores desde archivo o web.

    Si existe el archivo de entrada, lo lee. Si no, obtiene los nombres
    desde el directorio UAM y los guarda para uso futuro.

    Returns:
        Lista de nombres de profesores
    """
    if INPUT_FILE.exists():
        data = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
        return _normalize_names(data)

    # Fallback: obtener desde la web y persistir archivo de entrada
    res = asyncio.run(get_prof_names())
    INPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    INPUT_FILE.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    return _normalize_names(res)


def print_menu(names: List[str], per_row: int = 4) -> None:
    """
    Imprime un menú numerado de profesores en formato de columnas.

    Args:
        names: Lista de nombres de profesores
        per_row: Cantidad de nombres por fila (default: 4)
    """
    line = []
    for idx, name in enumerate(names, start=1):
        line.append(f"[{idx}] {name}")
        if len(line) == per_row:
            print(" ".join(line))
            line = []
    if line:
        print(" ".join(line))


def choose_index(n: int) -> int:
    """
    Solicita al usuario que elija un índice válido del menú.

    Args:
        n: Número total de opciones disponibles

    Returns:
        Índice seleccionado (1-based)
    """
    while True:
        raw = input("Teclea el número del profesor que quieres scrapear> ").strip()
        if raw.isdigit():
            i = int(raw)
            if 1 <= i <= n:
                return i
        print(f"Valor inválido. Escoge un número entre 1 y {n}.")


async def scrape_all_professors() -> None:
    """
    Scrapea todos los profesores del directorio UAM con caché inteligente.

    Este comando:
    1. Carga la lista de profesores desde nombres-uam
    2. Para cada profesor, verifica si necesita actualización
    3. Scrapea solo si hay cambios en el número de reseñas
    4. Aplica delays entre requests para evitar bloqueos

    Delays aplicados:
    - 2-4 segundos entre profesores (evita sobrecarga del servidor)
    - Backoff exponencial automático en find_and_scrape (tenacity)
    """
    names = load_names()
    if not names:
        raise SystemExit("No hay nombres disponibles. Ejecuta primero: python -m src.cli nombres-uam")

    total = len(names)
    print(f"Iniciando scraping de {total} profesores...")
    print("="*80)

    scraped = 0
    cached = 0
    errors = 0

    for idx, name in enumerate(names, start=1):
        try:
            print(f"\n[{idx}/{total}] Procesando: {name}")
            res = await find_and_scrape(name)

            if res.get('cached', False):
                cached += 1
                print(f"  -> Cache vigente ({len(res.get('reviews', []))} reseñas)")
            else:
                scraped += 1
                print(f"  -> Scrapeado exitosamente ({len(res.get('reviews', []))} reseñas)")

            # Delay entre profesores para evitar rate limiting
            # Solo aplicar delay si no es el último profesor
            if idx < total:
                delay = 2 + (2 * (idx % 3))  # Variar entre 2-4 segundos
                print(f"  -> Esperando {delay}s antes del siguiente...")
                await asyncio.sleep(delay)

        except Exception as e:
            errors += 1
            print(f"  -> Error: {str(e)}")
            # Continuar con el siguiente profesor
            continue

    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN DE SCRAPING")
    print("="*80)
    print(f"Total profesores procesados: {total}")
    print(f"Scrapeados exitosamente: {scraped}")
    print(f"Obtenidos de cache: {cached}")
    print(f"Errores: {errors}")
    print("="*80)


def main() -> None:
    """
    Punto de entrada principal del CLI.

    Maneja los comandos:
    - nombres-uam: Extrae y muestra nombres del directorio UAM
    - prof: Scrapea perfil de un profesor (interactivo o por nombre)
    - scrape-all: Scrapea todos los profesores con caché inteligente
    """
    ap = argparse.ArgumentParser(
        description="SentimentInsightUAM - Scraping de reseñas de profesores UAM"
    )
    ap.add_argument("cmd", choices=["nombres-uam", "prof", "scrape-all"],
                    help="Comando a ejecutar")
    ap.add_argument("--name", help="Nombre exacto del profesor a scrapear")
    args = ap.parse_args()

    if args.cmd == "nombres-uam":
        res = asyncio.run(get_prof_names())
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    if args.cmd == "scrape-all":
        asyncio.run(scrape_all_professors())
        return

    # cmd == "prof"
    if args.name:
        sel_name = args.name
    else:
        names = load_names()
        if not names:
            raise SystemExit("No hay nombres disponibles. Ejecuta primero: python -m src.cli nombres-uam")
        print_menu(names, per_row=4)
        idx = choose_index(len(names))
        sel_name = names[idx - 1]

    res = asyncio.run(find_and_scrape(sel_name))

    # Mostrar resumen
    print("\n" + "="*80)
    print(f"Profesor: {res['name']}")
    print(f"Calidad General: {res.get('overall_quality', 'N/A')}")
    print(f"Dificultad: {res.get('difficulty', 'N/A')}")
    print(f"Recomendación: {res.get('recommend_percent', 'N/A')}%")
    print(f"Total de reseñas: {len(res.get('reviews', []))}")
    print(f"Fuente: {'Cache' if res.get('cached', False) else 'Scraping nuevo'}")
    print("="*80)

    # Mostrar JSON completo si se desea
    # print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

