// ============================================================================
// Script de Inicialización de MongoDB para SentimentInsightUAM
// ============================================================================
// Base de datos: sentiment_uam_nlp
// Versión: 1.1.0
// Fecha: 2025-11-08
// 
// Descripción:
// Este script crea la estructura completa de la base de datos MongoDB
// para almacenar opiniones textuales y análisis de sentimiento con BERT.
// 
// Ejecución:
// mongosh sentiment_uam_nlp scripts/init_mongo.js
// ============================================================================

print('============================================================================');
print('Inicializando MongoDB para SentimentInsightUAM');
print('============================================================================');
print('');

// ============================================================================
// COLECCIÓN: opiniones
// ============================================================================

print('1. Creando colección "opiniones" con validación de esquema...');

// Eliminar colección si existe (solo para reinicialización)
// db.opiniones.drop();

// Crear colección con validación JSON Schema
db.createCollection("opiniones", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["profesor_id", "comentario", "fecha_opinion", "fecha_extraccion"],
            properties: {
                profesor_id: {
                    bsonType: "int",
                    description: "ID del profesor en PostgreSQL (requerido)"
                },
                profesor_nombre: {
                    bsonType: "string",
                    description: "Nombre limpio del profesor"
                },
                profesor_slug: {
                    bsonType: "string",
                    description: "Slug del profesor para URLs"
                },
                resenia_id: {
                    bsonType: ["int", "null"],
                    description: "ID de resenia_metadata en PostgreSQL"
                },
                fecha_opinion: {
                    bsonType: "date",
                    description: "Fecha de la opinión (requerido)"
                },
                curso: {
                    bsonType: ["string", "null"],
                    description: "Nombre del curso"
                },
                comentario: {
                    bsonType: "string",
                    minLength: 1,
                    description: "Texto del comentario (requerido)"
                },
                idioma: {
                    enum: ["es", "en"],
                    description: "Idioma del comentario (default: es)"
                },
                longitud_caracteres: {
                    bsonType: ["int", "null"],
                    minimum: 0,
                    description: "Longitud del comentario en caracteres"
                },
                longitud_palabras: {
                    bsonType: ["int", "null"],
                    minimum: 0,
                    description: "Longitud del comentario en palabras"
                },
                sentimiento_general: {
                    bsonType: "object",
                    properties: {
                        analizado: { 
                            bsonType: "bool",
                            description: "Si fue procesado por BERT (Módulo 1)"
                        },
                        clasificacion: {
                            enum: ["positivo", "neutral", "negativo", null],
                            description: "Clasificación basada en pesos"
                        },
                        pesos: {
                            bsonType: ["object", "null"],
                            description: "Pesos del análisis BERT",
                            properties: {
                                positivo: {
                                    bsonType: ["double", "null"],
                                    minimum: 0,
                                    maximum: 1,
                                    description: "Peso para sentimiento positivo"
                                },
                                negativo: {
                                    bsonType: ["double", "null"],
                                    minimum: 0,
                                    maximum: 1,
                                    description: "Peso para sentimiento negativo"
                                },
                                neutro: {
                                    bsonType: ["double", "null"],
                                    minimum: 0,
                                    maximum: 1,
                                    description: "Peso para sentimiento neutro"
                                }
                            }
                        },
                        confianza: {
                            bsonType: ["double", "null"],
                            minimum: 0,
                            maximum: 1,
                            description: "Confianza de la clasificación (0 a 1)"
                        },
                        modelo_version: {
                            bsonType: ["string", "null"],
                            description: "Versión del modelo BERT usado"
                        },
                        fecha_analisis: {
                            bsonType: ["date", "null"],
                            description: "Timestamp del análisis"
                        },
                        tiempo_procesamiento_ms: {
                            bsonType: ["int", "null"],
                            minimum: 0,
                            description: "Tiempo de procesamiento en ms"
                        }
                    }
                },
                categorizacion: {
                    bsonType: "object",
                    properties: {
                        analizado: {
                            bsonType: "bool",
                            description: "Si fue procesado por módulo de categorización (Módulo 2)"
                        },
                        calidad_didactica: {
                            bsonType: ["object", "null"],
                            description: "Evaluación de calidad didáctica del profesor",
                            properties: {
                                valoracion: {
                                    enum: ["POS", "NEG", "NEUTRO", null],
                                    description: "Valoración de calidad didáctica"
                                },
                                confianza: {
                                    bsonType: ["double", "null"],
                                    minimum: 0,
                                    maximum: 1,
                                    description: "Confianza de la categorización"
                                },
                                palabras_clave: {
                                    bsonType: "array",
                                    description: "Palabras/frases relevantes"
                                }
                            }
                        },
                        metodo_evaluacion: {
                            bsonType: ["object", "null"],
                            description: "Evaluación del método de evaluación del profesor",
                            properties: {
                                valoracion: {
                                    enum: ["POS", "NEG", "NEUTRO", null],
                                    description: "Valoración del método de evaluación"
                                },
                                confianza: {
                                    bsonType: ["double", "null"],
                                    minimum: 0,
                                    maximum: 1,
                                    description: "Confianza de la categorización"
                                },
                                palabras_clave: {
                                    bsonType: "array",
                                    description: "Palabras/frases relevantes"
                                }
                            }
                        },
                        empatia: {
                            bsonType: ["object", "null"],
                            description: "Evaluación de la empatía del profesor",
                            properties: {
                                valoracion: {
                                    enum: ["POS", "NEG", "NEUTRO", null],
                                    description: "Valoración de empatía"
                                },
                                confianza: {
                                    bsonType: ["double", "null"],
                                    minimum: 0,
                                    maximum: 1,
                                    description: "Confianza de la categorización"
                                },
                                palabras_clave: {
                                    bsonType: "array",
                                    description: "Palabras/frases relevantes"
                                }
                            }
                        },
                        modelo_version: {
                            bsonType: ["string", "null"],
                            description: "Versión del modelo de categorización"
                        },
                        fecha_analisis: {
                            bsonType: ["date", "null"],
                            description: "Timestamp del análisis"
                        },
                        tiempo_procesamiento_ms: {
                            bsonType: ["int", "null"],
                            minimum: 0,
                            description: "Tiempo de procesamiento en ms"
                        }
                    }
                },
                embedding: {
                    bsonType: ["array", "null"],
                    description: "Vector de embeddings BERT (768 dimensiones)"
                },
                fecha_extraccion: {
                    bsonType: "date",
                    description: "Fecha de extracción del scraper (requerido)"
                },
                fuente: {
                    bsonType: "string",
                    description: "Fuente de datos"
                },
                version_scraper: {
                    bsonType: "string",
                    description: "Versión del scraper usado"
                }
            }
        }
    },
    validationLevel: "moderate",
    validationAction: "warn"
});

