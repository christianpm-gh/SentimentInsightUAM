# Diseño de Persistencia - SentimentInsightUAM

**Versión**: 1.1.0  
**Fecha**: 2025-11-08  
**Estado**: Diseño Aprobado - Listo para Implementación

---

## 📊 Análisis de Datos del Scraping

### Estructura de Salida JSON Actual

Basado en el scraping de profesores reales (Josue Padilla Cuevas y Rodrigo Alexander Castro Campos):

```json
{
  "name": "Nombre Completo - Institución - MisProfesores.com",
  "overall_quality": 9.4,
  "difficulty": 2.9,
  "recommend_percent": 97.0,
  "tags": [
    {"label": "BRINDA APOYO", "count": 11},
    {"label": "CLASES EXCELENTES", "count": 13}
  ],
  "reviews": [
    {
      "date": "2025-08-09",
      "course": "Bases de Datos",
      "overall": 8.0,
      "ease": 8.0,
      "attendance": "Obligatoria",
      "grade_received": "23",
      "interest": "Alto",
      "tags": ["Califica Duro", "Clases excelentes"],
      "comment": "Muy buen profesor, domina la materia..."
    }
  ],
  "cached": false
}
```

### Observaciones Clave

1. **Nombre del profesor**: Incluye institución en el texto (necesita limpieza)
2. **Métricas numéricas**: Calidad (0-10), Dificultad (0-10), Recomendación (0-100%)
3. **Etiquetas del perfil**: Con contadores de frecuencia
4. **Reseñas**: 
   - Fecha en ISO 8601 ✅
   - Curso (puede ser "---" o texto libre)
   - Calificaciones: overall (calidad) y ease (facilidad)
   - Asistencia: "Obligatoria" | "No obligatoria"
   - Calificación recibida: String ("10", "MB", "23", etc.)
   - Nivel de interés: "Alto" | "Medio" | "Bajo"
   - Etiquetas de la reseña: Array de strings
   - **Comentario textual**: Target para análisis de sentimiento 🎯

---

## 🗄️ Arquitectura de Bases de Datos

### Decisión de Diseño: Dual Database

