#!/usr/bin/env python3
"""
Test de Integración de Bases de Datos - SentimentInsightUAM v1.1.1

Valida inserción y consulta de datos en PostgreSQL y MongoDB siguiendo
el esquema real de las bases de datos.
"""

import sys
import os
from datetime import datetime, date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from pymongo import MongoClient
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Error: {e}")
    print("Ejecuta: pip install psycopg2-binary pymongo python-dotenv")
    sys.exit(1)

load_dotenv()


class DatabaseTester:
    def __init__(self):
        self.pg_conn = None
        self.pg_cursor = None
        self.mongo_client = None
        self.mongo_db = None
        self.test_data = {}
        
    def connect_postgres(self):
        try:
            print("\n📊 Conectando a PostgreSQL...")
            self.pg_conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                database=os.getenv("POSTGRES_DB", "sentiment_uam_db"),
                user=os.getenv("POSTGRES_USER", "sentiment_admin"),
                password=os.getenv("POSTGRES_PASSWORD", "dev_password_2024")
            )
            self.pg_cursor = self.pg_conn.cursor(cursor_factory=RealDictCursor)
            print("✅ Conexión a PostgreSQL exitosa")
            return True
        except Exception as e:
            print(f"❌ Error PostgreSQL: {e}")
            return False
    
    def connect_mongodb(self):
        try:
            print("\n🍃 Conectando a MongoDB...")
            mongo_uri = (
                f"mongodb://{os.getenv('MONGO_USER', 'sentiment_admin')}:"
                f"{os.getenv('MONGO_PASSWORD', 'dev_password_2024')}@"
                f"{os.getenv('MONGO_HOST', 'localhost')}:"
                f"{os.getenv('MONGO_PORT', '27017')}/"
                f"{os.getenv('MONGO_DB', 'sentiment_uam_nlp')}?"
                f"authSource={os.getenv('MONGO_DB', 'sentiment_uam_nlp')}"
            )
            self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            self.mongo_client.admin.command('ping')
            self.mongo_db = self.mongo_client[os.getenv('MONGO_DB', 'sentiment_uam_nlp')]
            print("✅ Conexión a MongoDB exitosa")
            return True
        except Exception as e:
            print(f"❌ Error MongoDB: {e}")
            return False
    
    def test_postgres_insert(self):
        print("\n" + "="*70)
        print("TEST 1: Inserción en PostgreSQL")
        print("="*70)
        
        try:
            # 1. Profesor
            print("\n1️⃣ Insertando profesor...")
            self.pg_cursor.execute("""
                INSERT INTO profesores (nombre_completo, nombre_limpio, slug, departamento)
                VALUES (%s, %s, %s, %s)
                RETURNING id, nombre_completo
            """, ("Juan Pérez López", "Juan Perez Lopez", "juan-perez-lopez", "Sistemas"))
            prof = self.pg_cursor.fetchone()
            self.test_data['prof_id'] = prof['id']
            print(f"   ✓ Profesor ID={prof['id']}: {prof['nombre_completo']}")
            
            # 2. Perfil
            print("\n2️⃣ Insertando perfil...")
            self.pg_cursor.execute("""
                INSERT INTO perfiles (profesor_id, calidad_general,
                                    dificultad, porcentaje_recomendacion, total_resenias_encontradas)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, calidad_general
            """, (self.test_data['prof_id'], 9.5, 7.2, 95.0, 1))
            perfil = self.pg_cursor.fetchone()
            print(f"   ✓ Perfil ID={perfil['id']}, Calificación={perfil['calidad_general']}")
            
            # 3. Curso
            print("\n3️⃣ Insertando curso...")
            self.pg_cursor.execute("""
                INSERT INTO cursos (nombre, nombre_normalizado, codigo, nivel)
                VALUES (%s, %s, %s, %s)
                RETURNING id, nombre
            """, ("Estructura de Datos", "estructura de datos", "EDA-101", "Licenciatura"))
            curso = self.pg_cursor.fetchone()
            self.test_data['curso_id'] = curso['id']
            print(f"   ✓ Curso ID={curso['id']}: {curso['nombre']}")
            
            # 4. Reseña
            print("\n4️⃣ Insertando reseña...")
            self.pg_cursor.execute("""
                INSERT INTO resenias_metadata (
                    profesor_id, curso_id, fecha_resenia, calidad_general,
                    facilidad, asistencia, calificacion_recibida,
                    nivel_interes, fecha_extraccion
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, calidad_general
            """, (self.test_data['prof_id'], self.test_data['curso_id'],
                  date(2024, 10, 15), 9.5, 8.0, "Obligatoria", "10", "Alta", datetime.now()))
            resenia = self.pg_cursor.fetchone()
            self.test_data['resenia_id'] = resenia['id']
            print(f"   ✓ Reseña ID={resenia['id']}, Calificación={resenia['calidad_general']}")
            
            # 5. Etiquetas
            print("\n5️⃣ Asociando etiquetas...")
            self.pg_cursor.execute("""
                SELECT id, etiqueta FROM etiquetas WHERE etiqueta IN ('EXCELENTE CLASE', 'BUENA ONDA')
            """)
            for etiq in self.pg_cursor.fetchall():
                self.pg_cursor.execute("""
                    INSERT INTO resenia_etiquetas (resenia_id, etiqueta_id) VALUES (%s, %s)
                """, (self.test_data['resenia_id'], etiq['id']))
                print(f"   ✓ Etiqueta '{etiq['etiqueta']}' vinculada")
            
            self.pg_conn.commit()
            print("\n✅ PostgreSQL: Datos insertados correctamente")
            return True
        except Exception as e:
            self.pg_conn.rollback()
            print(f"\n❌ Error PostgreSQL: {e}")
            return False
    
    def test_mongodb_insert(self):
        print("\n" + "="*70)
        print("TEST 2: Inserción en MongoDB")
        print("="*70)
        
        try:
            self.pg_cursor.execute("SELECT nombre_completo, slug FROM profesores WHERE id = %s",
                                 (self.test_data['prof_id'],))
            prof = self.pg_cursor.fetchone()
            
            print("\n1️⃣ Insertando opinión en MongoDB...")
            opinion = {
                "profesor_id": self.test_data['prof_id'],
                "profesor_nombre": prof['nombre_completo'],
                "profesor_slug": prof['slug'],
                "resenia_id": self.test_data['resenia_id'],
                "fecha_opinion": datetime(2024, 10, 15),
                "curso": "Estructura de Datos",
                "comentario": "Excelente profesor, explica muy bien. Recomendado 100%.",
                "idioma": "es",
                "longitud_caracteres": 65,
                "longitud_palabras": 9,
                "sentimiento_general": {
                    "analizado": False,
                    "clasificacion": None,
                    "pesos": None,
                    "confianza": None
                },
                "categorizacion": {
                    "analizado": False
                },
                "fecha_extraccion": datetime.now(),
                "fuente": "misprofesores.com"
            }
            
            result = self.mongo_db.opiniones.insert_one(opinion)
            self.test_data['opinion_id'] = result.inserted_id
            print(f"   ✓ Opinión ID={result.inserted_id}")
            print(f"   ✓ Vinculada a resenia_id={self.test_data['resenia_id']} (PostgreSQL)")
            print("\n✅ MongoDB: Opinión insertada correctamente")
            return True
        except Exception as e:
            print(f"\n❌ Error MongoDB: {e}")
            return False
    
    def test_cross_query(self):
        print("\n" + "="*70)
        print("TEST 3: Consulta Cruzada PostgreSQL ↔ MongoDB")
        print("="*70)
        
        try:
            # PostgreSQL → MongoDB
            print("\n1️⃣ PostgreSQL → MongoDB...")
            self.pg_cursor.execute("""
                SELECT p.nombre_completo, r.id as resenia_id, c.nombre as nombre_curso
                FROM profesores p
                JOIN resenias_metadata r ON p.id = r.profesor_id
                JOIN cursos c ON r.curso_id = c.id
                WHERE p.id = %s
            """, (self.test_data['prof_id'],))
            pg_data = self.pg_cursor.fetchone()
            
            mongo_op = self.mongo_db.opiniones.find_one({"resenia_id": pg_data['resenia_id']})
            print(f"   ✓ PostgreSQL resenia_id={pg_data['resenia_id']}")
            print(f"   ✓ MongoDB opinion_id={mongo_op['_id']}")
            print(f"   ✓ Profesor: {pg_data['nombre_completo']}")
            print(f"   ✓ Curso: {pg_data['nombre_curso']}")
            
            # MongoDB → PostgreSQL
            print("\n2️⃣ MongoDB → PostgreSQL...")
            opinion = self.mongo_db.opiniones.find_one({"_id": self.test_data['opinion_id']})
            self.pg_cursor.execute("""
                SELECT r.calidad_general, p.nombre_completo
                FROM resenias_metadata r
                JOIN profesores p ON r.profesor_id = p.id
                WHERE r.id = %s
            """, (opinion['resenia_id'],))
            pg_rel = self.pg_cursor.fetchone()
            print(f"   ✓ Calificación: {pg_rel['calidad_general']}/10")
            print(f"   ✓ Profesor: {pg_rel['nombre_completo']}")
            
            print("\n✅ Consulta cruzada: Relaciones validadas correctamente")
            return True
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False
    
    def cleanup(self):
        print("\n" + "="*70)
        print("LIMPIEZA: Eliminando datos de prueba")
        print("="*70)
        
        try:
            # MongoDB
            result = self.mongo_db.opiniones.delete_many({"profesor_id": self.test_data['prof_id']})
            print(f"\n✓ MongoDB: {result.deleted_count} opiniones eliminadas")
            
            # PostgreSQL (CASCADE elimina relaciones)
            self.pg_cursor.execute("DELETE FROM profesores WHERE id = %s", (self.test_data['prof_id'],))
            self.pg_conn.commit()
            print(f"✓ PostgreSQL: Profesor y datos relacionados eliminados")
            
            print("\n✅ Limpieza completada")
            return True
        except Exception as e:
            print(f"\n❌ Error en limpieza: {e}")
            return False
    
    def close(self):
        if self.pg_cursor:
            self.pg_cursor.close()
        if self.pg_conn:
            self.pg_conn.close()
        if self.mongo_client:
            self.mongo_client.close()
        print("\n🔌 Conexiones cerradas")
    
    def run_all(self):
        print("\n" + "="*70)
        print("TESTS DE INTEGRACIÓN - SentimentInsightUAM v1.1.1")
        print("="*70)
        
        if not self.connect_postgres() or not self.connect_mongodb():
            return False
        
        tests = [
            ("PostgreSQL Insert", self.test_postgres_insert),
            ("MongoDB Insert", self.test_mongodb_insert),
            ("Cross-Database Query", self.test_cross_query),
        ]
        
        results = {}
        for name, func in tests:
            results[name] = func()
            if not results[name]:
                break
        
        if all(results.values()):
            self.cleanup()
        
        self.close()
        
        # Resumen
        print("\n" + "="*70)
        print("RESUMEN")
        print("="*70)
        for name, result in results.items():
            print(f"{'✅ PASS' if result else '❌ FAIL'} - {name}")
        
        passed = sum(results.values())
        total = len(results)
        print(f"\n{passed}/{total} tests exitosos")
        
        if passed == total:
            print("\n🎉 TODOS LOS TESTS PASARON")
            return True
        else:
            print("\n⚠️ ALGUNOS TESTS FALLARON")
            return False


if __name__ == "__main__":
    tester = DatabaseTester()
    success = tester.run_all()
    sys.exit(0 if success else 1)