print('✓ Colección "opiniones" creada con validación');
print('');

// ============================================================================
// ÍNDICES
// ============================================================================

print('2. Creando índices para optimización de consultas...');

// Índice 1: Búsquedas por profesor y fecha (más común)
db.opiniones.createIndex(
    { "profesor_id": 1, "fecha_opinion": -1 },
    { 
        name: "idx_profesor_fecha",
        background: true
    }
);
print('  ✓ Índice compuesto: profesor_id + fecha_opinion');

// Índice 2: Opiniones pendientes de análisis de sentimiento general (Módulo 1)
db.opiniones.createIndex(
    { "sentimiento_general.analizado": 1 },
    { 
        name: "idx_sentimiento_general_analizado",
        background: true,
        partialFilterExpression: { "sentimiento_general.analizado": false }
    }
);
print('  ✓ Índice parcial: sentimiento_general.analizado = false (Módulo 1)');

// Índice 3: Opiniones pendientes de categorización (Módulo 2)
db.opiniones.createIndex(
    { "categorizacion.analizado": 1 },
    { 
        name: "idx_categorizacion_analizado",
        background: true,
        partialFilterExpression: { "categorizacion.analizado": false }
    }
);
print('  ✓ Índice parcial: categorizacion.analizado = false (Módulo 2)');

// Índice 4: Clasificación de sentimiento general
db.opiniones.createIndex(
    { "sentimiento_general.clasificacion": 1 },
    { 
        name: "idx_sentimiento_clasificacion",
        background: true
    }
);
print('  ✓ Índice simple: sentimiento_general.clasificacion');

