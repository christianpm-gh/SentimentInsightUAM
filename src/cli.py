"""
Interfaz de línea de comandos para SentimentInsightUAM.

Este módulo proporciona comandos para:
1. Obtener nombres de profesores del directorio UAM Azcapotzalco
2. Scrapear perfiles y reseñas de profesores desde MisProfesores.com

Uso:
    python -m src.cli nombres-uam              # Obtener lista de profesores UAM
    python -m src.cli prof                     # Seleccionar profesor de menú interactivo
    python -m src.cli prof --name "Nombre"     # Scrapear profesor específico
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


def main() -> None:
    """
    Punto de entrada principal del CLI.

    Maneja los comandos:
    - nombres-uam: Extrae y muestra nombres del directorio UAM
    - prof: Scrapea perfil de un profesor (interactivo o por nombre)
    """
    ap = argparse.ArgumentParser(
        description="SentimentInsightUAM - Scraping de reseñas de profesores UAM"
    )
    ap.add_argument("cmd", choices=["nombres-uam", "prof"],
                    help="Comando a ejecutar")
    ap.add_argument("--name", help="Nombre exacto del profesor a scrapear")
    args = ap.parse_args()

    if args.cmd == "nombres-uam":
        res = asyncio.run(get_prof_names())
        print(json.dumps(res, ensure_ascii=False, indent=2))
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
    print(f"Fuente: {'Caché' if res.get('cached', False) else 'Scraping nuevo'}")
    print("="*80)

    # Mostrar JSON completo si se desea
    # print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
