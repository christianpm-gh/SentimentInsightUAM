# Changelog

Todos los cambios notables en SentimentInsightUAM se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

---

## Guía para Contribuidores

Este CHANGELOG documenta:
- ✅ **Características implementadas**: Funcionalidades completamente operativas
- 🚧 **En desarrollo**: Características parcialmente implementadas
- 📋 **Planificadas**: Próximas características según roadmap
- 🐛 **Correcciones**: Bugs resueltos y mejoras
- 🔧 **Cambios técnicos**: Refactorizaciones y optimizaciones

### Convención de Commits
| Prefijo | Uso |
|---------|-----|
| `feat:` | Nueva característica |
| `fix:` | Corrección de bug |
| `refactor:` | Refactorización sin cambio de funcionalidad |
| `perf:` | Mejora de rendimiento |
| `docs:` | Documentación |
| `test:` | Tests |
| `chore:` | Tareas de mantenimiento |

---

## [Unreleased]

### 📋 Planificado
- Worker de análisis de sentimiento con modelo BERT
- API REST con FastAPI
- Sistema de jobs programados con APScheduler
- Dashboard de visualización de datos
- Tests unitarios adicionales
- Migración de datos históricos JSON a bases de datos

---

## [1.2.1] - 2025-11-10

### 🐛 Corregido (Fixed)

- **Bug crítico de scraping: Solo extraía 5 reseñas por profesor**
  - Corregida indentación incorrecta en `src/mp/scrape_prof.py`
  - El código de guardado estaba dentro del bucle `for`, causando return prematuro
  - Ahora extrae todas las reseñas de todas las páginas correctamente
  - Ejemplo verificado: Esiquio Gutierrez extrae 153 reseñas (31 páginas) en lugar de 5
  - Regresión introducida en v1.2.0, funcionalidad restaurada de v1.0.0
  - **Impacto**: Todos los profesores scrapeados en v1.2.0 tienen datos incompletos

---

## [1.2.0] - 2025-11-09

### ✅ Añadido (Added)

#### Docker & Infraestructura
- **Soporte completo para Docker Compose**
  - Contenedor PostgreSQL 15-alpine con inicialización automática
  - Contenedor MongoDB 7.0 con creación automática de usuario
  - Red interna `sentiment_network` para comunicación entre servicios
  - Volúmenes persistentes para datos y configuración
  - Healthchecks automáticos para monitoreo de estado

- **Makefile con 11 comandos útiles**
  - `make docker-up/down` - Gestión de contenedores
  - `make db-status` - Verificación de estado de ambas BD
  - `make db-psql/mongo` - Conexión directa a shells de BD
  - `make docker-logs` - Visualización de logs
  - `make docker-clean` - Limpieza completa

#### Persistencia en Base de Datos
- **Módulos de base de datos** (`src/db/`)
  - `__init__.py` - Gestión de conexiones asíncronas (PostgreSQL + MongoDB)
  - `models.py` - 8 modelos ORM SQLAlchemy con type hints `Mapped[]`
  - `repository.py` - Lógica de persistencia dual con `guardar_profesor_completo()`

- **Integración con scraper**
  - Persistencia triple automática: HTML + JSON + Bases de Datos
  - Flag `DB_ENABLED` con import condicional para compatibilidad
  - Fallback graceful si BD no está disponible

- **Script de limpieza de bases de datos** (`scripts/clean_databases.py`)
  - Modos: interactivo, `--all`, `--postgres`, `--mongo`, `--verify`
  - Limpieza completa manteniendo esquemas e índices
  - Reinicio de secuencias de auto-increment

#### Tests de Integración
- `tests/test_database_integration.py` - Prueba de inserción, consulta y relaciones
- `tests/test_scrape_josue_padilla.py` - 5 pruebas comprehensivas de scraping

#### Documentación
- `docs/DOCKER_SETUP.md` - Guía completa de Docker (700+ líneas)
- Actualización de `README.md` con opción de instalación Docker
- Actualización de `docs/DATABASE_SETUP.md` con sección Docker

### 🔧 Cambiado (Changed)
- **Formato de persistencia**: De JSON a persistencia triple (HTML + JSON + BD)
- **Precisión de calificaciones**: DECIMAL(3,2) → DECIMAL(4,2) para soportar 10.0
- **Estructura de scripts**: Usuario MongoDB ahora se crea en JavaScript

### 🐛 Corregido (Fixed)
- **Error de autenticación MongoDB**: Usuario creado correctamente durante inicialización
- **DECIMAL precision overflow**: Calificaciones de 10.0 ahora funcionan
- **INET import error**: Movido a `sqlalchemy.dialects.postgresql`
- **Limpieza de nombres**: Función elimina sufijos institucionales correctamente

### 📊 Métricas
- Reducción de tiempo de setup: 93% (de ~15 min a ~1 min)
- Nuevos archivos creados: 8
- Líneas de documentación: ~1,500

---

## [1.1.1] - 2025-11-09

### ✅ Añadido (Added)

