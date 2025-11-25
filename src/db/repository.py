"""
Repositorio de persistencia para SentimentInsightUAM

Contiene funciones para guardar datos del scraping en PostgreSQL y MongoDB.
"""
import traceback
from datetime import datetime, date
from typing import Dict, Any, Optional
from slugify import slugify

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import get_db_session, get_mongo_db
from .models import (
    Profesor, Perfil, Etiqueta, PerfilEtiqueta, Curso,
    ReseniaMetadata, ReseniaEtiqueta, HistorialScraping
)


def limpiar_nombre_profesor(nombre_completo: str) -> str:
    """
    Limpia el nombre del profesor removiendo sufijos institucionales.
    
    Args:
        nombre_completo: Nombre con formato "Nombre - UAM (Azcapotzalco) - ..."
        
    Returns:
        str: Nombre limpio
        
    Ejemplo:
        >>> limpiar_nombre_profesor("Juan Pérez - UAM (Azcapotzalco) - MisProfesores.com")
        "Juan Pérez"
    """
    # Remover " - UAM (Azcapotzalco)" y todo lo que sigue
    if " - UAM" in nombre_completo:
        return nombre_completo.split(" - UAM")[0].strip()
    
    # Remover " - Universidad" y todo lo que sigue
    if " - Universidad" in nombre_completo:
        return nombre_completo.split(" - Universidad")[0].strip()
    
    # Remover " - MisProfesores" y todo lo que sigue
    if " - MisProfesores" in nombre_completo:
        return nombre_completo.split(" - MisProfesores")[0].strip()
    
    return nombre_completo.strip()


def normalizar_texto(texto: str) -> str:
    """
    Normaliza texto para búsqueda (lowercase, sin acentos).
    
    Args:
        texto: Texto a normalizar
        
    Returns:
        str: Texto normalizado
    """
    import unicodedata
    
    # Remover acentos
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    
    # Lowercase y trim
    return texto.lower().strip()


async def obtener_o_crear_etiqueta(session: AsyncSession, nombre: str) -> Etiqueta:
    """
    Obtiene una etiqueta existente o la crea si no existe.
    
    Args:
        session: Sesión de SQLAlchemy
        nombre: Nombre de la etiqueta
        
    Returns:
        Etiqueta: Instancia de la etiqueta
    """
    nombre_norm = normalizar_texto(nombre)
    
    # Buscar etiqueta existente
    result = await session.execute(
        select(Etiqueta).where(Etiqueta.etiqueta_normalizada == nombre_norm)
    )
    etiqueta = result.scalar_one_or_none()
    
    if etiqueta is None:
        # Crear nueva etiqueta
        etiqueta = Etiqueta(
            etiqueta=nombre.upper(),
            etiqueta_normalizada=nombre_norm,
            categoria=None  # Se puede categorizar manualmente después
        )
        session.add(etiqueta)
        await session.flush()
    
    return etiqueta


async def obtener_o_crear_curso(session: AsyncSession, nombre: str) -> Optional[Curso]:
    """
    Obtiene un curso existente o lo crea si no existe.
    
    Usa el diccionario de normalización para unificar variantes de materias.
    Por ejemplo: "POO", "poo", "prog orientada a obj" → "Programación Orientada a Objetos"
    
    Args:
        session: Sesión de SQLAlchemy
        nombre: Nombre del curso (puede ser variante)
        
    Returns:
        Curso o None si el nombre es inválido
        
    Ejemplo:
        >>> await obtener_o_crear_curso(session, "POO")
        <Curso(nombre='Programación Orientada a Objetos')>
        >>> await obtener_o_crear_curso(session, "---")
        None
    """
    # Validar nombre (rechazar valores inválidos comunes)
    if not nombre or nombre.strip() in ['', '---', 'N/A', 'N.A.', 'n/a']:
        return None
    
    # Normalizar usando el nuevo normalizador fuzzy
    from src.utils.normalization import CourseNormalizer
    normalizer = CourseNormalizer()
    
    nombre_oficial, score, is_match = normalizer.normalize(nombre)
    
    # Si no hay match, usamos el nombre original limpio
    # (Opcional: podríamos rechazarlo si queremos ser estrictos)
    nombre_final = nombre_oficial if is_match else nombre.strip()
    
    # Normalizar para búsqueda en BD (lowercase sin acentos)
    nombre_norm_bd = normalizar_texto(nombre_final)
    
    # Buscar curso existente por nombre normalizado
    result = await session.execute(
        select(Curso).where(Curso.nombre_normalizado == nombre_norm_bd)
    )
    curso = result.scalar_one_or_none()
    
    if curso is None:
        # Crear nuevo curso con nombre oficial
        curso = Curso(
            nombre=nombre_final,  # Nombre oficial normalizado
            nombre_normalizado=nombre_norm_bd,
            departamento='Sistemas'
        )
        session.add(curso)
        await session.flush()
    
    return curso


