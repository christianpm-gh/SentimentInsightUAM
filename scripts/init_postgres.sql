-- ============================================================================
-- Script de Inicialización de PostgreSQL para SentimentInsightUAM
-- ============================================================================
-- Base de datos: sentiment_uam_db
-- Versión: 1.1.0
-- Fecha: 2025-11-08
-- 
-- Descripción:
-- Este script crea la estructura completa de la base de datos PostgreSQL
-- para almacenar datos estructurados de profesores y reseñas.
-- 
-- Ejecución:
-- psql -U postgres -f scripts/init_postgres.sql
-- ============================================================================

-- NOTA: La base de datos es creada automáticamente por Docker
-- usando la variable POSTGRES_DB del docker-compose.yml
-- Ya estamos conectados a sentiment_uam_db por el entrypoint de Docker

-- ============================================================================
-- EXTENSIONES
-- ============================================================================

-- Extensión para remover acentos en búsquedas
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Extensión para búsqueda fuzzy (similitud de texto)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================================
-- FUNCIONES AUXILIARES
-- ============================================================================

-- Función para actualizar automáticamente updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Función para normalizar etiquetas (lowercase, sin acentos)
CREATE OR REPLACE FUNCTION normalizar_etiqueta(texto VARCHAR)
RETURNS VARCHAR AS $$
BEGIN
    RETURN LOWER(TRIM(
        unaccent(texto)
    ));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Función para normalizar nombres de curso
CREATE OR REPLACE FUNCTION normalizar_curso(texto VARCHAR)
RETURNS VARCHAR AS $$
BEGIN
    RETURN LOWER(TRIM(
        unaccent(texto)
    ));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- TABLAS
-- ============================================================================