// Índice 5: Búsqueda por categorías específicas (compuesto)
db.opiniones.createIndex(
    { 
        "categorizacion.calidad_didactica.valoracion": 1,
        "categorizacion.metodo_evaluacion.valoracion": 1,
        "categorizacion.empatia.valoracion": 1
    },
    { 
        name: "idx_categorizacion_valoraciones",
        background: true
    }
);
print('  ✓ Índice compuesto: valoraciones de 3 categorías');

// Índice 4: Búsqueda full-text en comentarios y curso
db.opiniones.createIndex(
    { 
        "comentario": "text", 
        "curso": "text" 
    },
    {
        name: "idx_fulltext_comentario_curso",
        weights: { comentario: 10, curso: 5 },
        default_language: "spanish",
        language_override: "idioma",
        background: true
    }
);
print('  ✓ Índice full-text: comentario + curso (español)');

// Índice 5: Búsqueda por curso
db.opiniones.createIndex(
    { "curso": 1 },
    { 
        name: "idx_curso",
        background: true
    }
);
print('  ✓ Índice simple: curso');

// Índice 6: Ordenamiento temporal
db.opiniones.createIndex(
    { "fecha_opinion": -1 },
    { 
        name: "idx_fecha_opinion",
        background: true
    }
);
print('  ✓ Índice simple: fecha_opinion (DESC)');

// Índice 7: Vínculo con PostgreSQL (único y sparse)
db.opiniones.createIndex(
    { "resenia_id": 1 },
    { 
        name: "idx_resenia_id_unique",
        unique: true,
        sparse: true,
        background: true
    }
);
print('  ✓ Índice único: resenia_id');

// Índice 8: Búsqueda por slug de profesor
db.opiniones.createIndex(
    { "profesor_slug": 1 },
    { 
        name: "idx_profesor_slug",
        background: true
    }
);
print('  ✓ Índice simple: profesor_slug');

// Nota: Índice vectorial para embeddings requiere MongoDB Atlas o configuración especial
// Se comentará para inicialización básica
/*
db.opiniones.createSearchIndex(
    "embedding_vector_index",
    {
        mappings: {
            dynamic: false,
            fields: {
                embedding: {
                    type: "knnVector",
                    dimensions: 768,
                    similarity: "cosine"
                }
            }
        }
    }
);
print('  ✓ Índice vectorial: embedding (768 dims, cosine)');
*/

print('');
print('Total de índices creados: ' + db.opiniones.getIndexes().length);
print('');

// ============================================================================
// COLECCIÓN: sentimiento_cache (opcional, para optimización)
// ============================================================================

print('3. Creando colección auxiliar "sentimiento_cache"...');

db.createCollection("sentimiento_cache", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["texto_hash", "resultado"],
            properties: {
                texto_hash: {
                    bsonType: "string",
                    description: "Hash SHA256 del texto"
                },
                resultado: {
                    bsonType: "object",
                    description: "Resultado del análisis BERT"
                },
                hits: {
                    bsonType: "int",
                    minimum: 0,
                    description: "Número de veces usado"
                },
                created_at: {
                    bsonType: "date"
                },
                last_used: {
                    bsonType: "date"
                }
            }
        }
    }
});

// Índice único para el hash
db.sentimiento_cache.createIndex(
    { "texto_hash": 1 },
    { 
        name: "idx_texto_hash_unique",
        unique: true
    }
);

// TTL index: eliminar cache después de 90 días de no uso
db.sentimiento_cache.createIndex(
    { "last_used": 1 },
    { 
        name: "idx_ttl_last_used",
        expireAfterSeconds: 7776000  // 90 días
    }
);

print('✓ Colección "sentimiento_cache" creada');
print('');

// ============================================================================
// DATOS INICIALES DE PRUEBA (SEED)
// ============================================================================

print('4. Insertando datos de prueba (opcional)...');

