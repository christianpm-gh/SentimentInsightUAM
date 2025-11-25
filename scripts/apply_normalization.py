"""
Script para aplicar normalización de materias a las bases de datos existentes.
Utiliza src.utils.normalization.CourseNormalizer para estandarizar nombres.
"""
import asyncio
import sys
from pathlib import Path
from sqlalchemy import select, update, func, delete
from sqlalchemy.orm import aliased

# Agregar root al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import get_db_session, get_mongo_db
from src.db.models import Curso, ReseniaMetadata
from src.utils.normalization import CourseNormalizer

async def apply_normalization():
    print("🚀 Iniciando proceso de normalización masiva...")
    normalizer = CourseNormalizer()
    
    if normalizer.get_stats()["total_oficiales"] == 0:
        print("❌ No se cargaron materias oficiales. Abortando.")
        return

    # ========================================================================
    # 1. NORMALIZACIÓN EN POSTGRESQL
    # ========================================================================
    print("\n🐘 Analizando PostgreSQL (Tabla 'cursos')...")
    
    async with get_db_session() as session:
        # Obtener todos los cursos actuales
        result = await session.execute(select(Curso))
        cursos_db = result.scalars().all()
        
        cambios_pendientes = []
        cursos_a_fusionar = {} # {nombre_oficial: [curso_obj, ...]}
        
        print(f"   Total cursos en BD: {len(cursos_db)}")
        
        for curso in cursos_db:
            nombre_original = curso.nombre
            nombre_norm, score, is_match = normalizer.normalize(nombre_original)
            
            if is_match and nombre_norm != nombre_original:
                # Agrupar para fusión
                if nombre_norm not in cursos_a_fusionar:
                    cursos_a_fusionar[nombre_norm] = []
                cursos_a_fusionar[nombre_norm].append(curso)
                
                print(f"   🔍 Match: '{nombre_original}' -> '{nombre_norm}' (Score: {score:.1f})")
            elif not is_match:
                # Si no hay match, se queda como está (o se podría marcar para revisión)
                pass
            else:
                # Ya está normalizado, pero igual lo agregamos al grupo para detectar duplicados existentes
                if nombre_norm not in cursos_a_fusionar:
                    cursos_a_fusionar[nombre_norm] = []
                cursos_a_fusionar[nombre_norm].append(curso)

        # Procesar fusiones
        print(f"\n   Procesando {len(cursos_a_fusionar)} grupos de materias para fusión/actualización...")
        
        total_actualizados = 0
        total_fusionados = 0
        
        for nombre_oficial, lista_cursos in cursos_a_fusionar.items():
            # Verificar si ya existe un curso con el nombre oficial en la lista o en la BD
            # Estrategia: 
            # 1. Buscar si alguno de la lista YA tiene el nombre oficial.
            # 2. Si no, elegir el que tenga más reseñas como "master" y renombrarlo.
            # 3. Mover reseñas de los otros al master y eliminarlos.
            
            master_curso = None
            
            # Buscar candidato master (preferencia: nombre exacto, luego mayor cantidad de reseñas)
            exact_matches = [c for c in lista_cursos if c.nombre == nombre_oficial]
            
            if exact_matches:
                master_curso = exact_matches[0] # Tomar el primero que ya coincida
            else:
                # Si ninguno coincide exacto, buscar si existe en BD fuera de esta lista (caso raro pero posible)
                # Por simplicidad, tomamos el de la lista con más reseñas (o ID más bajo)
                # Necesitamos saber cuántas reseñas tiene cada uno.
                # Haremos una query rápida o asumiremos el campo total_resenias si está actualizado.
                # Asumiremos que total_resenias puede no estar al día, mejor no confiar ciegamente.
                master_curso = lista_cursos[0] # Default al primero
            
            # Renombrar master si es necesario
            if master_curso.nombre != nombre_oficial:
                master_curso.nombre = nombre_oficial
                # También actualizar nombre_normalizado (slug interno de BD)
                # master_curso.nombre_normalizado = ... (esto lo maneja el modelo o repository usualmente, aquí lo forzamos)
                # Asumimos que nombre_normalizado es una versión simple para búsquedas
                import unicodedata
                norm = unicodedata.normalize('NFKD', nombre_oficial).encode('ASCII', 'ignore').decode('utf-8').lower()
                master_curso.nombre_normalizado = norm
                session.add(master_curso)
                total_actualizados += 1
            
            # Fusionar los demás
            otros_cursos = [c for c in lista_cursos if c.id != master_curso.id]
            
            if otros_cursos:
                ids_a_eliminar = [c.id for c in otros_cursos]
                print(f"      Fusionando {len(ids_a_eliminar)} cursos en '{nombre_oficial}' (ID Master: {master_curso.id})")
                
                # Reasignar reseñas
                await session.execute(
                    update(ReseniaMetadata)
                    .where(ReseniaMetadata.curso_id.in_(ids_a_eliminar))
                    .values(curso_id=master_curso.id)
                )
                
                # Eliminar cursos obsoletos
                await session.execute(
                    delete(Curso)
                    .where(Curso.id.in_(ids_a_eliminar))
                )
                total_fusionados += len(ids_a_eliminar)
        
        await session.commit()
        print(f"   ✅ PostgreSQL finalizado: {total_actualizados} nombres corregidos, {total_fusionados} duplicados eliminados.")

    # ========================================================================
    # 2. NORMALIZACIÓN EN MONGODB
    # ========================================================================
    print("\n🍃 Analizando MongoDB (Colección 'opiniones')...")
    mongo_db = get_mongo_db()
    collection = mongo_db["opiniones"]
    
    # Obtener cursos únicos
    cursos_mongo = await collection.distinct("curso")
    print(f"   Total nombres de curso únicos en Mongo: {len(cursos_mongo)}")
    
    mongo_updates = 0
    
    for nombre_original in cursos_mongo:
        if not nombre_original:
            continue
            
        nombre_norm, score, is_match = normalizer.normalize(nombre_original)
        
        if is_match and nombre_norm != nombre_original:
            # Actualizar todos los documentos con este nombre
            result = await collection.update_many(
                {"curso": nombre_original},
                {"$set": {"curso": nombre_norm}}
            )
            if result.modified_count > 0:
                print(f"   🔍 Mongo Match: '{nombre_original}' -> '{nombre_norm}' ({result.modified_count} docs)")
                mongo_updates += result.modified_count
                
    print(f"   ✅ MongoDB finalizado: {mongo_updates} documentos actualizados.")

if __name__ == "__main__":
    asyncio.run(apply_normalization())
