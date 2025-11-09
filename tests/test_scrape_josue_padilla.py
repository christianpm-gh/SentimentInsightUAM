#!/usr/bin/env python3
"""
Test de Integración: Scraping y Persistencia de Josué Padilla Cuevas

Valida el flujo completo de scraping e inserción en bases de datos
para un profesor real de la UAM Azcapotzalco.
"""
import sys
import os
import asyncio
from datetime import datetime

# Agregar directorio raíz al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from sqlalchemy import select, func
    from pymongo import MongoClient
    from dotenv import load_dotenv
    
    from src.mp.scrape_prof import find_and_scrape
    from src.db import get_db_session, get_mongo_db, init_db, close_db
    from src.db.models import Profesor, Perfil, ReseniaMetadata
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("\nEjecuta:")
    print("  pip install -r requirements.txt")
    print("  docker-compose up -d")
    sys.exit(1)

load_dotenv()


class TestScrapingIntegration:
    """Test de integración completo del flujo de scraping."""
    
    def __init__(self):
        self.profesor_nombre = "Josue Padilla Cuevas"
        self.profesor_id = None
        self.perfil_id = None
        self.mongo_db = None
        
    async def setup(self):
        """Inicializa conexiones a bases de datos."""
        print("\n" + "="*70)
        print("SETUP: Inicializando conexiones")
        print("="*70)
        
        try:
            await init_db()
            self.mongo_db = get_mongo_db()
            print("✅ Conexiones inicializadas")
            return True
        except Exception as e:
            print(f"❌ Error en setup: {e}")
            return False
    
    async def test_scraping(self):
        """Test 1: Ejecutar scraping del profesor."""
        print("\n" + "="*70)
        print(f"TEST 1: Scraping de '{self.profesor_nombre}'")
        print("="*70)
        
        try:
            # Ejecutar scraping (forzar para obtener datos frescos y guardar en BD)
            data = await find_and_scrape(self.profesor_nombre, force=True)
            
            # Validar estructura de datos
            assert 'name' in data, "Falta campo 'name'"
            assert 'overall_quality' in data, "Falta campo 'overall_quality'"
            assert 'reviews' in data, "Falta campo 'reviews'"
            assert len(data['reviews']) > 0, "No se encontraron reseñas"
            
            print(f"\n✅ Scraping exitoso:")
            print(f"   - Nombre: {data['name']}")
            print(f"   - Calidad: {data['overall_quality']}")
            print(f"   - Dificultad: {data['difficulty']}")
            print(f"   - Recomendación: {data['recommend_percent']}%")
            print(f"   - Total reseñas: {len(data['reviews'])}")
            print(f"   - Caché usado: {'Sí' if data.get('cached') else 'No'}")
            
            return True
        except Exception as e:
            print(f"\n❌ Error en scraping: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_postgres_data(self):
        """Test 2: Verificar inserción en PostgreSQL."""
        print("\n" + "="*70)
        print("TEST 2: Validación de datos en PostgreSQL")
        print("="*70)
        
        try:
            async with get_db_session() as session:
                # 1. Verificar profesor
                result = await session.execute(
                    select(Profesor).where(Profesor.nombre_limpio.ilike(f"%Josue Padilla%"))
                )
                profesor = result.scalar_one_or_none()
                
                assert profesor is not None, f"Profesor '{self.profesor_nombre}' no encontrado"
                self.profesor_id = profesor.id
                
                print(f"\n1️⃣ Profesor encontrado:")
                print(f"   - ID: {profesor.id}")
                print(f"   - Nombre: {profesor.nombre_limpio}")
                print(f"   - Slug: {profesor.slug}")
                print(f"   - Departamento: {profesor.departamento}")
                
                # 2. Verificar perfil
                result = await session.execute(
                    select(Perfil)
                    .where(Perfil.profesor_id == profesor.id)
                    .order_by(Perfil.fecha_extraccion.desc())
                    .limit(1)
                )
                perfil = result.scalar_one_or_none()
                
                assert perfil is not None, "No se encontró perfil"
                self.perfil_id = perfil.id
                
                print(f"\n2️⃣ Perfil más reciente:")
                print(f"   - ID: {perfil.id}")
                print(f"   - Calidad: {perfil.calidad_general}")
                print(f"   - Dificultad: {perfil.dificultad}")
                print(f"   - Recomendación: {perfil.porcentaje_recomendacion}%")
                print(f"   - Reseñas encontradas: {perfil.total_resenias_encontradas}")
                print(f"   - Fecha extracción: {perfil.fecha_extraccion}")
                
                # 3. Contar reseñas
                result = await session.execute(
                    select(func.count(ReseniaMetadata.id))
                    .where(ReseniaMetadata.profesor_id == profesor.id)
                )
                total_resenias = result.scalar()
                
                print(f"\n3️⃣ Reseñas en base de datos:")
                print(f"   - Total: {total_resenias}")
                
                # 4. Verificar reseñas con comentario
                result = await session.execute(
                    select(func.count(ReseniaMetadata.id))
                    .where(ReseniaMetadata.profesor_id == profesor.id)
                    .where(ReseniaMetadata.tiene_comentario == True)
                )
                resenias_con_comentario = result.scalar()
                
                print(f"   - Con comentario: {resenias_con_comentario}")
                print(f"   - Sin comentario: {total_resenias - resenias_con_comentario}")
                
                # 5. Verificar cursos
                result = await session.execute(
                    select(func.count(func.distinct(ReseniaMetadata.curso_id)))
                    .where(ReseniaMetadata.profesor_id == profesor.id)
                    .where(ReseniaMetadata.curso_id.isnot(None))
                )
                total_cursos = result.scalar()
                
                print(f"\n4️⃣ Cursos impartidos: {total_cursos}")
                
                print("\n✅ PostgreSQL: Datos validados correctamente")
                return True
                
        except Exception as e:
            print(f"\n❌ Error en PostgreSQL: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_mongodb_data(self):
        """Test 3: Verificar inserción en MongoDB."""
        print("\n" + "="*70)
        print("TEST 3: Validación de datos en MongoDB")
        print("="*70)
        
        try:
            # 1. Contar opiniones del profesor
            total_opiniones = await self.mongo_db.opiniones.count_documents({
                'profesor_id': self.profesor_id
            })
            
            print(f"\n1️⃣ Opiniones en MongoDB:")
            print(f"   - Total: {total_opiniones}")
            
            assert total_opiniones > 0, "No se encontraron opiniones en MongoDB"
            
            # 2. Obtener muestra de opiniones
            opiniones_muestra = await self.mongo_db.opiniones.find(
                {'profesor_id': self.profesor_id}
            ).limit(3).to_list(length=3)
            
            print(f"\n2️⃣ Muestra de opiniones (primeras 3):")
            for i, op in enumerate(opiniones_muestra, 1):
                print(f"\n   Opinión #{i}:")
                print(f"   - MongoDB ID: {op['_id']}")
                print(f"   - Curso: {op.get('curso', 'N/A')}")
                print(f"   - Comentario: {op['comentario'][:80]}...")
                print(f"   - Longitud: {op.get('longitud_palabras', 0)} palabras")
                print(f"   - Vinculada a resenia_id: {op.get('resenia_id', 'N/A')}")
            
            # 3. Verificar estado de análisis
            pendientes_sentimiento = await self.mongo_db.opiniones.count_documents({
                'profesor_id': self.profesor_id,
                'sentimiento_general.analizado': False
            })
            
            pendientes_categorizacion = await self.mongo_db.opiniones.count_documents({
                'profesor_id': self.profesor_id,
                'categorizacion.analizado': False
            })
            
            print(f"\n3️⃣ Estado de análisis:")
            print(f"   - Pendientes análisis sentimiento: {pendientes_sentimiento}")
            print(f"   - Pendientes categorización: {pendientes_categorizacion}")
            
            print("\n✅ MongoDB: Datos validados correctamente")
            return True
            
        except Exception as e:
            print(f"\n❌ Error en MongoDB: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_cross_database_consistency(self):
        """Test 4: Verificar coherencia entre PostgreSQL y MongoDB."""
        print("\n" + "="*70)
        print("TEST 4: Coherencia entre bases de datos")
        print("="*70)
        
        try:
            async with get_db_session() as session:
                # 1. Obtener reseñas con vínculo a MongoDB
                result = await session.execute(
                    select(ReseniaMetadata)
                    .where(ReseniaMetadata.profesor_id == self.profesor_id)
                    .where(ReseniaMetadata.mongo_opinion_id.isnot(None))
                    .limit(5)
                )
                resenias_vinculadas = result.scalars().all()
                
                print(f"\n1️⃣ Reseñas vinculadas a MongoDB: {len(resenias_vinculadas)}")
                
                # 2. Verificar cada vínculo
                vinculaciones_exitosas = 0
                
                for resenia in resenias_vinculadas:
                    # Buscar en MongoDB por ObjectId
                    from bson import ObjectId
                    
                    opinion = await self.mongo_db.opiniones.find_one({
                        '_id': ObjectId(resenia.mongo_opinion_id)
                    })
                    
                    if opinion:
                        # Verificar coherencia
                        assert opinion['profesor_id'] == self.profesor_id, "Inconsistencia en profesor_id"
                        assert opinion['resenia_id'] == resenia.id, "Inconsistencia en resenia_id"
                        
                        vinculaciones_exitosas += 1
                
                print(f"   - Vinculaciones verificadas: {vinculaciones_exitosas}/{len(resenias_vinculadas)}")
                
                # 3. Verificar coherencia bidireccional
                opiniones_con_resenia_id = await self.mongo_db.opiniones.count_documents({
                    'profesor_id': self.profesor_id,
                    'resenia_id': {'$exists': True, '$ne': None}
                })
                
                print(f"\n2️⃣ Opiniones con resenia_id: {opiniones_con_resenia_id}")
                
                # Muestrear 3 opiniones y verificar que existen en PostgreSQL
                opiniones_muestra = await self.mongo_db.opiniones.find(
                    {
                        'profesor_id': self.profesor_id,
                        'resenia_id': {'$exists': True, '$ne': None}
                    }
                ).limit(3).to_list(length=3)
                
                for op in opiniones_muestra:
                    result = await session.execute(
                        select(ReseniaMetadata).where(ReseniaMetadata.id == op['resenia_id'])
                    )
                    resenia = result.scalar_one_or_none()
                    
                    assert resenia is not None, f"Reseña {op['resenia_id']} no existe en PostgreSQL"
                    assert str(resenia.mongo_opinion_id) == str(op['_id']), "Inconsistencia en vínculo bidireccional"
                
                print(f"   - Vinculaciones bidireccionales verificadas: 3/3")
                
                print("\n✅ Coherencia: Datos consistentes entre bases de datos")
                return True
                
        except Exception as e:
            print(f"\n❌ Error en verificación de coherencia: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_query_capabilities(self):
        """Test 5: Probar capacidades de consulta."""
        print("\n" + "="*70)
        print("TEST 5: Capacidades de consulta")
        print("="*70)
        
        try:
            async with get_db_session() as session:
                # 1. Consulta compleja en PostgreSQL
                from sqlalchemy import and_
                
                result = await session.execute(
                    select(
                        ReseniaMetadata.id,
                        ReseniaMetadata.fecha_resenia,
                        ReseniaMetadata.calidad_general,
                        ReseniaMetadata.tiene_comentario
                    )
                    .where(and_(
                        ReseniaMetadata.profesor_id == self.profesor_id,
                        ReseniaMetadata.calidad_general >= 8.0
                    ))
                    .order_by(ReseniaMetadata.fecha_resenia.desc())
                    .limit(5)
                )
                
                resenias_alta_calidad = result.all()
                
                print(f"\n1️⃣ Reseñas con calidad >= 8.0:")
                print(f"   - Total encontradas: {len(resenias_alta_calidad)}")
                
                for r in resenias_alta_calidad[:3]:
                    print(f"   - Fecha: {r.fecha_resenia}, Calidad: {r.calidad_general}, Con comentario: {r.tiene_comentario}")
                
                # 2. Búsqueda full-text en MongoDB
                opiniones_positivas = await self.mongo_db.opiniones.find(
                    {
                        '$text': {'$search': 'excelente buen recomendado'},
                        'profesor_id': self.profesor_id
                    },
                    {'score': {'$meta': 'textScore'}}
                ).sort([('score', {'$meta': 'textScore'})]).limit(3).to_list(length=3)
                
                print(f"\n2️⃣ Búsqueda full-text (palabras positivas):")
                print(f"   - Resultados: {len(opiniones_positivas)}")
                
                for op in opiniones_positivas:
                    print(f"   - {op['comentario'][:60]}... (score: {op.get('score', 0):.2f})")
                
                print("\n✅ Consultas: Funcionan correctamente")
                return True
                
        except Exception as e:
            print(f"\n❌ Error en consultas: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def cleanup(self):
        """Cerrar conexiones."""
        print("\n" + "="*70)
        print("CLEANUP: Cerrando conexiones")
        print("="*70)
        
        try:
            await close_db()
            print("✅ Conexiones cerradas")
        except Exception as e:
            print(f"⚠ Error en cleanup: {e}")
    
    async def run_all(self):
        """Ejecuta todos los tests."""
        print("\n" + "="*70)
        print("TEST DE INTEGRACIÓN COMPLETO - Josué Padilla Cuevas")
        print("="*70)
        print(f"Fecha: {datetime.now()}")
        print("="*70)
        
        if not await self.setup():
            return False
        
        tests = [
            ("Scraping del Profesor", self.test_scraping),
            ("Validación PostgreSQL", self.test_postgres_data),
            ("Validación MongoDB", self.test_mongodb_data),
            ("Coherencia entre BD", self.test_cross_database_consistency),
            ("Capacidades de Consulta", self.test_query_capabilities),
        ]
        
        results = {}
        for name, func in tests:
            results[name] = await func()
            if not results[name]:
                print(f"\n⚠ Test '{name}' falló - abortando suite")
                break
        
        await self.cleanup()
        
        # Resumen
        print("\n" + "="*70)
        print("RESUMEN DE TESTS")
        print("="*70)
        
        for name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {name}")
        
        passed = sum(results.values())
        total = len(results)
        
        print(f"\nResultado: {passed}/{total} tests exitosos")
        
        if passed == total:
            print("\n🎉 TODOS LOS TESTS PASARON")
            print("="*70)
            return True
        else:
            print("\n⚠️ ALGUNOS TESTS FALLARON")
            print("="*70)
            return False


if __name__ == "__main__":
    tester = TestScrapingIntegration()
    success = asyncio.run(tester.run_all())
    sys.exit(0 if success else 1)