// Comentar esta sección si no se desean datos de prueba
/*
db.opiniones.insertMany([
    {
        profesor_id: 999,
        profesor_nombre: "Profesor de Prueba",
        profesor_slug: "profesor-de-prueba",
        resenia_id: null,
        fecha_opinion: new Date("2025-01-15"),
        curso: "Curso de Prueba",
        comentario: "Este es un comentario de prueba para validar la estructura de la base de datos.",
        idioma: "es",
        longitud_caracteres: 85,
        longitud_palabras: 15,
        sentimiento: {
            analizado: false,
            puntuacion: null,
            confianza: null,
            clasificacion: null,
            aspectos: null,
            modelo_version: null,
            fecha_analisis: null,
            tiempo_procesamiento_ms: null
        },
        embedding: null,
        fecha_extraccion: new Date(),
        fuente: "misprofesores.com",
        version_scraper: "1.0.0"
    }
]);

print('✓ Documento de prueba insertado');
*/
print('  (Omitido - se poblarán datos reales con el scraper)');
print('');

// ============================================================================
// VALIDACIÓN Y ESTADÍSTICAS
// ============================================================================

print('5. Validando estructura de la base de datos...');
print('');

// Listar todas las colecciones
const collections = db.getCollectionNames();
print('Colecciones creadas:');
collections.forEach(function(coll) {
    print('  - ' + coll);
});
print('');

// Estadísticas de índices por colección
print('Índices por colección:');
collections.forEach(function(coll) {
    const indexes = db.getCollection(coll).getIndexes();
    print('  ' + coll + ': ' + indexes.length + ' índices');
});
print('');

// Información de la base de datos
const dbStats = db.stats();
print('Estadísticas de la base de datos:');
print('  - Tamaño de datos: ' + (dbStats.dataSize / 1024).toFixed(2) + ' KB');
print('  - Tamaño de índices: ' + (dbStats.indexSize / 1024).toFixed(2) + ' KB');
print('  - Colecciones: ' + dbStats.collections);
print('  - Documentos totales: ' + dbStats.objects);
print('');

// ============================================================================
// CREACIÓN DE USUARIO DE APLICACIÓN
// ============================================================================

print('6. Configurando usuario de aplicación en MongoDB...');
print('');

// Leer variables de entorno pasadas desde Docker Compose
const appUser = process.env.MONGO_USER || 'sentiment_admin';
const appPassword = process.env.MONGO_PASSWORD || 'dev_password_2024';

try {
    // Crear usuario de aplicación con permisos específicos
    db.createUser({
        user: appUser,
        pwd: appPassword,
        roles: [
            {
                role: "readWrite",
                db: "sentiment_uam_nlp"
            },
            {
                role: "dbAdmin",
                db: "sentiment_uam_nlp"
            }
        ],
        mechanisms: ["SCRAM-SHA-256"]
    });
    
    print('✓ Usuario "' + appUser + '" creado exitosamente');
    print('  - Base de datos: sentiment_uam_nlp');
    print('  - Roles: readWrite, dbAdmin');
    print('  - Autenticación: SCRAM-SHA-256');
    print('');
} catch (error) {
    if (error.code === 51003) {
        print('⚠ Usuario "' + appUser + '" ya existe - omitiendo creación');
        print('');
    } else {
        print('❌ Error al crear usuario: ' + error.message);
        print('');
    }
}

// ============================================================================
// MENSAJE FINAL
// ============================================================================

print('============================================================================');
print('INICIALIZACIÓN DE MONGODB COMPLETADA EXITOSAMENTE');
print('============================================================================');
print('');
print('Base de datos: sentiment_uam_nlp');
print('Versión: 1.1.0');
print('Fecha: ' + new Date());
print('');
print('Resumen:');
print('  - Colecciones: ' + collections.length);
print('  - Índices en "opiniones": ' + db.opiniones.getIndexes().length);
print('  - Validación de esquema: Activa (modo: moderate)');
print('  - Usuario de aplicación: ' + appUser);
print('');
print('Próximos pasos:');
print('  1. Integrar con scraper para poblar datos');
print('  2. Configurar worker BERT para análisis');
print('  3. Verificar índices con explain() en consultas reales');
print('');
print('La base de datos está lista para recibir opiniones del scraper.');
print('============================================================================');