-- Tabla: profesores
-- Catálogo maestro de profesores de la UAM Azcapotzalco
CREATE TABLE profesores (
    id SERIAL PRIMARY KEY,
    
    -- Identificación
    nombre_completo VARCHAR(255) NOT NULL,
    nombre_limpio VARCHAR(255) NOT NULL,
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

-- Índices de profesores
CREATE INDEX idx_profesores_slug ON profesores(slug);
CREATE INDEX idx_profesores_nombre_limpio ON profesores(nombre_limpio);
CREATE INDEX idx_profesores_departamento ON profesores(departamento);
CREATE INDEX idx_profesores_activo ON profesores(activo) WHERE activo = TRUE;

-- Trigger para updated_at en profesores
CREATE TRIGGER update_profesores_updated_at
BEFORE UPDATE ON profesores
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================

-- Tabla: perfiles
-- Snapshot temporal de métricas de cada profesor
CREATE TABLE perfiles (
    id SERIAL PRIMARY KEY,
    
    -- Relación
    profesor_id INTEGER NOT NULL REFERENCES profesores(id) ON DELETE CASCADE,
    
    -- Métricas principales
    calidad_general DECIMAL(4, 2) CHECK (calidad_general >= 0 AND calidad_general <= 10),
    dificultad DECIMAL(4, 2) CHECK (dificultad >= 0 AND dificultad <= 10),
    porcentaje_recomendacion DECIMAL(5, 2) CHECK (porcentaje_recomendacion >= 0 AND porcentaje_recomendacion <= 100),
    
    -- Metadatos de scraping
    total_resenias_encontradas INTEGER DEFAULT 0,
    scraping_exitoso BOOLEAN DEFAULT TRUE,
    fuente VARCHAR(50) DEFAULT 'misprofesores.com',
    
    -- Auditoría
    fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice único para evitar duplicados del mismo día (usando fecha sin hora)
CREATE UNIQUE INDEX idx_perfiles_profesor_fecha_unico 
    ON perfiles(profesor_id, CAST(fecha_extraccion AS DATE));

-- Índices de perfiles
CREATE INDEX idx_perfiles_profesor ON perfiles(profesor_id);
CREATE INDEX idx_perfiles_fecha ON perfiles(fecha_extraccion DESC);
CREATE INDEX idx_perfiles_calidad ON perfiles(calidad_general DESC);

-- ============================================================================

-- Tabla: etiquetas
-- Catálogo unificado de etiquetas (tags) del sistema
CREATE TABLE etiquetas (
    id SERIAL PRIMARY KEY,
    
    -- Etiqueta normalizada
    etiqueta VARCHAR(100) UNIQUE NOT NULL,
    etiqueta_normalizada VARCHAR(100) UNIQUE NOT NULL,
    
    -- Categorización
    categoria VARCHAR(50),
    
    -- Estadísticas
    uso_total INTEGER DEFAULT 0,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices de etiquetas
CREATE INDEX idx_etiquetas_etiqueta_normalizada ON etiquetas(etiqueta_normalizada);
CREATE INDEX idx_etiquetas_categoria ON etiquetas(categoria);
CREATE INDEX idx_etiquetas_uso_total ON etiquetas(uso_total DESC);

-- ============================================================================

-- Tabla: perfil_etiquetas
-- Relación many-to-many entre perfiles y etiquetas con contadores
CREATE TABLE perfil_etiquetas (
    id SERIAL PRIMARY KEY,
    
    -- Relaciones
    perfil_id INTEGER NOT NULL REFERENCES perfiles(id) ON DELETE CASCADE,
    etiqueta_id INTEGER NOT NULL REFERENCES etiquetas(id) ON DELETE CASCADE,
    
    -- Contador
    contador INTEGER DEFAULT 0,
    
    -- Evitar duplicados
    UNIQUE(perfil_id, etiqueta_id)
);

-- Índices de perfil_etiquetas
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

-- ============================================================================

-- Tabla: cursos
-- Catálogo de materias/cursos impartidos
CREATE TABLE cursos (
    id SERIAL PRIMARY KEY,
    
    -- Identificación
    nombre VARCHAR(255) NOT NULL,
    nombre_normalizado VARCHAR(255) UNIQUE NOT NULL,
    codigo VARCHAR(50),
    
    -- Clasificación
    departamento VARCHAR(100) DEFAULT 'Sistemas',
    nivel VARCHAR(50),
    
    -- Estadísticas
    total_resenias INTEGER DEFAULT 0,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices de cursos
CREATE INDEX idx_cursos_nombre_normalizado ON cursos(nombre_normalizado);
CREATE INDEX idx_cursos_departamento ON cursos(departamento);

-- ============================================================================

-- Tabla: resenias_metadata
-- Datos estructurados de cada reseña (sin comentario textual)
CREATE TABLE resenias_metadata (
    id SERIAL PRIMARY KEY,
    
    -- Relaciones
    profesor_id INTEGER NOT NULL REFERENCES profesores(id) ON DELETE CASCADE,
    curso_id INTEGER REFERENCES cursos(id) ON DELETE SET NULL,
    perfil_id INTEGER REFERENCES perfiles(id) ON DELETE SET NULL,
    
    -- Datos de la reseña
    fecha_resenia DATE NOT NULL,
    calidad_general DECIMAL(4, 2) CHECK (calidad_general >= 0 AND calidad_general <= 10),
    facilidad DECIMAL(4, 2) CHECK (facilidad >= 0 AND facilidad <= 10),
    
    -- Metadatos categóricos
    asistencia VARCHAR(50),
    calificacion_recibida VARCHAR(10),
    nivel_interes VARCHAR(50),
    
    -- Referencia a MongoDB
    mongo_opinion_id VARCHAR(24) UNIQUE,
    
    -- Indicador de comentario
    tiene_comentario BOOLEAN DEFAULT FALSE,
    longitud_comentario INTEGER DEFAULT 0,
    
    -- Auditoría
    fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fuente VARCHAR(50) DEFAULT 'misprofesores.com'
);

-- Índices de resenias_metadata
CREATE INDEX idx_resenias_profesor ON resenias_metadata(profesor_id);
CREATE INDEX idx_resenias_curso ON resenias_metadata(curso_id);
CREATE INDEX idx_resenias_perfil ON resenias_metadata(perfil_id);
CREATE INDEX idx_resenias_fecha ON resenias_metadata(fecha_resenia DESC);
CREATE INDEX idx_resenias_mongo ON resenias_metadata(mongo_opinion_id);
CREATE INDEX idx_resenias_tiene_comentario ON resenias_metadata(tiene_comentario) WHERE tiene_comentario = TRUE;
CREATE INDEX idx_resenias_profesor_fecha ON resenias_metadata(profesor_id, fecha_resenia DESC);

-- ============================================================================

-- Tabla: resenia_etiquetas
-- Relación many-to-many entre reseñas y etiquetas
CREATE TABLE resenia_etiquetas (
    id SERIAL PRIMARY KEY,
    
    -- Relaciones
    resenia_id INTEGER NOT NULL REFERENCES resenias_metadata(id) ON DELETE CASCADE,
    etiqueta_id INTEGER NOT NULL REFERENCES etiquetas(id) ON DELETE CASCADE,
    
    -- Evitar duplicados
    UNIQUE(resenia_id, etiqueta_id)
);

-- Índices de resenia_etiquetas
CREATE INDEX idx_resenia_etiquetas_resenia ON resenia_etiquetas(resenia_id);
CREATE INDEX idx_resenia_etiquetas_etiqueta ON resenia_etiquetas(etiqueta_id);

-- ============================================================================

-- Tabla: historial_scraping
-- Auditoría completa de ejecuciones del scraper
CREATE TABLE historial_scraping (
    id SERIAL PRIMARY KEY,
    
    -- Relación
    profesor_id INTEGER REFERENCES profesores(id) ON DELETE SET NULL,
    
    -- Información de ejecución
    estado VARCHAR(50) NOT NULL,
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
    razon_rescraping TEXT,
    
    -- Auditoría
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_origen INET
);

-- Índices de historial_scraping
CREATE INDEX idx_historial_profesor ON historial_scraping(profesor_id);
CREATE INDEX idx_historial_timestamp ON historial_scraping(timestamp DESC);
CREATE INDEX idx_historial_estado ON historial_scraping(estado);
CREATE INDEX idx_historial_errores ON historial_scraping(estado) WHERE estado = 'error';

-- ============================================================================
-- VISTAS
-- ============================================================================

-- Vista: perfiles_actuales
-- Perfil más reciente de cada profesor
CREATE OR REPLACE VIEW perfiles_actuales AS
SELECT DISTINCT ON (profesor_id)
    p.*,
    prof.nombre_limpio,
    prof.slug
FROM perfiles p
INNER JOIN profesores prof ON p.profesor_id = prof.id
ORDER BY profesor_id, fecha_extraccion DESC;

-- ============================================================================

-- Vista Materializada: stats_profesores
-- Estadísticas completas por profesor para dashboards
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

-- Índices para stats_profesores
CREATE UNIQUE INDEX idx_stats_profesores_id ON stats_profesores(profesor_id);
CREATE INDEX idx_stats_profesores_calidad ON stats_profesores(calidad_actual DESC);

-- Función para refrescar stats_profesores
CREATE OR REPLACE FUNCTION refresh_stats_profesores()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY stats_profesores;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- DATOS INICIALES (SEED)
-- ============================================================================

-- Insertar etiquetas comunes
INSERT INTO etiquetas (etiqueta, etiqueta_normalizada, categoria) VALUES
    ('BRINDA APOYO', 'brinda apoyo', 'positivo'),
    ('CLASES EXCELENTES', 'clases excelentes', 'positivo'),
    ('TOMARÍA SU CLASE OTRA VEZ', 'tomaria su clase otra vez', 'positivo'),
    ('DA BUENA RETROALIMENTACIÓN', 'da buena retroalimentacion', 'positivo'),
    ('ASPECTOS DE CALIFICACIÓN CLAROS', 'aspectos de calificacion claros', 'positivo'),
    ('RESPETADO POR LOS ESTUDIANTES', 'respetado por los estudiantes', 'positivo'),
    ('MUY CÓMICO', 'muy comico', 'positivo'),
    ('INSPIRACIONAL', 'inspiracional', 'positivo'),
    ('DA CRÉDITO EXTRA', 'da credito extra', 'positivo'),
    ('CALIFICA DURO', 'califica duro', 'negativo'),
    ('MUCHAS TAREAS', 'muchas tareas', 'carga_trabajo'),
    ('LOS EXÁMENES SON DIFÍCILES', 'los examenes son dificiles', 'negativo'),
    ('DEJA TRABAJOS LARGOS', 'deja trabajos largos', 'carga_trabajo'),
    ('MUCHOS EXÁMENES', 'muchos exámenes', 'carga_trabajo'),
    ('LAS CLASES SON LARGAS', 'las clases son largas', 'neutral'),
    ('ASISTENCIA OBLIGATORIA', 'asistencia obligatoria', 'neutral'),
    ('LA PARTICIPACIÓN IMPORTA', 'la participacion importa', 'neutral'),
    ('POCOS EXÁMENES', 'pocos examenes', 'positivo'),
    ('PREPÁRATE PARA LEER', 'preparate para leer', 'neutral'),
    ('MUCHOS PROYECTOS GRUPALES', 'muchos proyectos grupales', 'neutral'),
    ('BARCO', 'barco', 'positivo');

-- ============================================================================
-- VALIDACIÓN Y MENSAJE FINAL
-- ============================================================================

-- Contar tablas creadas
DO $$
DECLARE
    tabla_count INTEGER;
    vista_count INTEGER;
    funcion_count INTEGER;
    indice_count INTEGER;
    etiqueta_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO tabla_count FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    SELECT COUNT(*) INTO vista_count FROM information_schema.views WHERE table_schema = 'public';
    SELECT COUNT(*) INTO funcion_count FROM pg_proc WHERE pronamespace = 'public'::regnamespace;
    SELECT COUNT(*) INTO indice_count FROM pg_indexes WHERE schemaname = 'public';
    SELECT COUNT(*) INTO etiqueta_count FROM etiquetas;
    
    RAISE NOTICE '';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'INICIALIZACIÓN DE BASE DE DATOS COMPLETADA EXITOSAMENTE';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Base de datos: sentiment_uam_db';
    RAISE NOTICE 'Versión: 1.1.0';
    RAISE NOTICE 'Fecha: %', CURRENT_TIMESTAMP;
    RAISE NOTICE '';
    RAISE NOTICE 'Estadísticas:';
    RAISE NOTICE '  - Tablas creadas: %', tabla_count;
    RAISE NOTICE '  - Vistas creadas: %', vista_count;
    RAISE NOTICE '  - Funciones creadas: %', funcion_count;
    RAISE NOTICE '  - Índices creados: %', indice_count;
    RAISE NOTICE '  - Etiquetas iniciales: %', etiqueta_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Tablas principales:';
    RAISE NOTICE '  1. profesores';
    RAISE NOTICE '  2. perfiles';
    RAISE NOTICE '  3. etiquetas';
    RAISE NOTICE '  4. perfil_etiquetas';
    RAISE NOTICE '  5. cursos';
    RAISE NOTICE '  6. resenias_metadata';
    RAISE NOTICE '  7. resenia_etiquetas';
    RAISE NOTICE '  8. historial_scraping';
    RAISE NOTICE '';
    RAISE NOTICE 'La base de datos está lista para recibir datos del scraper.';
    RAISE NOTICE '============================================================================';
END $$;
