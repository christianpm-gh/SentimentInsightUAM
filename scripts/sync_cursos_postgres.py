#!/usr/bin/env python3
"""
Script para sincronizar cursos normalizados de MongoDB a PostgreSQL.

Este script:
1. Limpia la tabla 'cursos' de PostgreSQL (mantiene estructura)
2. Extrae cursos únicos normalizados de MongoDB
3. Inserta los cursos en PostgreSQL

Uso:
    python scripts/sync_cursos_postgres.py [--dry-run]

Opciones:
    --dry-run : Muestra los cambios sin aplicarlos
"""

import asyncio
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, delete
from src.db import get_db_session, get_mongo_db
from src.db.models import Curso


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    NC = "\033[0m"


def normalizar_texto(texto: str) -> str:
    """Normaliza texto para búsqueda (lowercase, sin acentos)."""
    import unicodedata
    texto = texto.strip().lower()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto


async def obtener_cursos_mongo() -> list[dict]:
    """Obtiene cursos únicos de MongoDB con conteo de opiniones."""
    mongo_db = get_mongo_db()
    
    pipeline = [
        {"$group": {
            "_id": "$curso_normalizado",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]
    
    cursos = []
    async for doc in mongo_db.opiniones.aggregate(pipeline):
        nombre = doc["_id"]
        if nombre:  # Ignorar None/null
            cursos.append({
                "nombre": nombre,
                "total_resenias": doc["count"]
            })
    
    return cursos


async def sync_cursos(dry_run: bool = False):
    """Sincroniza cursos de MongoDB a PostgreSQL."""
    print("=" * 70)
    print(f"{Colors.BLUE}{Colors.BOLD}🔄 SINCRONIZACIÓN DE CURSOS: MongoDB → PostgreSQL{Colors.NC}")
    if dry_run:
        print(f"{Colors.YELLOW}   (MODO DRY-RUN - No se aplicarán cambios){Colors.NC}")
    print("=" * 70)
    print()
    
    # 1. Obtener cursos de MongoDB
    print(f"{Colors.CYAN}📊 Obteniendo cursos de MongoDB...{Colors.NC}")
    cursos_mongo = await obtener_cursos_mongo()
    total_opiniones = sum(c["total_resenias"] for c in cursos_mongo)
    print(f"   → {len(cursos_mongo)} cursos únicos encontrados")
    print(f"   → {total_opiniones} opiniones totales")
    print()
    
    # 2. Mostrar cursos a insertar
    print(f"{Colors.CYAN}📋 Cursos a insertar en PostgreSQL:{Colors.NC}")
    print("-" * 70)
    for curso in cursos_mongo[:20]:  # Mostrar top 20
        print(f"   {curso['total_resenias']:4} │ {curso['nombre']}")
    if len(cursos_mongo) > 20:
        print(f"   ... y {len(cursos_mongo) - 20} más")
    print("-" * 70)
    print()
    
    if dry_run:
        print(f"{Colors.YELLOW}⚠️  MODO DRY-RUN: No se realizaron cambios{Colors.NC}")
        return
    
    # 3. Limpiar tabla cursos y sincronizar
    async with get_db_session() as session:
        try:
            # Primero verificar si hay reseñas con curso_id
            result = await session.execute(
                text("SELECT COUNT(*) FROM resenias_metadata WHERE curso_id IS NOT NULL")
            )
            resenias_con_curso = result.scalar()
            
            if resenias_con_curso > 0:
                print(f"{Colors.YELLOW}⚠️  Hay {resenias_con_curso} reseñas con curso_id asignado{Colors.NC}")
                print(f"   → Poniendo curso_id en NULL antes de limpiar...")
                await session.execute(
                    text("UPDATE resenias_metadata SET curso_id = NULL WHERE curso_id IS NOT NULL")
                )
            
            # Limpiar tabla cursos
            print(f"{Colors.BLUE}🗑️  Limpiando tabla 'cursos'...{Colors.NC}")
            result = await session.execute(delete(Curso))
            print(f"   → {result.rowcount} registros eliminados")
            
            # Reiniciar secuencia
            await session.execute(text("ALTER SEQUENCE cursos_id_seq RESTART WITH 1"))
            print(f"   → Secuencia reiniciada a 1")
            
            # Insertar nuevos cursos
            print(f"{Colors.BLUE}📥 Insertando cursos normalizados...{Colors.NC}")
            insertados = 0
            
            for curso_data in cursos_mongo:
                nombre = curso_data["nombre"]
                nombre_normalizado = normalizar_texto(nombre)
                
                curso = Curso(
                    nombre=nombre,
                    nombre_normalizado=nombre_normalizado,
                    departamento='Sistemas',
                    total_resenias=curso_data["total_resenias"]
                )
                session.add(curso)
                insertados += 1
            
            await session.commit()
            print(f"   → {insertados} cursos insertados")
            
            # Verificar resultado
            result = await session.execute(text("SELECT COUNT(*) FROM cursos"))
            total_final = result.scalar()
            
            print()
            print("=" * 70)
            print(f"{Colors.GREEN}✅ SINCRONIZACIÓN COMPLETADA{Colors.NC}")
            print("=" * 70)
            print(f"   Cursos en PostgreSQL: {total_final}")
            print(f"   Cursos en MongoDB: {len(cursos_mongo)}")
            
        except Exception as e:
            await session.rollback()
            print(f"{Colors.RED}❌ Error: {e}{Colors.NC}")
            raise


async def main():
    dry_run = "--dry-run" in sys.argv
    await sync_cursos(dry_run=dry_run)


if __name__ == "__main__":
    asyncio.run(main())