#### Infraestructura Docker
- **`docker-compose.yml`**: Configuración completa para desarrollo
  - PostgreSQL 15-alpine con healthcheck automático
  - MongoDB 7.0 con autenticación habilitada
  - Red aislada `sentiment_network`
  - Volúmenes persistentes para datos

- **`Makefile`**: 11 comandos útiles
  - `make help` - Ayuda con colores y categorización
  - `make docker-up/down` - Gestión de contenedores
  - `make db-status` - Verificación de estado
  - `make db-psql/mongo` - Shells interactivos

- **Scripts de configuración**
  - `scripts/setup_mongo_user.sh` - Script de creación de usuario MongoDB
  - `.env.docker` - Template de variables de entorno

#### Documentación
- `docs/DOCKER_SETUP.md` - Guía completa (700+ líneas)
  - Instalación de Docker por OS
  - Troubleshooting detallado
  - Comparativa Docker vs Manual

### 🏗️ Arquitectura de Contenedores
- Aislamiento total con contenedores separados
- Persistencia garantizada con volúmenes Docker
- Inicialización automática de scripts SQL/JS
- Healthchecks para verificación de disponibilidad

---

## [1.1.0] - 2025-11-08

### ✅ Añadido (Added)

#### Esquemas de Bases de Datos
- **PostgreSQL (`sentiment_uam_db`)**
  - 8 tablas principales con relaciones completas
  - 2 vistas (1 materializada para dashboards)
  - 4 funciones PL/pgSQL auxiliares
  - 3 triggers automáticos
  - 20+ índices optimizados
  - 21 etiquetas seed categorizadas

- **MongoDB (`sentiment_uam_nlp`)**
  - Colección `opiniones` con validación JSON Schema
  - 8 índices especializados
  - Preparado para embeddings vectoriales BERT

#### Scripts de Inicialización
- `scripts/init_postgres.sql` - Esquema PostgreSQL completo (400+ líneas)
- `scripts/init_mongo.js` - Configuración MongoDB (300+ líneas)

#### Documentación Técnica
- `docs/DATABASE_DESIGN.md` - Diseño completo de persistencia (3500+ líneas)
- `docs/DATABASE_SETUP.md` - Guía práctica de configuración (2000+ líneas)

---

## [1.0.0] - 2024-11-08

### ✅ Características Principales

#### Sistema de Scraping Completo
- **Extracción de Directorio UAM** (`src/uam/nombres_uam.py`)
  - Scraping del directorio oficial UAM Azcapotzalco
  - Carga dinámica mediante clics en "Ver más Profesorado"
  - Normalización de nombres con `slugify`
  - Extracción de 150+ profesores del Departamento de Sistemas

- **Scraping de Perfiles MisProfesores.com** (`src/mp/scrape_prof.py`)
  - Búsqueda normalizada sin acentos (case-insensitive)
  - Navegación directa por href
  - Extracción completa: calificaciones, etiquetas, reseñas
  - Paginación automática sin límite
  - Reintentos con backoff exponencial (tenacity)

#### Sistema de Caché Inteligente
- Detección automática de cambios (compara número de reseñas)
- Tolerancia de ±5 reseñas
- Opción `force=True` para forzar actualización

#### Persistencia Dual
- **HTML Original**: `data/outputs/html/{slug}.html` (auditoría)
- **JSON Estructurado**: `data/outputs/profesores/{slug}.json` (consumo)

#### Parser HTML Robusto (`src/mp/parser.py`)
- Extracción de perfil: calidad, dificultad, recomendación, etiquetas
- Extracción de reseñas: fecha, curso, calificaciones, comentario
- Conversión de fechas a ISO 8601
- Conteo automático de páginas

#### CLI Interactivo (`src/cli.py`)
- `nombres-uam` - Extrae lista de profesores UAM
- `prof` - Scrapea profesor (interactivo o directo)
- `scrape-all` - Scrapea todos con caché inteligente

### 🐛 Correcciones
- **AttributeError en Parser**: Pattern seguro en 7 ubicaciones
- **Timeouts en búsqueda**: Navegación directa por href
- **Paginación limitada**: URL directa sin límite artificial

### 📊 Métricas de Rendimiento
- Tiempo promedio por profesor: ~5-8 segundos
- Scraping completo (150 profesores): ~15-20 minutos
- Tasa de éxito: >95% con reintentos automáticos
- Uso de caché: ~80% en ejecuciones subsecuentes

---

## Historial de Versiones

| Versión | Fecha | Descripción |
|---------|-------|-------------|
| 1.2.1 | 2025-11-10 | Fix bug crítico de paginación |
| 1.2.0 | 2025-11-09 | Persistencia dual PostgreSQL + MongoDB |
| 1.1.1 | 2025-11-09 | Soporte Docker Compose |
| 1.1.0 | 2025-11-08 | Diseño de esquemas de BD |
| 1.0.0 | 2024-11-08 | Lanzamiento inicial |

---

**Última actualización**: 2025-11-26  
**Mantenedores**: Equipo SentimentInsightUAM - UAM Azcapotzalco  
**Licencia**: Open Source (Fines Educativos)