```
┌─────────────────────────────────────────────────────────────┐
│                  SentimentInsightUAM                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────┐       ┌──────────────────────┐  │
│  │    PostgreSQL        │       │      MongoDB         │  │
│  │  "sentiment_uam_db"  │       │ "sentiment_uam_nlp"  │  │
│  ├──────────────────────┤       ├──────────────────────┤  │
│  │ - Profesores         │       │ - Opiniones          │  │
│  │ - Perfiles           │       │ - Análisis BERT      │  │
│  │ - Reseñas Metadata   │◄─────►│ - Embeddings         │  │
│  │ - Cursos             │       │ - Sentimientos       │  │
│  │ - Etiquetas          │       │                      │  │
│  │ - Historial          │       │                      │  │
│  └──────────────────────┘       └──────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Razones para PostgreSQL**:
- ✅ Integridad referencial para datos estructurados
- ✅ JOINs complejos para estadísticas
- ✅ Índices eficientes para calificaciones numéricas
- ✅ Transacciones ACID para consistencia
- ✅ Ideal para dashboards y reportes

**Razones para MongoDB**:
- ✅ Almacenamiento flexible de comentarios largos
- ✅ Documentos con estructura anidada (análisis de sentimiento)
- ✅ Búsqueda full-text nativa
- ✅ Escalabilidad horizontal para NLP
- ✅ Ideal para procesamiento BERT y embeddings

---

## 🐘 PostgreSQL: Esquema Detallado

### Nombre de Base de Datos: `sentiment_uam_db`

### Tabla: `profesores`

**Propósito**: Catálogo maestro de profesores de la UAM Azcapotzalco

```sql
CREATE TABLE profesores (
    id SERIAL PRIMARY KEY,
    
    -- Identificación
    nombre_completo VARCHAR(255) NOT NULL,
    nombre_limpio VARCHAR(255) NOT NULL,  -- Sin "- UAM (Azcapotzalco)"
    slug VARCHAR(255) UNIQUE NOT NULL,
    
    -- URLs de origen
    url_directorio_uam TEXT,
    url_misprofesores TEXT,
    
    -- Metadata
    departamento VARCHAR(100) DEFAULT 'Sistemas',
    activo BOOLEAN DEFAULT TRUE,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX idx_profesores_slug ON profesores(slug);
CREATE INDEX idx_profesores_nombre_limpio ON profesores(nombre_limpio);
CREATE INDEX idx_profesores_departamento ON profesores(departamento);
CREATE INDEX idx_profesores_activo ON profesores(activo) WHERE activo = TRUE;

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_profesores_updated_at
BEFORE UPDATE ON profesores
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**Ejemplo de registro**:
```sql
INSERT INTO profesores (nombre_completo, nombre_limpio, slug, url_misprofesores)
VALUES (
    'Josue Padilla - UAM (Azcapotzalco) - Universidad Autónoma Metropolitana - MisProfesores.com',
    'Josue Padilla',
    'josue-padilla-cuevas',
    'https://www.misprofesores.com/profesores/Josue-Padilla-Cuevas_123456'
);
```

---

### Tabla: `perfiles`

**Propósito**: Snapshot temporal de métricas de cada profesor (historial de cambios)

```sql
CREATE TABLE perfiles (
    id SERIAL PRIMARY KEY,
    
    -- Relación
    profesor_id INTEGER NOT NULL REFERENCES profesores(id) ON DELETE CASCADE,
    
    -- Métricas principales (del perfil de MisProfesores)
    calidad_general DECIMAL(3, 2) CHECK (calidad_general >= 0 AND calidad_general <= 10),
    dificultad DECIMAL(3, 2) CHECK (dificultad >= 0 AND dificultad <= 10),
    porcentaje_recomendacion DECIMAL(5, 2) CHECK (porcentaje_recomendacion >= 0 AND porcentaje_recomendacion <= 100),
    
    -- Metadatos de scraping
    total_resenias_encontradas INTEGER DEFAULT 0,
    scraping_exitoso BOOLEAN DEFAULT TRUE,
    fuente VARCHAR(50) DEFAULT 'misprofesores.com',
    
    -- Auditoría
    fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Índice único para evitar duplicados del mismo día
    UNIQUE(profesor_id, DATE(fecha_extraccion))
);

-- Índices
CREATE INDEX idx_perfiles_profesor ON perfiles(profesor_id);
CREATE INDEX idx_perfiles_fecha ON perfiles(fecha_extraccion DESC);
CREATE INDEX idx_perfiles_calidad ON perfiles(calidad_general DESC);

-- Vista para el perfil más reciente de cada profesor
CREATE OR REPLACE VIEW perfiles_actuales AS
SELECT DISTINCT ON (profesor_id)
    p.*,
    prof.nombre_limpio,
    prof.slug
FROM perfiles p
INNER JOIN profesores prof ON p.profesor_id = prof.id
ORDER BY profesor_id, fecha_extraccion DESC;
```

**Ejemplo de registro**:
```sql
INSERT INTO perfiles (profesor_id, calidad_general, dificultad, porcentaje_recomendacion, total_resenias_encontradas)
VALUES (1, 9.4, 2.9, 97.0, 38);
```

---

### Tabla: `etiquetas`

**Propósito**: Catálogo unificado de etiquetas (tags) del sistema

```sql
CREATE TABLE etiquetas (
    id SERIAL PRIMARY KEY,
    
    -- Etiqueta normalizada
    etiqueta VARCHAR(100) UNIQUE NOT NULL,
    etiqueta_normalizada VARCHAR(100) UNIQUE NOT NULL,  -- lowercase, sin acentos
    
    -- Categorización (manual o automática)
    categoria VARCHAR(50),  -- 'positivo', 'negativo', 'neutral', 'carga_trabajo', etc.
    
    -- Estadísticas
    uso_total INTEGER DEFAULT 0,  -- Contador acumulado
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX idx_etiquetas_etiqueta_normalizada ON etiquetas(etiqueta_normalizada);
CREATE INDEX idx_etiquetas_categoria ON etiquetas(categoria);
CREATE INDEX idx_etiquetas_uso_total ON etiquetas(uso_total DESC);

-- Función para normalizar etiquetas
CREATE OR REPLACE FUNCTION normalizar_etiqueta(texto VARCHAR)
RETURNS VARCHAR AS $$
BEGIN
    RETURN LOWER(TRIM(
        TRANSLATE(texto, 
            'ÁÉÍÓÚáéíóúÑñ', 
            'AEIOUaeiouNn'
        )
    ));
END;
$$ LANGUAGE plpgsql IMMUTABLE;
```

**Ejemplo de registros**:
```sql
INSERT INTO etiquetas (etiqueta, etiqueta_normalizada, categoria)
VALUES 
    ('BRINDA APOYO', 'brinda apoyo', 'positivo'),
    ('CLASES EXCELENTES', 'clases excelentes', 'positivo'),
    ('CALIFICA DURO', 'califica duro', 'negativo'),
    ('MUCHAS TAREAS', 'muchas tareas', 'carga_trabajo');
```

---

### Tabla: `perfil_etiquetas`

**Propósito**: Relación many-to-many entre perfiles y etiquetas con contadores

```sql
CREATE TABLE perfil_etiquetas (
    id SERIAL PRIMARY KEY,
    
    -- Relaciones
    perfil_id INTEGER NOT NULL REFERENCES perfiles(id) ON DELETE CASCADE,
    etiqueta_id INTEGER NOT NULL REFERENCES etiquetas(id) ON DELETE CASCADE,
    
    -- Contador (del JSON "count")
    contador INTEGER DEFAULT 0,
    
    -- Evitar duplicados
    UNIQUE(perfil_id, etiqueta_id)
);

-- Índices
CREATE INDEX idx_perfil_etiquetas_perfil ON perfil_etiquetas(perfil_id);
CREATE INDEX idx_perfil_etiquetas_etiqueta ON perfil_etiquetas(etiqueta_id);
CREATE INDEX idx_perfil_etiquetas_contador ON perfil_etiquetas(contador DESC);

-- Trigger para actualizar uso_total de etiqueta
CREATE OR REPLACE FUNCTION actualizar_uso_total_etiqueta()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE etiquetas SET uso_total = uso_total + NEW.contador
        WHERE id = NEW.etiqueta_id;
    ELSIF (TG_OP = 'UPDATE') THEN
        UPDATE etiquetas SET uso_total = uso_total + (NEW.contador - OLD.contador)
        WHERE id = NEW.etiqueta_id;
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE etiquetas SET uso_total = uso_total - OLD.contador
        WHERE id = OLD.etiqueta_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_actualizar_uso_total_etiqueta
AFTER INSERT OR UPDATE OR DELETE ON perfil_etiquetas
FOR EACH ROW EXECUTE FUNCTION actualizar_uso_total_etiqueta();
```

---

### Tabla: `cursos`

**Propósito**: Catálogo de materias/cursos impartidos

```sql
CREATE TABLE cursos (
    id SERIAL PRIMARY KEY,
    
    -- Identificación
    nombre VARCHAR(255) NOT NULL,
    nombre_normalizado VARCHAR(255) UNIQUE NOT NULL,
    codigo VARCHAR(50),
    
    -- Clasificación
    departamento VARCHAR(100) DEFAULT 'Sistemas',
    nivel VARCHAR(50),  -- 'Licenciatura', 'Posgrado', etc.
    
    -- Estadísticas
    total_resenias INTEGER DEFAULT 0,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX idx_cursos_nombre_normalizado ON cursos(nombre_normalizado);
CREATE INDEX idx_cursos_departamento ON cursos(departamento);

-- Función para normalizar nombre de curso
CREATE OR REPLACE FUNCTION normalizar_curso(texto VARCHAR)
RETURNS VARCHAR AS $$
BEGIN
    -- Convierte "POO" → "programacion orientada a objetos" si existe mapeo
    -- Por ahora, solo normalización básica
    RETURN LOWER(TRIM(
        TRANSLATE(texto, 
            'ÁÉÍÓÚáéíóúÑñ', 
            'AEIOUaeiouNn'
        )
    ));
END;
$$ LANGUAGE plpgsql IMMUTABLE;
```

**Ejemplo de registros**:
```sql
INSERT INTO cursos (nombre, nombre_normalizado)
VALUES 
    ('Bases de Datos', 'bases de datos'),
    ('Programación Orientada a Objetos', 'programacion orientada a objetos'),
    ('POO', 'programacion orientada a objetos'),  -- Alias
    ('Algoritmos', 'algoritmos');
```

---

### Tabla: `resenias_metadata`

**Propósito**: Datos estructurados de cada reseña (sin comentario textual)

```sql
CREATE TABLE resenias_metadata (
    id SERIAL PRIMARY KEY,
    
    -- Relaciones
    profesor_id INTEGER NOT NULL REFERENCES profesores(id) ON DELETE CASCADE,
    curso_id INTEGER REFERENCES cursos(id) ON DELETE SET NULL,
    perfil_id INTEGER REFERENCES perfiles(id) ON DELETE SET NULL,  -- Asociar con snapshot
    
    -- Datos de la reseña
    fecha_resenia DATE NOT NULL,
    calidad_general DECIMAL(3, 2) CHECK (calidad_general >= 0 AND calidad_general <= 10),
    facilidad DECIMAL(3, 2) CHECK (facilidad >= 0 AND facilidad <= 10),
    
    -- Metadatos categóricos
    asistencia VARCHAR(50),  -- 'Obligatoria', 'No obligatoria'
    calificacion_recibida VARCHAR(10),  -- '10', 'MB', 'B', etc.
    nivel_interes VARCHAR(50),  -- 'Alto', 'Medio', 'Bajo'
    
    -- Referencia a MongoDB (vínculo con opinión textual)
    mongo_opinion_id VARCHAR(24) UNIQUE,  -- ObjectId de MongoDB
    
    -- Indicador de existencia de comentario
    tiene_comentario BOOLEAN DEFAULT FALSE,
    longitud_comentario INTEGER DEFAULT 0,
    
    -- Auditoría
    fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fuente VARCHAR(50) DEFAULT 'misprofesores.com'
);

-- Índices
CREATE INDEX idx_resenias_profesor ON resenias_metadata(profesor_id);
CREATE INDEX idx_resenias_curso ON resenias_metadata(curso_id);
CREATE INDEX idx_resenias_perfil ON resenias_metadata(perfil_id);
CREATE INDEX idx_resenias_fecha ON resenias_metadata(fecha_resenia DESC);
CREATE INDEX idx_resenias_mongo ON resenias_metadata(mongo_opinion_id);
CREATE INDEX idx_resenias_tiene_comentario ON resenias_metadata(tiene_comentario) WHERE tiene_comentario = TRUE;

-- Índice compuesto para búsquedas frecuentes
CREATE INDEX idx_resenias_profesor_fecha ON resenias_metadata(profesor_id, fecha_resenia DESC);
```

---

### Tabla: `resenia_etiquetas`

**Propósito**: Relación many-to-many entre reseñas y etiquetas

```sql
CREATE TABLE resenia_etiquetas (
    id SERIAL PRIMARY KEY,
    
    -- Relaciones
    resenia_id INTEGER NOT NULL REFERENCES resenias_metadata(id) ON DELETE CASCADE,
    etiqueta_id INTEGER NOT NULL REFERENCES etiquetas(id) ON DELETE CASCADE,
    
    -- Evitar duplicados
    UNIQUE(resenia_id, etiqueta_id)
);

-- Índices
CREATE INDEX idx_resenia_etiquetas_resenia ON resenia_etiquetas(resenia_id);
CREATE INDEX idx_resenia_etiquetas_etiqueta ON resenia_etiquetas(etiqueta_id);
```

---

### Tabla: `historial_scraping`

**Propósito**: Auditoría completa de ejecuciones del scraper

```sql
CREATE TABLE historial_scraping (
    id SERIAL PRIMARY KEY,
    
    -- Relación
    profesor_id INTEGER REFERENCES profesores(id) ON DELETE SET NULL,
    
    -- Información de ejecución
    estado VARCHAR(50) NOT NULL,  -- 'exito', 'error', 'parcial', 'cache_usado'
    resenias_encontradas INTEGER DEFAULT 0,
    resenias_nuevas INTEGER DEFAULT 0,
    resenias_actualizadas INTEGER DEFAULT 0,
    
    -- Errores
    mensaje_error TEXT,
    stack_trace TEXT,
    
    -- Rendimiento
    duracion_segundos INTEGER,
    url_procesada TEXT,
    
    -- Metadatos de caché
    cache_utilizado BOOLEAN DEFAULT FALSE,
    razon_rescraping TEXT,  -- 'cambio_detectado', 'forzado', 'primera_vez'
    
    -- Auditoría
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_origen INET
);

-- Índices
CREATE INDEX idx_historial_profesor ON historial_scraping(profesor_id);
CREATE INDEX idx_historial_timestamp ON historial_scraping(timestamp DESC);
CREATE INDEX idx_historial_estado ON historial_scraping(estado);
CREATE INDEX idx_historial_errores ON historial_scraping(estado) WHERE estado = 'error';
```

---

## 🍃 MongoDB: Esquema Detallado

### Nombre de Base de Datos: `sentiment_uam_nlp`

### Colección: `opiniones`

**Propósito**: Almacenar comentarios textuales con análisis de sentimiento

```javascript
// Ejemplo de opinión sin analizar (recién extraída)
{
    // Identificación (MongoDB ObjectId automático)
    "_id": ObjectId("507f1f77bcf86cd799439011"),
    
    // Referencias a PostgreSQL
    "profesor_id": 1,
    "profesor_nombre": "Josue Padilla",
    "profesor_slug": "josue-padilla-cuevas",
    "resenia_id": 123,  // ID de resenias_metadata
    
    // Contexto de la reseña
    "fecha_opinion": ISODate("2025-08-09T00:00:00Z"),
    "curso": "Bases de Datos",
    
    // Texto original
    "comentario": "Muy buen profesor, domina la materia y sabe transmitir su conocimiento...",
    "idioma": "es",
    "longitud_caracteres": 145,
    "longitud_palabras": 24,
    
    // Análisis de sentimiento general con BERT
    "sentimiento_general": {
        "analizado": false,  // true cuando BERT lo procese
        
        // Clasificación general basada en pesos
        "clasificacion": null,  // "positivo", "neutral", "negativo"
        
        // Pesos/scores del análisis BERT
        "pesos": {
            "positivo": null,   // Peso para sentimiento positivo (0.0 a 1.0)
            "negativo": null,   // Peso para sentimiento negativo (0.0 a 1.0)
            "neutro": null      // Peso para sentimiento neutro (0.0 a 1.0)
        },
        
        // Metadata del análisis general
        "confianza": null,  // Confianza de la clasificación (0 a 1)
        "modelo_version": "bert-base-spanish-sentiment-v1",
        "fecha_analisis": null,
        "tiempo_procesamiento_ms": null
    },
    
    // Categorización por dimensiones clave del profesor
    "categorizacion": {
        "analizado": false,  // true cuando el módulo de categorización lo procese
        
        // Dimensión 1: Calidad Didáctica
        // Evalúa: explicaciones, claridad, dominio del tema, recursos didácticos
        "calidad_didactica": {
            "valoracion": null,  // "POS", "NEG", "NEUTRO"
            "confianza": null,   // Confianza de la categorización (0 a 1)
            "palabras_clave": []  // Palabras/frases que influyeron en la decisión
        },
        
        // Dimensión 2: Método de Evaluación
        // Evalúa: exámenes, tareas, criterios de calificación, justicia
        "metodo_evaluacion": {
            "valoracion": null,  // "POS", "NEG", "NEUTRO"
            "confianza": null,   // Confianza de la categorización (0 a 1)
            "palabras_clave": []  // Palabras/frases que influyeron en la decisión
        },
        
        // Dimensión 3: Empatía
        // Evalúa: trato, disponibilidad, comprensión, apoyo al estudiante
        "empatia": {
            "valoracion": null,  // "POS", "NEG", "NEUTRO"
            "confianza": null,   // Confianza de la categorización (0 a 1)
            "palabras_clave": []  // Palabras/frases que influyeron en la decisión
        },
        
        // Metadata del análisis de categorización
        "modelo_version": "bert-category-classifier-v1",
        "fecha_analisis": null,
        "tiempo_procesamiento_ms": null
    },
    
    // Embeddings para búsqueda semántica (futuro)
    "embedding": null,  // Array de 768 floats (BERT base)
    
    // Auditoría
    "fecha_extraccion": ISODate("2025-11-08T10:30:00Z"),
    "fuente": "misprofesores.com",
    "version_scraper": "1.0.0"
}

// Ejemplo de opinión completamente procesada
{
    "_id": ObjectId("507f1f77bcf86cd799439012"),
    "profesor_id": 1,
    "profesor_nombre": "Josue Padilla",
    "profesor_slug": "josue-padilla-cuevas",
    "resenia_id": 124,
    "fecha_opinion": ISODate("2025-08-09T00:00:00Z"),
    "curso": "Bases de Datos",
    "comentario": "Muy buen profesor, domina la materia y sabe transmitir su conocimiento. La carga de trabajo es bastante: actividades, exámenes, proyecto final. Recomendado si quieres aprender bien.",
    "idioma": "es",
    "longitud_caracteres": 185,
    "longitud_palabras": 28,
    
    // Análisis de sentimiento general (procesado por Módulo 1)
    "sentimiento_general": {
        "analizado": true,
        "clasificacion": "positivo",  // Clasificación basada en pesos
        "pesos": {
            "positivo": 0.87,  // Mayor peso → clasificación positiva
            "negativo": 0.08,
            "neutro": 0.05
        },
        "confianza": 0.92,
        "modelo_version": "bert-base-spanish-sentiment-v1",
        "fecha_analisis": ISODate("2025-11-08T11:00:00Z"),
        "tiempo_procesamiento_ms": 234
    },
    
    // Categorización por dimensiones (procesado por Módulo 2)
    "categorizacion": {
        "analizado": true,
        "calidad_didactica": {
            "valoracion": "POS",
            "confianza": 0.89,
            "palabras_clave": ["domina la materia", "sabe transmitir", "aprender bien"]
        },
        "metodo_evaluacion": {
            "valoracion": "NEUTRO",
            "confianza": 0.65,
            "palabras_clave": ["carga de trabajo bastante", "actividades", "exámenes", "proyecto final"]
        },
        "empatia": {
            "valoracion": "POS",
            "confianza": 0.71,
            "palabras_clave": ["recomendado"]
        },
        "modelo_version": "bert-category-classifier-v1",
        "fecha_analisis": ISODate("2025-11-08T11:00:15Z"),
        "tiempo_procesamiento_ms": 412
    },
    
    "embedding": null,
    "fecha_extraccion": ISODate("2025-11-08T10:30:00Z"),
    "fuente": "misprofesores.com",
    "version_scraper": "1.0.0"
}
```

### Índices MongoDB

```javascript
// 1. Índice compuesto para búsquedas por profesor y fecha
db.opiniones.createIndex({ 
    "profesor_id": 1, 
    "fecha_opinion": -1 
});

// 2. Índice para búsqueda de opiniones pendientes de análisis
db.opiniones.createIndex({ 
    "sentimiento.analizado": 1 
});

// 3. Índice de clasificación de sentimiento
db.opiniones.createIndex({ 
    "sentimiento.clasificacion": 1,
    "sentimiento.puntuacion": -1
});

// 4. Índice full-text para búsqueda en comentarios
db.opiniones.createIndex({ 
    "comentario": "text", 
    "curso": "text" 
}, {
    weights: { comentario: 10, curso: 5 },
    default_language: "spanish",
    language_override: "idioma"
});

// 5. Índice por curso
db.opiniones.createIndex({ "curso": 1 });

// 6. Índice temporal
db.opiniones.createIndex({ "fecha_opinion": -1 });

// 7. Índice para vincular con PostgreSQL
db.opiniones.createIndex({ "resenia_id": 1 }, { unique: true, sparse: true });

// 8. Índice para embeddings (búsqueda vectorial - futuro)
// Requiere MongoDB Atlas o Milvus
db.opiniones.createIndex({ 
    "embedding": "vector" 
}, {
    name: "embedding_vector_index",
    type: "knnVector",
    dimensions: 768,
    similarity: "cosine"
});
```

### Validación de Esquema MongoDB

```javascript
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
                resenia_id: {
                    bsonType: ["int", "null"],
                    description: "ID de resenia_metadata en PostgreSQL"
                },
                comentario: {
                    bsonType: "string",
                    minLength: 1,
                    description: "Texto del comentario (requerido)"
                },
                idioma: {
                    enum: ["es", "en"],
                    description: "Idioma del comentario"
                },
                fecha_opinion: {
                    bsonType: "date",
                    description: "Fecha de la opinión (requerido)"
                },
                sentimiento_general: {
                    bsonType: ["object", "null"],
                    properties: {
                        analizado: { bsonType: "bool" },
                        clasificacion: {
                            enum: ["positivo", "neutral", "negativo", null]
                        },
                        pesos: {
                            bsonType: ["object", "null"],
                            properties: {
                                positivo: { bsonType: ["double", "null"], minimum: 0, maximum: 1 },
                                negativo: { bsonType: ["double", "null"], minimum: 0, maximum: 1 },
                                neutro: { bsonType: ["double", "null"], minimum: 0, maximum: 1 }
                            }
                        },
                        confianza: { bsonType: ["double", "null"], minimum: 0, maximum: 1 }
                    }
                },
                categorizacion: {
                    bsonType: ["object", "null"],
                    properties: {
                        analizado: { bsonType: "bool" },
                        calidad_didactica: {
                            bsonType: ["object", "null"],
                            properties: {
                                valoracion: { enum: ["POS", "NEG", "NEUTRO", null] },
                                confianza: { bsonType: ["double", "null"], minimum: 0, maximum: 1 },
                                palabras_clave: { bsonType: "array" }
                            }
                        },
                        metodo_evaluacion: {
                            bsonType: ["object", "null"],
                            properties: {
                                valoracion: { enum: ["POS", "NEG", "NEUTRO", null] },
                                confianza: { bsonType: ["double", "null"], minimum: 0, maximum: 1 },
                                palabras_clave: { bsonType: "array" }
                            }
                        },
                        empatia: {
                            bsonType: ["object", "null"],
                            properties: {
                                valoracion: { enum: ["POS", "NEG", "NEUTRO", null] },
                                confianza: { bsonType: ["double", "null"], minimum: 0, maximum: 1 },
                                palabras_clave: { bsonType: "array" }
                            }
                        }
                    }
                }
            }
        }
    }
});
```

---

## 🔗 Sincronización entre Bases de Datos

### Flujo de Persistencia después del Scraping

```
┌─────────────────────────────────────────────┐
│  1. Scraping exitoso (JSON generado)       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  2. PostgreSQL: Insertar/Actualizar        │
│     - Profesor (si no existe)               │
│     - Perfil (snapshot del día)             │
│     - Etiquetas del perfil                  │
│     - Historial de scraping                 │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  3. Para cada reseña:                       │
│     a) Insertar curso (si no existe)        │
│     b) Insertar resenia_metadata            │
│     c) Insertar etiquetas de reseña         │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  4. MongoDB: Insertar opinión               │
│     - Si comentario NO está vacío           │
│     - Generar ObjectId                      │
│     - Vincular con resenia_metadata         │
│     - sentimiento.analizado = false         │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  5. PostgreSQL: Actualizar vínculo          │
│     - resenia_metadata.mongo_opinion_id     │
│     - resenia_metadata.tiene_comentario     │
└─────────────────────────────────────────────┘
```

### Ejemplo de Código de Integración

```python
async def guardar_profesor_completo(data: dict) -> int:
    """
    Guarda un profesor completo en ambas bases de datos.
    
    Args:
        data: JSON del scraping (estructura conocida)
        
    Returns:
        ID del profesor en PostgreSQL
    """
    async with AsyncSession(pg_engine) as pg_session:
        try:
            # 1. Insertar/actualizar profesor
            nombre_limpio = limpiar_nombre_profesor(data['name'])
            slug = slugify(nombre_limpio)
            
            profesor = await pg_session.execute(
                select(Profesor).where(Profesor.slug == slug)
            )
            profesor = profesor.scalar_one_or_none()
            
            if not profesor:
                profesor = Profesor(
                    nombre_completo=data['name'],
                    nombre_limpio=nombre_limpio,
                    slug=slug,
                    url_misprofesores=data.get('url')
                )
                pg_session.add(profesor)
                await pg_session.flush()
            
            # 2. Insertar perfil (snapshot)
            perfil = Perfil(
                profesor_id=profesor.id,
                calidad_general=data['overall_quality'],
                dificultad=data['difficulty'],
                porcentaje_recomendacion=data['recommend_percent'],
                total_resenias_encontradas=len(data['reviews'])
            )
            pg_session.add(perfil)
            await pg_session.flush()
            
            # 3. Insertar etiquetas del perfil
            for tag in data['tags']:
                etiqueta = await obtener_o_crear_etiqueta(
                    pg_session, 
                    tag['label']
                )
                
                perfil_etiqueta = PerfilEtiqueta(
                    perfil_id=perfil.id,
                    etiqueta_id=etiqueta.id,
                    contador=tag['count'] or 0
                )
                pg_session.add(perfil_etiqueta)
            
            # 4. Procesar reseñas
            for review in data['reviews']:
                # a) Curso
                curso = None
                if review['course'] and review['course'] != '---':
                    curso = await obtener_o_crear_curso(
                        pg_session, 
                        review['course']
                    )
                
                # b) Metadata de reseña (PostgreSQL)
                resenia = ReseniaMetadata(
                    profesor_id=profesor.id,
                    curso_id=curso.id if curso else None,
                    perfil_id=perfil.id,
                    fecha_resenia=review['date'],
                    calidad_general=review['overall'],
                    facilidad=review['ease'],
                    asistencia=review['attendance'],
                    calificacion_recibida=review['grade_received'],
                    nivel_interes=review['interest'],
                    tiene_comentario=bool(review['comment']),
                    longitud_comentario=len(review['comment'])
                )
                pg_session.add(resenia)
                await pg_session.flush()
                
                # c) Etiquetas de reseña
                for tag_name in review['tags']:
                    etiqueta = await obtener_o_crear_etiqueta(
                        pg_session, 
                        tag_name
                    )
                    
                    resenia_etiqueta = ReseniaEtiqueta(
                        resenia_id=resenia.id,
                        etiqueta_id=etiqueta.id
                    )
                    pg_session.add(resenia_etiqueta)
                
                # d) Opinión textual (MongoDB) - solo si hay comentario
                if review['comment']:
                    mongo_result = await mongo_db.opiniones.insert_one({
                        'profesor_id': profesor.id,
                        'profesor_nombre': nombre_limpio,
                        'profesor_slug': slug,
                        'resenia_id': resenia.id,
                        'fecha_opinion': datetime.fromisoformat(review['date']),
                        'curso': review['course'],
                        'comentario': review['comment'],
                        'idioma': 'es',
                        'longitud_caracteres': len(review['comment']),
                        'longitud_palabras': len(review['comment'].split()),
                        'sentimiento': {
                            'analizado': False
                        },
                        'fecha_extraccion': datetime.utcnow(),
                        'fuente': 'misprofesores.com',
                        'version_scraper': '1.0.0'
                    })
                    
                    # e) Vincular MongoDB con PostgreSQL
                    resenia.mongo_opinion_id = str(mongo_result.inserted_id)
            
            # 5. Registrar en historial
            historial = HistorialScraping(
                profesor_id=profesor.id,
                estado='exito',
                resenias_encontradas=len(data['reviews']),
                cache_utilizado=data.get('cached', False),
                razon_rescraping='actualizacion_programada'
            )
            pg_session.add(historial)
            
            # Commit final
            await pg_session.commit()
            return profesor.id
            
        except Exception as e:
            await pg_session.rollback()
            # Registrar error en historial
            historial_error = HistorialScraping(
                estado='error',
                mensaje_error=str(e),
                stack_trace=traceback.format_exc()
            )
            pg_session.add(historial_error)
            await pg_session.commit()
            raise
```

---

## 📈 Vistas Materializadas para Dashboards

### Vista: Estadísticas por Profesor

```sql
CREATE MATERIALIZED VIEW stats_profesores AS
SELECT 
    p.id AS profesor_id,
    p.nombre_limpio,
    p.slug,
    
    -- Perfil más reciente
    perf_actual.calidad_general AS calidad_actual,
    perf_actual.dificultad AS dificultad_actual,
    perf_actual.porcentaje_recomendacion AS recomendacion_actual,
    
    -- Totales
    COUNT(DISTINCT r.id) AS total_resenias,
    COUNT(DISTINCT r.curso_id) AS total_cursos_impartidos,
    
    -- Promedios históricos
    AVG(r.calidad_general) AS promedio_calidad_historico,
    AVG(r.facilidad) AS promedio_facilidad_historico,
    
    -- Distribución de asistencia
    SUM(CASE WHEN r.asistencia = 'Obligatoria' THEN 1 ELSE 0 END) AS resenias_asistencia_obligatoria,
    SUM(CASE WHEN r.asistencia = 'No obligatoria' THEN 1 ELSE 0 END) AS resenias_asistencia_opcional,
    
    -- Rango de fechas
    MIN(r.fecha_resenia) AS primera_resenia,
    MAX(r.fecha_resenia) AS ultima_resenia,
    
    -- Etiquetas top 3
    (
        SELECT json_agg(json_build_object('etiqueta', e.etiqueta, 'count', pe.contador))
        FROM (
            SELECT etiqueta_id, contador
            FROM perfil_etiquetas
            WHERE perfil_id = perf_actual.id
            ORDER BY contador DESC
            LIMIT 3
        ) pe
        INNER JOIN etiquetas e ON pe.etiqueta_id = e.id
    ) AS top_etiquetas

FROM profesores p
LEFT JOIN perfiles_actuales perf_actual ON p.id = perf_actual.profesor_id
LEFT JOIN resenias_metadata r ON p.id = r.profesor_id
WHERE p.activo = TRUE
GROUP BY p.id, p.nombre_limpio, p.slug, perf_actual.id, 
         perf_actual.calidad_general, perf_actual.dificultad, 
         perf_actual.porcentaje_recomendacion;

-- Índice para búsqueda rápida
CREATE UNIQUE INDEX idx_stats_profesores_id ON stats_profesores(profesor_id);
CREATE INDEX idx_stats_profesores_calidad ON stats_profesores(calidad_actual DESC);

-- Refrescar automáticamente cada noche
CREATE OR REPLACE FUNCTION refresh_stats_profesores()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY stats_profesores;
END;
$$ LANGUAGE plpgsql;
```

---

## 🚀 Scripts de Inicialización

### Script 1: Crear estructura PostgreSQL

```sql
-- init_postgres.sql
-- Ejecutar: psql -U postgres -d sentiment_uam_db -f init_postgres.sql

-- Crear base de datos
CREATE DATABASE sentiment_uam_db
    WITH ENCODING 'UTF8'
    LC_COLLATE = 'es_MX.UTF-8'
    LC_CTYPE = 'es_MX.UTF-8'
    TEMPLATE template0;

\c sentiment_uam_db

-- Habilitar extensiones
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- Para búsqueda fuzzy

-- Crear todas las tablas (en orden de dependencias)
-- [Incluir aquí todas las definiciones CREATE TABLE anteriores]

-- Crear funciones auxiliares
-- [Incluir aquí todas las definiciones CREATE FUNCTION anteriores]

-- Crear vistas
-- [Incluir aquí todas las definiciones CREATE VIEW anteriores]

-- Datos iniciales (seed)
INSERT INTO etiquetas (etiqueta, etiqueta_normalizada, categoria) VALUES
    ('BRINDA APOYO', 'brinda apoyo', 'positivo'),
    ('CLASES EXCELENTES', 'clases excelentes', 'positivo'),
    ('TOMARÍA SU CLASE OTRA VEZ', 'tomaria su clase otra vez', 'positivo'),
    ('DA BUENA RETROALIMENTACIÓN', 'da buena retroalimentacion', 'positivo'),
    ('CALIFICA DURO', 'califica duro', 'negativo'),
    ('MUCHAS TAREAS', 'muchas tareas', 'carga_trabajo'),
    ('LOS EXÁMENES SON DIFÍCILES', 'los examenes son dificiles', 'negativo'),
    ('ASISTENCIA OBLIGATORIA', 'asistencia obligatoria', 'neutral'),
    ('INSPIRACIONAL', 'inspiracional', 'positivo'),
    ('RESPETADO POR LOS ESTUDIANTES', 'respetado por los estudiantes', 'positivo');

-- Mensaje de éxito
DO $$
BEGIN
    RAISE NOTICE 'Base de datos PostgreSQL inicializada correctamente';
    RAISE NOTICE 'Tablas creadas: %', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public');
END $$;
```

### Script 2: Inicializar MongoDB

```javascript
// init_mongo.js
// Ejecutar: mongosh sentiment_uam_nlp init_mongo.js

// Crear colección con validación
db.createCollection("opiniones", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["profesor_id", "comentario", "fecha_opinion", "fecha_extraccion"],
            properties: {
                profesor_id: { bsonType: "int" },
                resenia_id: { bsonType: ["int", "null"] },
                comentario: { bsonType: "string", minLength: 1 },
                idioma: { enum: ["es", "en"] },
                fecha_opinion: { bsonType: "date" },
                sentimiento: {
                    bsonType: "object",
                    properties: {
                        analizado: { bsonType: "bool" },
                        puntuacion: { 
                            bsonType: ["double", "null"],
                            minimum: -1,
                            maximum: 1
                        }
                    }
                }
            }
        }
    }
});

// Crear todos los índices
db.opiniones.createIndex({ "profesor_id": 1, "fecha_opinion": -1 });
db.opiniones.createIndex({ "sentimiento.analizado": 1 });
db.opiniones.createIndex({ "sentimiento.clasificacion": 1, "sentimiento.puntuacion": -1 });
db.opiniones.createIndex({ "comentario": "text", "curso": "text" }, {
    weights: { comentario: 10, curso: 5 },
    default_language: "spanish"
});
db.opiniones.createIndex({ "curso": 1 });
db.opiniones.createIndex({ "fecha_opinion": -1 });
db.opiniones.createIndex({ "resenia_id": 1 }, { unique: true, sparse: true });

print("MongoDB inicializado correctamente");
print("Colecciones:", db.getCollectionNames());
print("Índices en 'opiniones':", db.opiniones.getIndexes().length);
```

---

## 📊 Casos de Uso y Consultas Ejemplo

### Caso 1: Obtener profesores mejor calificados

```sql
SELECT 
    nombre_limpio,
    calidad_actual,
    recomendacion_actual,
    total_resenias,
    top_etiquetas
FROM stats_profesores
WHERE total_resenias >= 10  -- Mínimo 10 reseñas para confiabilidad
ORDER BY calidad_actual DESC, recomendacion_actual DESC
LIMIT 20;
```

### Caso 2: Opiniones positivas de un curso específico

```javascript
// MongoDB
db.opiniones.find({
    "curso": /bases de datos/i,
    "sentimiento.clasificacion": "positivo",
    "sentimiento.puntuacion": { $gte: 0.7 }
}).sort({ "sentimiento.puntuacion": -1 }).limit(10);
```

### Caso 3: Tendencia temporal de un profesor

```sql
SELECT 
    DATE_TRUNC('month', fecha_extraccion) AS mes,
    AVG(calidad_general) AS calidad_promedio,
    AVG(porcentaje_recomendacion) AS recomendacion_promedio,
    COUNT(*) AS snapshots
FROM perfiles
WHERE profesor_id = 1
GROUP BY DATE_TRUNC('month', fecha_extraccion)
ORDER BY mes DESC;
```

### Caso 4: Profesores con más comentarios negativos

```sql
SELECT 
    p.nombre_limpio,
    COUNT(r.id) AS total_resenias,
    SUM(CASE WHEN r.mongo_opinion_id IS NOT NULL THEN 1 ELSE 0 END) AS con_comentario,
    (
        SELECT COUNT(*)
        FROM opiniones o (via MongoDB connector o JOIN)
        WHERE o.profesor_id = p.id AND o.sentimiento.clasificacion = 'negativo'
    ) AS comentarios_negativos
FROM profesores p
INNER JOIN resenias_metadata r ON p.id = r.profesor_id
GROUP BY p.id, p.nombre_limpio
HAVING SUM(CASE WHEN r.mongo_opinion_id IS NOT NULL THEN 1 ELSE 0 END) >= 10
ORDER BY comentarios_negativos DESC;
```

---

## 🔧 Configuración de Conexión

### Variables de Entorno (.env)

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sentiment_uam_db
POSTGRES_USER=sentiment_admin
POSTGRES_PASSWORD=securepassword123

# MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB=sentiment_uam_nlp
MONGO_USER=sentiment_admin
MONGO_PASSWORD=securepassword123

# URLs de conexión
DATABASE_URL=postgresql+asyncpg://sentiment_admin:securepassword123@localhost:5432/sentiment_uam_db
MONGO_URL=mongodb://sentiment_admin:securepassword123@localhost:27017/sentiment_uam_nlp

# Scraper
HEADLESS=true
USER_AGENT=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36
```

---

## ✅ Checklist de Implementación

- [ ] **PostgreSQL**
  - [ ] Instalar PostgreSQL 15+
  - [ ] Crear base de datos `sentiment_uam_db`
  - [ ] Ejecutar script `init_postgres.sql`
  - [ ] Verificar creación de tablas (13 tablas esperadas)
  - [ ] Crear usuario `sentiment_admin` con permisos

- [ ] **MongoDB**
  - [ ] Instalar MongoDB 7.0+
  - [ ] Crear base de datos `sentiment_uam_nlp`
  - [ ] Ejecutar script `init_mongo.js`
  - [ ] Verificar índices (7 índices esperados)
  - [ ] Habilitar autenticación

- [ ] **Módulo de Persistencia**
  - [ ] Crear `src/db/__init__.py`
  - [ ] Implementar `src/db/postgres.py` (SQLAlchemy async)
  - [ ] Implementar `src/db/mongodb.py` (Motor async)
  - [ ] Implementar `src/db/models.py` (Modelos ORM)
  - [ ] Implementar `src/db/sync.py` (Lógica de sincronización)

- [ ] **Integración con Scraper**
  - [ ] Modificar `src/mp/scrape_prof.py`
  - [ ] Agregar llamada a `guardar_profesor_completo()`
  - [ ] Mantener persistencia JSON (auditoría)
  - [ ] Agregar logging de persistencia

- [ ] **Testing**
  - [ ] Scrapear 5 profesores de prueba
  - [ ] Verificar integridad en PostgreSQL
  - [ ] Verificar vínculo con MongoDB
  - [ ] Ejecutar consultas de validación

- [ ] **Documentación**
  - [ ] Actualizar README.md con setup de BD
  - [ ] Actualizar CHANGELOG.md (v1.1.0)
  - [ ] Crear guía de migración de datos

---

## 📚 Próximos Pasos después de Persistencia

1. **Worker de Análisis BERT** (v1.2.0)
   - Cargar modelo BERT español
   - Procesar opiniones pendientes
   - Actualizar campo `sentimiento` en MongoDB

2. **API REST con FastAPI** (v1.3.0)
   - Endpoints para consulta de profesores
   - Endpoints para estadísticas
   - Documentación OpenAPI

3. **Sistema de Jobs APScheduler** (v2.0.0)
   - Scraping incremental cada 6h
   - Análisis BERT cada hora
   - Actualización de vistas materializadas

---

**Fin del Documento**  
**Versión**: 1.1.0  
**Última actualización**: 2025-11-08