async def guardar_profesor_completo(data: Dict[str, Any], url_misprofesores: Optional[str] = None) -> int:
    """
    Guarda un profesor completo en PostgreSQL y MongoDB.
    
    Este es el punto de entrada principal para la persistencia desde el scraper.
    Maneja toda la lógica de inserción en ambas bases de datos y mantiene
    la sincronización mediante el campo mongo_opinion_id.
    
    Args:
        data: JSON del scraping con la estructura completa del profesor
        url_misprofesores: URL del perfil en MisProfesores (opcional)
        
    Returns:
        int: ID del profesor en PostgreSQL
        
    Ejemplo de data esperado:
        {
            "name": "Juan Pérez - UAM (Azcapotzalco) - MisProfesores.com",
            "overall_quality": 9.5,
            "difficulty": 7.2,
            "recommend_percent": 95.0,
            "tags": [
                {"label": "EXCELENTE CLASE", "count": 25}
            ],
            "reviews": [
                {
                    "date": "2024-01-15",
                    "course": "Estructura de Datos",
                    "overall": 10.0,
                    "ease": 8.0,
                    "attendance": "Obligatoria",
                    "grade_received": "10",
                    "interest": "Alta",
                    "tags": ["BUENA ONDA"],
                    "comment": "Excelente..."
                }
            ],
            "cached": False
        }
    """
    mongo_db = get_mongo_db()
    inicio = datetime.now()
    
    async with get_db_session() as session:
        try:
            # 1. Limpiar nombre y crear slug
            nombre_completo = data['name']
            nombre_limpio = limpiar_nombre_profesor(nombre_completo)
            slug = slugify(nombre_limpio)
            
            # 2. Obtener o crear profesor
            result = await session.execute(
                select(Profesor).where(Profesor.slug == slug)
            )
            profesor = result.scalar_one_or_none()
            
            if profesor is None:
                # Crear nuevo profesor
                profesor = Profesor(
                    nombre_completo=nombre_completo,
                    nombre_limpio=nombre_limpio,
                    slug=slug,
                    url_misprofesores=url_misprofesores,
                    departamento='Sistemas',
                    activo=True
                )
                session.add(profesor)
                await session.flush()
                print(f"  → Profesor '{nombre_limpio}' creado (ID={profesor.id})")
            else:
                # Actualizar URL si se proporcionó
                if url_misprofesores and not profesor.url_misprofesores:
                    profesor.url_misprofesores = url_misprofesores
                print(f"  → Profesor '{nombre_limpio}' ya existe (ID={profesor.id})")
            
            # 3. Crear perfil (snapshot del día)
            perfil = Perfil(
                profesor_id=profesor.id,
                calidad_general=data.get('overall_quality'),
                dificultad=data.get('difficulty'),
                porcentaje_recomendacion=data.get('recommend_percent'),
                total_resenias_encontradas=len(data.get('reviews', [])),
                scraping_exitoso=True,
                fuente='misprofesores.com'
            )
            session.add(perfil)
            await session.flush()
            print(f"  → Perfil creado (ID={perfil.id}, calidad={perfil.calidad_general})")
            
            # 4. Procesar etiquetas del perfil
            tags_count = 0
            for tag_data in data.get('tags', []):
                etiqueta = await obtener_o_crear_etiqueta(session, tag_data['label'])
                
                perfil_etiqueta = PerfilEtiqueta(
                    perfil_id=perfil.id,
                    etiqueta_id=etiqueta.id,
                    contador=tag_data.get('count', 0)
                )
                session.add(perfil_etiqueta)
                tags_count += 1
            
            if tags_count > 0:
                await session.flush()
                print(f"  → {tags_count} etiquetas del perfil asociadas")
            
            # 5. Procesar reseñas
            reviews = data.get('reviews', [])
            resenias_insertadas = 0
            opiniones_insertadas = 0
            
            for review in reviews:
                # a) Obtener o crear curso
                curso = None
                if review.get('course'):
                    curso = await obtener_o_crear_curso(session, review['course'])
                
                # b) Crear reseña en PostgreSQL
                # Convertir fecha string a date object
                fecha_resenia_str = review.get('date')
                if fecha_resenia_str:
                    if isinstance(fecha_resenia_str, str):
                        fecha_resenia = datetime.fromisoformat(fecha_resenia_str).date()
                    elif isinstance(fecha_resenia_str, date):
                        fecha_resenia = fecha_resenia_str
                    else:
                        fecha_resenia = datetime.now().date()
                else:
                    fecha_resenia = datetime.now().date()
                
                comentario = review.get('comment', '')
                
                resenia = ReseniaMetadata(
                    profesor_id=profesor.id,
                    curso_id=curso.id if curso else None,
                    perfil_id=perfil.id,
                    fecha_resenia=fecha_resenia,
                    calidad_general=review.get('overall'),
                    facilidad=review.get('ease'),
                    asistencia=review.get('attendance'),
                    calificacion_recibida=review.get('grade_received'),
                    nivel_interes=review.get('interest'),
                    tiene_comentario=bool(comentario),
                    longitud_comentario=len(comentario) if comentario else 0,
                    fuente='misprofesores.com'
                )
                session.add(resenia)
                await session.flush()  # Necesario para obtener resenia.id
                
                # c) Procesar etiquetas de la reseña
                for tag_name in review.get('tags', []):
                    etiqueta = await obtener_o_crear_etiqueta(session, tag_name)
                    
                    resenia_etiqueta = ReseniaEtiqueta(
                        resenia_id=resenia.id,
                        etiqueta_id=etiqueta.id
                    )
                    session.add(resenia_etiqueta)
                
                # d) Insertar opinión en MongoDB (solo si hay comentario)
                if comentario:
                    # Normalizar curso para MongoDB también
                    curso_mongo = review.get('course') or ''
                    if curso_mongo:
                        from src.utils.normalization import CourseNormalizer
                        norm_mongo = CourseNormalizer()
                        curso_norm, _, is_match = norm_mongo.normalize(curso_mongo)
                        if is_match:
                            curso_mongo = curso_norm

                    opinion_doc = {
                        'profesor_id': profesor.id,
                        'profesor_nombre': nombre_limpio,
                        'profesor_slug': slug,
                        'resenia_id': resenia.id,
                        'fecha_opinion': datetime.combine(fecha_resenia, datetime.min.time()),
                        'curso': curso_mongo,
                        'comentario': comentario,
                        'idioma': 'es',
                        'longitud_caracteres': len(comentario),
                        'longitud_palabras': len(comentario.split()),
                        'sentimiento_general': {
                            'analizado': False,
                            'clasificacion': None,
                            'pesos': None,
                            'confianza': None
                        },
                        'categorizacion': {
                            'analizado': False
                        },
                        'fecha_extraccion': datetime.now(),
                        'fuente': 'misprofesores.com',
                        'version_scraper': '1.2.0'
                    }
                    
                    mongo_result = await mongo_db.opiniones.insert_one(opinion_doc)
                    
                    # e) Vincular MongoDB con PostgreSQL
                    resenia.mongo_opinion_id = str(mongo_result.inserted_id)
                    opiniones_insertadas += 1
                
                resenias_insertadas += 1
            
            print(f"  → {resenias_insertadas} reseñas insertadas en PostgreSQL")
            print(f"  → {opiniones_insertadas} opiniones insertadas en MongoDB")
            
            # 6. Registrar en historial de scraping
            duracion = int((datetime.now() - inicio).total_seconds())
            
            historial = HistorialScraping(
                profesor_id=profesor.id,
                estado='exito',
                resenias_encontradas=len(reviews),
                resenias_nuevas=resenias_insertadas,
                resenias_actualizadas=0,
                duracion_segundos=duracion,
                url_procesada=url_misprofesores,
                cache_utilizado=data.get('cached', False),
                razon_rescraping='integracion_base_datos' if not data.get('cached') else 'cache_usado',
                user_agent='SentimentInsightUAM/1.2.0'
            )
            session.add(historial)
            
            # 7. Commit final
            await session.commit()
            
            print(f"✅ Persistencia exitosa: {nombre_limpio} (ID={profesor.id})")
            print(f"   Duración: {duracion}s")
            
            return profesor.id
            
        except Exception as e:
            await session.rollback()
            
            # Registrar error en historial
            try:
                historial_error = HistorialScraping(
                    estado='error',
                    mensaje_error=str(e),
                    stack_trace=traceback.format_exc(),
                    timestamp=datetime.now()
                )
                session.add(historial_error)
                await session.commit()
            except:
                pass  # Si falla el registro de error, continuar
            
            print(f"❌ Error en persistencia: {e}")
            raise


# ============================================================================
# FUNCIONES DE CONSULTA
# ============================================================================

async def obtener_profesor_por_slug(slug: str) -> Optional[Profesor]:
    """
    Obtiene un profesor por su slug.
    
    Args:
        slug: Slug del profesor
        
    Returns:
        Profesor o None si no existe
    """
    async with get_db_session() as session:
        result = await session.execute(
            select(Profesor).where(Profesor.slug == slug)
        )
        return result.scalar_one_or_none()


async def obtener_ultimos_profesores(limite: int = 10) -> list[Profesor]:
    """
    Obtiene los últimos profesores agregados.
    
    Args:
        limite: Número máximo de profesores a retornar
        
    Returns:
        Lista de profesores
    """
    async with get_db_session() as session:
        result = await session.execute(
            select(Profesor)
            .order_by(Profesor.created_at.desc())
            .limit(limite)
        )
        return list(result.scalars().all())
