#!/usr/bin/env python3
"""
Script para asociar reseñas existentes con sus cursos correspondientes.

Este script:
1. Lee las reseñas de PostgreSQL que no tienen curso_id asignado
2. Busca el curso_normalizado en MongoDB
3. Encuentra el curso correspondiente en PostgreSQL
4. Actualiza el curso_id en resenias_metadata

Uso:
    python scripts/asociar_cursos_resenias.py [--dry-run]

Opciones:
    --dry-run : Muestra los cambios sin aplicarlos
"""

import asyncio
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, select, update
from src.db import get_db_session, get_mongo_db
from src.db.models import Curso, ReseniaMetadata


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


async def asociar_cursos(dry_run: bool = False):
    """Asocia reseñas con sus cursos correspondientes."""
    print("=" * 70)
    print(f"{Colors.BLUE}{Colors.BOLD}🔗 ASOCIACIÓN DE CURSOS A RESEÑAS{Colors.NC}")
    if dry_run:
        print(f"{Colors.YELLOW}   (MODO DRY-RUN - No se aplicarán cambios){Colors.NC}")
    print("=" * 70)
    print()
    
    mongo_db = get_mongo_db()
    
    async with get_db_session() as session:
        try:
            # 1. Obtener reseñas sin curso_id
            print(f"{Colors.CYAN}📊 Analizando reseñas sin curso asignado...{Colors.NC}")
            result = await session.execute(
                text("SELECT COUNT(*) FROM resenias_metadata WHERE curso_id IS NULL")
            )
            sin_curso = result.scalar()
            
            result = await session.execute(
                text("SELECT COUNT(*) FROM resenias_metadata WHERE curso_id IS NOT NULL")
            )
            con_curso = result.scalar()
            
            result = await session.execute(
                text("SELECT COUNT(*) FROM resenias_metadata")
            )
            total = result.scalar()
            
            print(f"   → Total de reseñas: {total}")
            print(f"   → Con curso asignado: {con_curso}")
            print(f"   → Sin curso asignado: {sin_curso}")
            print()
            
            if sin_curso == 0:
                print(f"{Colors.GREEN}✅ Todas las reseñas ya tienen curso asignado{Colors.NC}")
                return
            
            # 2. Obtener mapeo de cursos PostgreSQL (nombre_normalizado -> id)
            print(f"{Colors.CYAN}📋 Cargando catálogo de cursos...{Colors.NC}")
            result = await session.execute(select(Curso))
            cursos_pg = {c.nombre_normalizado: c.id for c in result.scalars().all()}
            print(f"   → {len(cursos_pg)} cursos en catálogo")
            print()
            
            # 3. Obtener reseñas sin curso_id con su mongo_opinion_id
            print(f"{Colors.CYAN}🔍 Procesando reseñas sin curso...{Colors.NC}")
            result = await session.execute(
                select(ReseniaMetadata.id, ReseniaMetadata.mongo_opinion_id)
                .where(ReseniaMetadata.curso_id.is_(None))
                .where(ReseniaMetadata.mongo_opinion_id.isnot(None))
            )
            resenias_sin_curso = result.all()
            
            print(f"   → {len(resenias_sin_curso)} reseñas a procesar")
            print()
            
            # 4. Buscar curso_normalizado en MongoDB y asociar
            actualizadas = 0
            sin_coincidencia = 0
            errores = 0
            cursos_no_encontrados = {}  # Para logging de cursos sin match
            
            from bson import ObjectId
            
            print(f"{Colors.BLUE}🔄 Asociando cursos...{Colors.NC}")
            
            updates_to_apply = []
            
            for i, (resenia_id, mongo_id) in enumerate(resenias_sin_curso):
                try:
                    # Buscar en MongoDB
                    opinion = await mongo_db.opiniones.find_one({"_id": ObjectId(mongo_id)})
                    
                    if not opinion:
                        errores += 1
                        continue
                    
                    curso_normalizado = opinion.get("curso_normalizado")
                    if not curso_normalizado:
                        sin_coincidencia += 1
                        continue
                    
                    # Normalizar el nombre del curso para buscar en PostgreSQL
                    # (MongoDB tiene acentos, PostgreSQL tiene lowercase sin acentos)
                    curso_norm_busqueda = normalizar_texto(curso_normalizado)
                    
                    # Buscar en catálogo de cursos
                    curso_id = cursos_pg.get(curso_norm_busqueda)
                    
                    if curso_id:
                        updates_to_apply.append({"resenia_id": resenia_id, "curso_id": curso_id})
                        actualizadas += 1
                    else:
                        sin_coincidencia += 1
                        # Registrar cursos no encontrados para debug
                        cursos_no_encontrados[curso_normalizado] = cursos_no_encontrados.get(curso_normalizado, 0) + 1
                    
                    # Mostrar progreso cada 500
                    if (i + 1) % 500 == 0:
                        print(f"   → Procesadas {i + 1}/{len(resenias_sin_curso)} reseñas...")
                        
                except Exception as e:
                    errores += 1
                    continue
            
            # Mostrar cursos no encontrados (para debug)
            if cursos_no_encontrados:
                print()
                print(f"{Colors.YELLOW}⚠️  Cursos sin coincidencia en catálogo:{Colors.NC}")
                for curso, count in sorted(cursos_no_encontrados.items(), key=lambda x: -x[1])[:10]:
                    print(f"      {count:4} │ {curso}")
            
            print()
            print(f"{Colors.CYAN}📊 Resumen del procesamiento:{Colors.NC}")
            print(f"   → Reseñas a actualizar: {actualizadas}")
            print(f"   → Sin coincidencia de curso: {sin_coincidencia}")
            print(f"   → Errores: {errores}")
            print()
            
            if dry_run:
                print(f"{Colors.YELLOW}⚠️  MODO DRY-RUN: No se realizaron cambios{Colors.NC}")
                print(f"   Se actualizarían {actualizadas} reseñas")
                return
            
            # 5. Aplicar actualizaciones
            if updates_to_apply:
                print(f"{Colors.BLUE}💾 Aplicando actualizaciones...{Colors.NC}")
                
                for upd in updates_to_apply:
                    await session.execute(
                        update(ReseniaMetadata)
                        .where(ReseniaMetadata.id == upd["resenia_id"])
                        .values(curso_id=upd["curso_id"])
                    )
                
                await session.commit()
                print(f"   → {len(updates_to_apply)} reseñas actualizadas")
            
            # 6. Verificar resultado final
            result = await session.execute(
                text("SELECT COUNT(*) FROM resenias_metadata WHERE curso_id IS NOT NULL")
            )
            con_curso_final = result.scalar()
            
            print()
            print("=" * 70)
            print(f"{Colors.GREEN}✅ ASOCIACIÓN COMPLETADA{Colors.NC}")
            print("=" * 70)
            print(f"   Reseñas con curso antes: {con_curso}")
            print(f"   Reseñas con curso ahora: {con_curso_final}")
            print(f"   Nuevas asociaciones: {con_curso_final - con_curso}")
            
        except Exception as e:
            await session.rollback()
            print(f"{Colors.RED}❌ Error: {e}{Colors.NC}")
            import traceback
            traceback.print_exc()
            raise


async def main():
    dry_run = "--dry-run" in sys.argv
    await asociar_cursos(dry_run=dry_run)


if __name__ == "__main__":
    asyncio.run(main())
