#!/usr/bin/env python3
"""
Script para aplicar el mapeo manual de cursos a MongoDB.

Lee el archivo mapeo_cursos_manual.json y aplica las normalizaciones
directamente a la colección de opiniones en MongoDB.

Uso:
    python scripts/aplicar_mapeo_cursos.py [--dry-run] [--show-current]
    
    --dry-run      : Muestra qué cambios se harían sin aplicarlos
    --show-current : Muestra los cursos actuales en MongoDB para referencia
"""

import asyncio
import json
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import get_mongo_db


class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    GRAY = '\033[0;90m'
    NC = '\033[0m'


def cargar_mapeo_manual() -> dict:
    """Carga el mapeo manual desde el archivo JSON."""
    # Primero intentar el archivo completo, luego el manual
    path_completo = Path(__file__).parent.parent / "data" / "inputs" / "mapeo_cursos_completo.json"
    path_manual = Path(__file__).parent.parent / "data" / "inputs" / "mapeo_cursos_manual.json"
    
    path = path_completo if path_completo.exists() else path_manual
    
    if not path.exists():
        print(f"{Colors.RED}❌ No se encontró ningún archivo de mapeo{Colors.NC}")
        print(f"   Ejecuta primero: python scripts/analizar_cursos_mongo.py")
        sys.exit(1)
    
    print(f"{Colors.CYAN}📂 Usando: {path.name}{Colors.NC}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Filtrar solo el mapeo (ignorar campos que empiezan con _)
    mapeo = {}
    for key, value in data.get("mapeo", {}).items():
        if not key.startswith("_"):
            mapeo[key] = value
    
    return mapeo


async def mostrar_cursos_actuales():
    """Muestra todos los cursos actuales en MongoDB con su conteo."""
    db = get_mongo_db()
    
    pipeline = [
        {"$group": {"_id": "$curso_normalizado", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    print(f"\n{Colors.CYAN}{'='*80}{Colors.NC}")
    print(f"{Colors.CYAN}📊 CURSOS ACTUALES EN MONGODB{Colors.NC}")
    print(f"{Colors.CYAN}{'='*80}{Colors.NC}\n")
    
    total_cursos = 0
    total_opiniones = 0
    
    async for doc in db.opiniones.aggregate(pipeline):
        curso = doc["_id"]
        count = doc["count"]
        total_cursos += 1
        total_opiniones += count
        print(f"   {count:4} │ {curso}")
    
    print(f"\n{Colors.CYAN}{'─'*80}{Colors.NC}")
    print(f"   Total: {total_cursos} cursos distintos, {total_opiniones} opiniones")
    print()


async def aplicar_mapeo(dry_run: bool = False):
    """Aplica el mapeo manual a MongoDB."""
    mapeo = cargar_mapeo_manual()
    db = get_mongo_db()
    
    print(f"\n{Colors.BLUE}{'='*80}{Colors.NC}")
    print(f"{Colors.BLUE}🔧 APLICANDO MAPEO MANUAL DE CURSOS{Colors.NC}")
    if dry_run:
        print(f"{Colors.YELLOW}   (MODO DRY-RUN - No se aplicarán cambios){Colors.NC}")
    print(f"{Colors.BLUE}{'='*80}{Colors.NC}\n")
    
    # Estadísticas
    normalizados = 0
    ignorados = 0
    no_encontrados = 0
    total_docs_actualizados = 0
    
    # Procesar cada mapeo
    for curso_original, curso_destino in mapeo.items():
        # Contar documentos con este curso
        count = await db.opiniones.count_documents({"curso_normalizado": curso_original})
        
        if count == 0:
            no_encontrados += 1
            print(f"   {Colors.GRAY}⊘ '{curso_original}' - No encontrado en MongoDB{Colors.NC}")
            continue
        
        if curso_destino is None:
            # Ignorar este curso (no hacer nada, solo reportar)
            ignorados += 1
            print(f"   {Colors.YELLOW}⊗ '{curso_original}' ({count} docs) → IGNORAR{Colors.NC}")
            continue
        
        # Normalizar
        normalizados += 1
        print(f"   {Colors.GREEN}✓ '{curso_original}' ({count} docs) → '{curso_destino}'{Colors.NC}")
        
        if not dry_run:
            result = await db.opiniones.update_many(
                {"curso_normalizado": curso_original},
                {"$set": {"curso_normalizado": curso_destino}}
            )
            total_docs_actualizados += result.modified_count
    
    # Resumen
    print(f"\n{Colors.CYAN}{'='*80}{Colors.NC}")
    print(f"{Colors.CYAN}📊 RESUMEN{Colors.NC}")
    print(f"{Colors.CYAN}{'='*80}{Colors.NC}")
    print(f"   Cursos normalizados:  {Colors.GREEN}{normalizados}{Colors.NC}")
    print(f"   Cursos ignorados:     {Colors.YELLOW}{ignorados}{Colors.NC}")
    print(f"   Cursos no encontrados: {Colors.GRAY}{no_encontrados}{Colors.NC}")
    
    if not dry_run:
        print(f"\n   {Colors.GREEN}✅ Documentos actualizados: {total_docs_actualizados}{Colors.NC}")
    else:
        print(f"\n   {Colors.YELLOW}⚠️  MODO DRY-RUN - Ejecuta sin --dry-run para aplicar cambios{Colors.NC}")
    
    print()
    
    # Mostrar cursos únicos después de aplicar
    if not dry_run and normalizados > 0:
        cursos_finales = await db.opiniones.distinct("curso_normalizado")
        print(f"   Cursos únicos después del mapeo: {len(cursos_finales)}")
        print()


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Aplica el mapeo manual de cursos a MongoDB")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Muestra qué cambios se harían sin aplicarlos")
    parser.add_argument("--show-current", action="store_true",
                       help="Muestra los cursos actuales en MongoDB")
    
    args = parser.parse_args()
    
    if args.show_current:
        await mostrar_cursos_actuales()
        return
    
    await aplicar_mapeo(dry_run=args.dry_run)


if __name__ == "__main__":
    asyncio.run(main())
