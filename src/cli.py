"""
Interfaz de línea de comandos para SentimentInsightUAM.

Este módulo proporciona comandos para:
1. Obtener nombres de profesores del directorio UAM Azcapotzalco
2. Scrapear perfiles y reseñas de profesores desde MisProfesores.com
3. Scrapear todos los profesores con caché inteligente
4. Mostrar estado de las bases de datos

Uso:
    python -m src.cli nombres-uam              # Obtener lista de profesores UAM
    python -m src.cli prof                     # Seleccionar profesor de menú interactivo
    python -m src.cli prof --name "Nombre"     # Scrapear profesor específico
    python -m src.cli scrape-all               # Scrapear todos los profesores
    python -m src.cli db-sample                # Mostrar un registro de cada tabla
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


async def show_db_samples() -> None:
    """
    Muestra un registro de ejemplo de cada tabla en PostgreSQL y MongoDB.
    """
    from src.db import get_db_session, get_mongo_db
    from src.db.models import (
        Profesor, Perfil, Etiqueta, PerfilEtiqueta, Curso,
        ReseniaMetadata, ReseniaEtiqueta, HistorialScraping
    )
    from sqlalchemy import select
    
    print("=" * 80)
    print("MUESTRAS DE REGISTROS EN BASES DE DATOS")
    print("=" * 80)
    
    # ========================================================================
    # PostgreSQL
    # ========================================================================
    print("\n🐘 POSTGRESQL")
    print("-" * 80)
    
    async with get_db_session() as session:
        # Profesor
        result = await session.execute(select(Profesor).limit(1))
        prof = result.scalar_one_or_none()
        print("\n📌 PROFESORES:")
        if prof:
            print(f"   id: {prof.id}")
            print(f"   nombre_completo: {prof.nombre_completo}")
            print(f"   nombre_limpio: {prof.nombre_limpio}")
            print(f"   slug: {prof.slug}")
            print(f"   departamento: {prof.departamento}")
            print(f"   activo: {prof.activo}")
        else:
            print("   (vacía)")
        
        # Perfil
        result = await session.execute(select(Perfil).limit(1))
        perfil = result.scalar_one_or_none()
        print("\n📌 PERFILES:")
        if perfil:
            print(f"   id: {perfil.id}")
            print(f"   profesor_id: {perfil.profesor_id}")
            print(f"   calidad_general: {perfil.calidad_general}")
            print(f"   dificultad: {perfil.dificultad}")
            print(f"   porcentaje_recomendacion: {perfil.porcentaje_recomendacion}")
            print(f"   total_resenias_encontradas: {perfil.total_resenias_encontradas}")
        else:
            print("   (vacía)")
        
        # Curso
        result = await session.execute(select(Curso).limit(1))
        curso = result.scalar_one_or_none()
        print("\n📌 CURSOS:")
        if curso:
            print(f"   id: {curso.id}")
            print(f"   nombre: {curso.nombre}")
            print(f"   nombre_normalizado: {curso.nombre_normalizado}")
            print(f"   departamento: {curso.departamento}")
        else:
            print("   (vacía)")
        
        # Etiqueta
        result = await session.execute(select(Etiqueta).limit(1))
        etiq = result.scalar_one_or_none()
        print("\n📌 ETIQUETAS:")
        if etiq:
            print(f"   id: {etiq.id}")
            print(f"   etiqueta: {etiq.etiqueta}")
            print(f"   etiqueta_normalizada: {etiq.etiqueta_normalizada}")
            print(f"   categoria: {etiq.categoria}")
        else:
            print("   (vacía)")
        
        # ReseniaMetadata
        result = await session.execute(select(ReseniaMetadata).limit(1))
        resenia = result.scalar_one_or_none()
        print("\n📌 RESENIAS_METADATA:")
        if resenia:
            print(f"   id: {resenia.id}")
            print(f"   profesor_id: {resenia.profesor_id}")
            print(f"   curso_id: {resenia.curso_id}")
            print(f"   fecha_resenia: {resenia.fecha_resenia}")
            print(f"   calidad_general: {resenia.calidad_general}")
            print(f"   facilidad: {resenia.facilidad}")
            print(f"   tiene_comentario: {resenia.tiene_comentario}")
            print(f"   mongo_opinion_id: {resenia.mongo_opinion_id}")
        else:
            print("   (vacía)")
        
        # PerfilEtiqueta
        result = await session.execute(select(PerfilEtiqueta).limit(1))
        pe = result.scalar_one_or_none()
        print("\n📌 PERFIL_ETIQUETAS:")
        if pe:
            print(f"   id: {pe.id}")
            print(f"   perfil_id: {pe.perfil_id}")
            print(f"   etiqueta_id: {pe.etiqueta_id}")
            print(f"   contador: {pe.contador}")
        else:
            print("   (vacía)")
        
        # ReseniaEtiqueta
        result = await session.execute(select(ReseniaEtiqueta).limit(1))
        re = result.scalar_one_or_none()
        print("\n📌 RESENIA_ETIQUETAS:")
        if re:
            print(f"   id: {re.id}")
            print(f"   resenia_id: {re.resenia_id}")
            print(f"   etiqueta_id: {re.etiqueta_id}")
        else:
            print("   (vacía)")
        
        # HistorialScraping
        result = await session.execute(select(HistorialScraping).limit(1))
        hist = result.scalar_one_or_none()
        print("\n📌 HISTORIAL_SCRAPING:")
        if hist:
            print(f"   id: {hist.id}")
            print(f"   profesor_id: {hist.profesor_id}")
            print(f"   estado: {hist.estado}")
            print(f"   resenias_encontradas: {hist.resenias_encontradas}")
            print(f"   resenias_nuevas: {hist.resenias_nuevas}")
            print(f"   duracion_segundos: {hist.duracion_segundos}")
        else:
            print("   (vacía)")
    
    # ========================================================================
    # MongoDB
    # ========================================================================
    print("\n" + "-" * 80)
    print("🍃 MONGODB")
    print("-" * 80)
    
    mongo_db = get_mongo_db()
    
    # Opiniones
    opinion = await mongo_db.opiniones.find_one()
    print("\n📌 OPINIONES:")
    if opinion:
        print(f"   _id: {opinion.get('_id')}")
        print(f"   profesor_id: {opinion.get('profesor_id')}")
        print(f"   profesor_nombre: {opinion.get('profesor_nombre')}")
        print(f"   resenia_id: {opinion.get('resenia_id')}")
        print(f"   curso: {opinion.get('curso')}")
        print(f"   comentario: {opinion.get('comentario', '')[:100]}...")
        print(f"   sentimiento_general.analizado: {opinion.get('sentimiento_general', {}).get('analizado')}")
        print(f"   sentimiento_general.clasificacion: {opinion.get('sentimiento_general', {}).get('clasificacion')}")
    else:
        print("   (vacía)")
    
    # Sentimiento Cache
    cache = await mongo_db.sentimiento_cache.find_one()
    print("\n📌 SENTIMIENTO_CACHE:")
    if cache:
        print(f"   _id: {cache.get('_id')}")
        for key, value in cache.items():
            if key != '_id':
                print(f"   {key}: {value}")
    else:
        print("   (vacía)")
    
    print("\n" + "=" * 80)


def main() -> None:
    """
    Punto de entrada principal del CLI.

    Maneja los comandos:
    - nombres-uam: Extrae y muestra nombres del directorio UAM
    - prof: Scrapea perfil de un profesor (interactivo o por nombre)
    - scrape-all: Scrapea todos los profesores con caché inteligente
    - db-sample: Muestra un registro de cada tabla en las bases de datos
    """
    ap = argparse.ArgumentParser(
        description="SentimentInsightUAM - Scraping de reseñas de profesores UAM"
    )
    ap.add_argument("cmd", choices=["nombres-uam", "prof", "scrape-all", "db-sample"],
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

    if args.cmd == "db-sample":
        asyncio.run(show_db_samples())
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

