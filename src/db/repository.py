"""
Repositorio de persistencia para SentimentInsightUAM

Contiene funciones para guardar datos del scraping en PostgreSQL y MongoDB.
"""
import json
import traceback
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, Optional
from slugify import slugify

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import get_db_session, get_mongo_db
from .models import (
    Profesor, Perfil, Etiqueta, PerfilEtiqueta, Curso,
    ReseniaMetadata, ReseniaEtiqueta, HistorialScraping
)


# ============================================================================
# MAPEO DE CURSOS UNIFICADO
# ============================================================================
# Cargar mapeo de cursos para normalización automática al insertar

_CURSOS_MAPPING: Dict[str, Dict[str, Any]] = {}
_CURSOS_MAPPING_LOADED = False


def _cargar_mapeo_cursos():
    """
    Carga el mapeo de cursos desde cursos_unificado.json.
    Solo se carga una vez (singleton).
    """
    global _CURSOS_MAPPING, _CURSOS_MAPPING_LOADED
    
    if _CURSOS_MAPPING_LOADED:
        return
    
    mapping_path = Path(__file__).parent.parent.parent / 'data' / 'inputs' / 'cursos_unificado.json'
    
    if mapping_path.exists():
        try:
            with open(mapping_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            _CURSOS_MAPPING = data.get('mapping', {})
            print(f"  📚 Mapeo de cursos cargado: {len(_CURSOS_MAPPING)} entradas")
        except Exception as e:
            print(f"  ⚠️ Error cargando mapeo de cursos: {e}")
            _CURSOS_MAPPING = {}
    else:
        print(f"  ⚠️ Archivo de mapeo no encontrado: {mapping_path}")
        _CURSOS_MAPPING = {}
    
    _CURSOS_MAPPING_LOADED = True


def obtener_curso_normalizado(nombre_curso: str) -> str:
    """
    Obtiene el nombre normalizado de un curso usando el mapeo unificado.
    
    Args:
        nombre_curso: Nombre original del curso
        
    Returns:
        str: Nombre normalizado o el original si no está en el mapeo
    """
    _cargar_mapeo_cursos()
    
    if not nombre_curso:
        return nombre_curso
    
    # Buscar en el mapeo (case-sensitive primero)
    if nombre_curso in _CURSOS_MAPPING:
        return _CURSOS_MAPPING[nombre_curso].get('normalizado_a', nombre_curso)
    
    # Buscar case-insensitive
    nombre_lower = nombre_curso.lower()
    for key, value in _CURSOS_MAPPING.items():
        if key.lower() == nombre_lower:
            return value.get('normalizado_a', nombre_curso)
    
    # No encontrado, retornar original
    return nombre_curso


# ============================================================================
# COMENTARIOS INVÁLIDOS
# ============================================================================
# Patrones de comentarios que no deben guardarse en MongoDB
# Son placeholders o contenido bloqueado de MisProfesores.com
COMENTARIOS_INVALIDOS = frozenset([
    '[Comentario esperando revisión]',
    '[Comentario bloqueado]',
])


def es_comentario_valido(comentario: str) -> bool:
    """
    Verifica si un comentario es válido para análisis de sentimiento.
    
    Retorna False si el comentario es un placeholder o está bloqueado.
    
    Args:
        comentario: Texto del comentario
        
    Returns:
        bool: True si es válido, False si debe ignorarse
    """
    if not comentario or not comentario.strip():
        return False
    
    return comentario not in COMENTARIOS_INVALIDOS


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
    
    Usa el mapeo unificado de cursos_unificado.json para normalizar.
    
    Args:
        session: Sesión de SQLAlchemy
        nombre: Nombre del curso
        
    Returns:
        Curso o None si el nombre es inválido
    """
    # Validar nombre (rechazar valores inválidos comunes)
    if not nombre or nombre.strip() in ['', '-', '--', '---', '-----', '...', '0', 'N/A', 'N.A.', 'n/a']:
        return None
    
    nombre_limpio = nombre.strip()
    
    # Obtener nombre normalizado usando el mapeo unificado
    nombre_normalizado = obtener_curso_normalizado(nombre_limpio)
    nombre_norm_bd = normalizar_texto(nombre_normalizado)
    
    # Buscar curso existente por nombre normalizado
    result = await session.execute(
        select(Curso).where(Curso.nombre_normalizado == nombre_norm_bd)
    )
    curso = result.scalar_one_or_none()
    
    if curso is None:
        # Crear nuevo curso con el nombre normalizado
        curso = Curso(
            nombre=nombre_normalizado,  # Usar nombre normalizado, no el original
            nombre_normalizado=nombre_norm_bd,
            departamento='Sistemas'
        )
        session.add(curso)
        await session.flush()
        print(f"    📗 Nuevo curso creado: '{nombre_limpio}' → '{nombre_normalizado}'")
    
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
            resenias_duplicadas = 0
            opiniones_insertadas = 0
            
            for review in reviews:
                # a) Obtener o crear curso
                curso = None
                curso_nombre_original = review.get('course', '')
                curso_nombre_normalizado = obtener_curso_normalizado(curso_nombre_original) if curso_nombre_original else None
                
                if curso_nombre_original:
                    curso = await obtener_o_crear_curso(session, curso_nombre_original)
                
                # b) Convertir fecha string a date object
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
                tiene_comentario_valido = es_comentario_valido(comentario)
                
                # c) Verificar si la reseña ya existe (evitar duplicados)
                # Criterio: mismo profesor + fecha + curso + calificación
                query_duplicado = select(ReseniaMetadata).where(
                    ReseniaMetadata.profesor_id == profesor.id,
                    ReseniaMetadata.fecha_resenia == fecha_resenia,
                    ReseniaMetadata.calidad_general == review.get('overall')
                )
                if curso:
                    query_duplicado = query_duplicado.where(ReseniaMetadata.curso_id == curso.id)
                
                result_dup = await session.execute(query_duplicado)
                resenia_existente = result_dup.scalar_one_or_none()
                
                if resenia_existente:
                    resenias_duplicadas += 1
                    continue  # Saltar reseña duplicada
                
                # d) Crear reseña en PostgreSQL
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
                    tiene_comentario=tiene_comentario_valido,
                    longitud_comentario=len(comentario) if tiene_comentario_valido else 0,
                    fuente='misprofesores.com'
                )
                session.add(resenia)
                await session.flush()  # Necesario para obtener resenia.id
                
                # e) Procesar etiquetas de la reseña
                for tag_name in review.get('tags', []):
                    etiqueta = await obtener_o_crear_etiqueta(session, tag_name)
                    
                    resenia_etiqueta = ReseniaEtiqueta(
                        resenia_id=resenia.id,
                        etiqueta_id=etiqueta.id
                    )
                    session.add(resenia_etiqueta)
                
                # f) Insertar opinión en MongoDB (solo si hay comentario válido)
                if tiene_comentario_valido:
                    # Verificar duplicado en MongoDB también
                    opinion_existente = await mongo_db.opiniones.find_one({
                        'profesor_id': profesor.id,
                        'comentario': comentario
                    })
                    
                    if opinion_existente:
                        # Ya existe, solo vincular
                        resenia.mongo_opinion_id = str(opinion_existente['_id'])
                    else:
                        # Crear nueva opinión con curso normalizado
                        opinion_doc = {
                            'profesor_id': profesor.id,
                            'profesor_nombre': nombre_limpio,
                            'profesor_slug': slug,
                            'resenia_id': resenia.id,
                            'fecha_opinion': datetime.combine(fecha_resenia, datetime.min.time()),
                            'curso': curso_nombre_original,  # Curso original del scraping
                            'curso_normalizado': curso_nombre_normalizado,  # Curso normalizado
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
                        
                        # Vincular MongoDB con PostgreSQL
                        resenia.mongo_opinion_id = str(mongo_result.inserted_id)
                        opiniones_insertadas += 1
                
                resenias_insertadas += 1
            
            print(f"  → {resenias_insertadas} reseñas insertadas en PostgreSQL")
            if resenias_duplicadas > 0:
                print(f"  → {resenias_duplicadas} reseñas duplicadas omitidas")
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
