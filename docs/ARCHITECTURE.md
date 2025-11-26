# Arquitectura del Sistema - SentimentInsightUAM

**Versión**: 1.2.1  
**Última actualización**: 2025-11-26

Este documento describe la arquitectura técnica del sistema SentimentInsightUAM, incluyendo componentes, flujos de datos y patrones de diseño.

---

## 📋 Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Componentes del Sistema](#componentes-del-sistema)
3. [Diagrama de Arquitectura](#diagrama-de-arquitectura)
4. [Flujo de Datos](#flujo-de-datos)
5. [Estructura del Proyecto](#estructura-del-proyecto)
6. [Módulos Principales](#módulos-principales)
7. [Persistencia de Datos](#persistencia-de-datos)
8. [Patrones de Diseño](#patrones-de-diseño)
9. [Roadmap Técnico](#roadmap-técnico)

---

## 🎯 Visión General

SentimentInsightUAM es un sistema de scraping y análisis de reseñas de profesores universitarios. El sistema extrae información del directorio oficial de la UAM Azcapotzalco y de perfiles en MisProfesores.com para análisis de sentimiento.

### Objetivos Técnicos
- **Extracción robusta** de datos mediante web scraping
- **Caché inteligente** para eficiencia y respeto a servidores
- **Persistencia triple** (HTML, JSON, Base de Datos)
- **Arquitectura asíncrona** para alto rendimiento
- **Extensibilidad** para futuras características (API, BERT, Dashboard)

---

## 🧩 Componentes del Sistema

### Capa de Extracción
| Componente | Archivo | Descripción |
|------------|---------|-------------|
| Navegador | `src/core/browser.py` | Context manager de Playwright |
| Scraper UAM | `src/uam/nombres_uam.py` | Extracción del directorio UAM |
| Scraper MP | `src/mp/scrape_prof.py` | Scraping de MisProfesores.com |
| Parser | `src/mp/parser.py` | Parsing HTML estructurado |

### Capa de Persistencia
| Componente | Archivo | Descripción |
|------------|---------|-------------|
| Modelos ORM | `src/db/models.py` | 8 modelos SQLAlchemy |
| Repositorio | `src/db/repository.py` | Lógica de persistencia dual |
| Conexiones | `src/db/__init__.py` | Gestión de conexiones async |

### Capa de Presentación
| Componente | Archivo | Descripción |
|------------|---------|-------------|
| CLI | `src/cli.py` | Interfaz de línea de comandos |

### Infraestructura
| Componente | Archivo | Descripción |
|------------|---------|-------------|
| Docker | `docker-compose.yml` | Orquestación de contenedores |
| Makefile | `Makefile` | Comandos de desarrollo |
| Scripts BD | `scripts/*.sql`, `scripts/*.js` | Inicialización de BD |

---

## 📊 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SentimentInsightUAM v1.2.1                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Capa de Presentación                          │   │
│  │  ┌───────────────────┐                                               │   │
│  │  │    CLI (cli.py)   │ ← Comandos: nombres-uam, prof, scrape-all    │   │
│  │  └─────────┬─────────┘                                               │   │
│  └────────────┼─────────────────────────────────────────────────────────┘   │
│               │                                                             │
│               ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Capa de Lógica de Negocio                     │   │
│  │                                                                       │   │
│  │  ┌───────────────────┐    ┌───────────────────┐                     │   │
│  │  │   Scraper UAM     │    │   Scraper MP      │                     │   │
│  │  │ (nombres_uam.py)  │    │ (scrape_prof.py)  │                     │   │
│  │  └─────────┬─────────┘    └─────────┬─────────┘                     │   │
│  │            │                        │                                │   │
│  │            │    ┌───────────────────┤                                │   │
│  │            │    │                   │                                │   │
│  │            ▼    ▼                   ▼                                │   │
│  │  ┌───────────────────┐    ┌───────────────────┐                     │   │
│  │  │  Browser Context  │    │      Parser       │                     │   │
│  │  │   (browser.py)    │    │   (parser.py)     │                     │   │
│  │  │   [Playwright]    │    │ [BeautifulSoup]   │                     │   │
│  │  └───────────────────┘    └───────────────────┘                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│               │                                                             │
│               ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Capa de Persistencia                          │   │
│  │                                                                       │   │
│  │  ┌───────────────┐   ┌───────────────┐   ┌───────────────────────┐  │   │
│  │  │   HTML Files  │   │  JSON Files   │   │   Base de Datos       │  │   │
│  │  │ data/outputs/ │   │ data/outputs/ │   │   (repository.py)     │  │   │
│  │  │    /html/     │   │ /profesores/  │   │                       │  │   │
│  │  └───────────────┘   └───────────────┘   └───────────┬───────────┘  │   │
│  │                                                       │              │   │
│  │                                          ┌────────────┴────────────┐ │   │
│  │                                          │                         │ │   │
│  │                                          ▼                         ▼ │   │
│  │                                ┌───────────────┐         ┌───────────┐│  │
│  │                                │  PostgreSQL   │         │  MongoDB  ││  │
│  │                                │  (Estructural)│         │(Opiniones)││  │
│  │                                │   8 tablas    │◄───────►│1 colección││  │
│  │                                └───────────────┘         └───────────┘│  │
│  │                                      mongo_opinion_id ←→ _id          │  │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌───────────────────────────────────────┐
                    │           Infraestructura             │
                    │                                       │
                    │  ┌─────────────────────────────────┐  │
                    │  │        Docker Compose           │  │
                    │  │  ┌──────────┐   ┌──────────┐   │  │
                    │  │  │ postgres │   │  mongodb │   │  │
                    │  │  │  :5432   │   │  :27017  │   │  │
                    │  │  └──────────┘   └──────────┘   │  │
                    │  │       sentiment_network        │  │
                    │  └─────────────────────────────────┘  │
                    └───────────────────────────────────────┘
```

---

## 🔄 Flujo de Datos

### Flujo 1: Extracción de Profesores UAM

```
┌─────────────────┐
│ CLI: nombres-uam│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│     get_prof_names()            │
│  (src/uam/nombres_uam.py)       │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  1. Navegar a Directorio UAM    │
│  2. Clic "Ver más Profesorado"  │
│  3. Parsear tarjetas de profs   │
│  4. Normalizar con slugify      │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ data/inputs/profesor_nombres.json│
│ [{name, slug, url}, ...]        │
└─────────────────────────────────┘
```

### Flujo 2: Scraping de Profesor Individual

```
┌─────────────────┐
│  CLI: prof      │
│  --name "Juan"  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│    find_and_scrape(prof_name)   │
│   (src/mp/scrape_prof.py)       │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  1. Verificar caché existente   │
│     └─ _get_cached_data()       │
└────────┬────────────────────────┘
         │
    ┌────┴────┐
    │         │
   Sí        No
    │         │
    ▼         ▼
┌────────┐ ┌──────────────────────┐
│Compare │ │ Buscar en sitio      │
│reviews │ │ MisProfesores.com    │
└───┬────┘ └──────────┬───────────┘
    │                 │
    ▼                 ▼
┌─────────────────────────────────┐
│  2. Extraer page_count()        │
│     └─ Calcular páginas         │
└────────┬────────────────────────┘
         │
    ┌────┴────┐
    │         │
  Igual    Diferente
    │         │
    ▼         ▼
┌────────┐ ┌──────────────────────┐
│Retorna │ │ 3. Scrapear completo │
│ caché  │ │    └─ Todas las pág  │
└────────┘ │    └─ parse_profile()│
           │    └─ parse_reviews()│
           └──────────┬───────────┘
                      │
                      ▼
           ┌──────────────────────┐
           │ 4. Persistencia      │
           │    ├─ _save_html()   │
           │    ├─ _save_json()   │
           │    └─ guardar_prof..()│
           └──────────┬───────────┘
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
    ┌─────────┐ ┌─────────┐ ┌──────────┐
    │  HTML   │ │  JSON   │ │PostgreSQL│
    │ archivo │ │ archivo │ │+ MongoDB │
    └─────────┘ └─────────┘ └──────────┘
```

### Flujo 3: Scraping Masivo

```
┌─────────────────┐
│ CLI: scrape-all │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  scrape_all_professors()        │
│  1. Cargar lista de profesores  │
│  2. Para cada profesor:         │
│     ├─ find_and_scrape()        │
│     ├─ Manejar errores          │
│     └─ Delay 2-4s               │
│  3. Generar resumen             │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ RESUMEN DE SCRAPING             │
│ ├─ Total procesados: 150        │
│ ├─ Scrapeados: 28               │
│ ├─ Cache: 119                   │
│ └─ Errores: 3                   │
└─────────────────────────────────┘
```

---

## 📁 Estructura del Proyecto

```
SentimentInsightUAM/
├── src/                          # Código fuente principal
│   ├── __init__.py
│   ├── cli.py                    # Interfaz de línea de comandos
│   ├── core/                     # Funcionalidades centrales
│   │   ├── __init__.py
│   │   └── browser.py            # Context manager Playwright
│   ├── db/                       # Módulos de base de datos
│   │   ├── __init__.py           # Gestión de conexiones
│   │   ├── models.py             # Modelos ORM SQLAlchemy
│   │   └── repository.py         # Lógica de persistencia
│   ├── mp/                       # Módulo MisProfesores
│   │   ├── __init__.py
│   │   ├── parser.py             # Parser HTML
│   │   └── scrape_prof.py        # Scraper con caché
│   ├── uam/                      # Módulo UAM
│   │   ├── __init__.py
│   │   └── nombres_uam.py        # Scraper directorio UAM
│   └── utils/                    # Utilidades
│       └── __init__.py
├── data/                         # Datos de entrada/salida
│   ├── inputs/
│   │   └── profesor_nombres.json # Lista de profesores
│   └── outputs/
│       ├── html/                 # HTML original (auditoría)
│       └── profesores/           # JSON estructurado
├── scripts/                      # Scripts de utilidad
│   ├── init_postgres.sql         # Esquema PostgreSQL
│   ├── init_mongo.js             # Configuración MongoDB
│   ├── clean_databases.py        # Limpieza de BD
│   └── verify_docker_setup.sh    # Verificación Docker
├── tests/                        # Tests
│   ├── test_database_integration.py
│   └── test_scrape_josue_padilla.py
├── docs/                         # Documentación
│   ├── ARCHITECTURE.md           # Este archivo
│   ├── TECHNICAL_DOCUMENTATION.md
│   ├── DATABASE_DESIGN.md
│   ├── DATABASE_SETUP.md
│   ├── DOCKER_SETUP.md
│   └── DEVELOPMENT_GUIDE.md
├── .github/                      # Configuración GitHub
│   ├── CONTRIBUTING.md
│   ├── COMMIT_CONVENTION.md
│   ├── BRANCH_NAMING.md
│   └── PULL_REQUEST_TEMPLATE.md
├── docker-compose.yml            # Orquestación Docker
├── Makefile                      # Comandos de desarrollo
├── requirements.txt              # Dependencias Python
├── .env.example                  # Variables de entorno ejemplo
├── README.md                     # Documentación principal
└── CHANGELOG.md                  # Historial de cambios
```

---

## 🔧 Módulos Principales

### `src/core/browser.py`
Context manager asíncrono para Playwright.

```python
# Uso típico
async with browser_ctx() as ctx:
    page = await ctx.new_page()
    await page.goto(url)
```

**Características:**
- User agent realista (Chrome 122)
- Modo headless configurable via `.env`
- Gestión automática de ciclo de vida
- Timeout configurado: 45s navegación

### `src/mp/scrape_prof.py`
Scraper principal con caché inteligente.

**Funciones principales:**
- `find_and_scrape(prof_name, force=False)` - Función principal
- `_get_cached_data(prof_name)` - Lectura de caché
- `_save_html(prof_name, html)` - Guardar HTML
- `_save_json(prof_name, data)` - Guardar JSON

**Características:**
- Detección automática de cambios (±5 reseñas)
- Navegación directa por href (evita timeouts)
- Paginación automática sin límite
- Reintentos con backoff exponencial (tenacity)

### `src/mp/parser.py`
Parser HTML especializado para MisProfesores.com.

**Funciones principales:**
- `parse_profile(html)` - Extrae perfil (calidad, dificultad, etiquetas)
- `parse_reviews(html)` - Extrae reseñas de una página
- `page_count(html)` - Calcula número de páginas

**Características:**
- Pattern seguro para elementos opcionales
- Conversión de fechas a ISO 8601
- Normalización de números (punto/coma)

### `src/db/repository.py`
Lógica de persistencia dual.

**Funciones principales:**
- `guardar_profesor_completo(datos, url_mp)` - Persistencia dual
- `limpiar_nombre_profesor(nombre)` - Normalización
- `obtener_o_crear_etiqueta(session, etiqueta)` - Catálogo
- `obtener_o_crear_curso(session, curso)` - Catálogo

**Características:**
- Transacciones con rollback automático
- Sincronización PostgreSQL ↔ MongoDB
- Registro en historial de scraping

---

## 💾 Persistencia de Datos

### Estrategia de Persistencia Triple

```
┌───────────────────────────────────────────────────────────────────┐
│                    Datos de Profesor                              │
└───────────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐
│   HTML (Audit)  │  │   JSON (Local)  │  │   Base de Datos (Query) │
├─────────────────┤  ├─────────────────┤  ├─────────────────────────┤
│ ✓ Re-parsing    │  │ ✓ Consumo local │  │ ✓ Consultas complejas   │
│ ✓ Debugging     │  │ ✓ Retrocompat.  │  │ ✓ Análisis estadístico  │
│ ✓ Auditoría     │  │ ✓ Respaldo      │  │ ✓ API REST (futuro)     │
└─────────────────┘  └─────────────────┘  └─────────────────────────┘
```

### Esquema PostgreSQL

```
profesores ──┬── perfiles ──── perfil_etiquetas ──── etiquetas
             │
             ├── resenias_metadata ──┬── resenia_etiquetas ──── etiquetas
             │                       │
             │                       └── cursos
             │
             └── historial_scraping
```

**Tablas principales:**
| Tabla | Propósito |
|-------|-----------|
| `profesores` | Catálogo maestro |
| `perfiles` | Snapshots temporales de métricas |
| `etiquetas` | Catálogo de tags |
| `cursos` | Catálogo de materias |
| `resenias_metadata` | Datos estructurados de reseñas |
| `historial_scraping` | Auditoría de ejecuciones |

### Esquema MongoDB

**Colección `opiniones`:**
```javascript
{
  "_id": ObjectId,
  "profesor_id": Number,      // FK a PostgreSQL
  "resenia_id": Number,       // FK a PostgreSQL
  "comentario": String,       // Texto completo
  "sentimiento": {            // Para BERT (futuro)
    "analizado": Boolean,
    "puntuacion": Number,
    "clasificacion": String
  }
}
```

### Sincronización entre BD

```
PostgreSQL                          MongoDB
┌─────────────────────┐             ┌─────────────────────┐
│ resenias_metadata   │             │     opiniones       │
├─────────────────────┤             ├─────────────────────┤
│ id: 123             │────────────▶│ resenia_id: 123     │
│ mongo_opinion_id:   │◀────────────│ _id: ObjectId(...)  │
│   ObjectId(...)     │             │                     │
└─────────────────────┘             └─────────────────────┘
```

---

## 🎨 Patrones de Diseño

### 1. Context Manager (Navegador)
```python
@asynccontextmanager
async def browser_ctx():
    browser = await playwright.chromium.launch()
    ctx = await browser.new_context()
    try:
        yield ctx
    finally:
        await ctx.close()
        await browser.close()
```

### 2. Repository Pattern (Persistencia)
```python
class ProfesorRepository:
    async def guardar(self, data):
        # Lógica de persistencia
    
    async def obtener_por_slug(self, slug):
        # Lógica de consulta
```

### 3. Factory Pattern (Modelos ORM)
```python
def obtener_o_crear_etiqueta(session, nombre):
    etiqueta = session.query(Etiqueta).filter_by(nombre=nombre).first()
    if not etiqueta:
        etiqueta = Etiqueta(nombre=nombre)
        session.add(etiqueta)
    return etiqueta
```

### 4. Retry Pattern (Tenacity)
```python
@retry(wait=wait_random_exponential(min=1, max=8), stop=stop_after_attempt(4))
async def fetch_with_retry(url):
    # Operación con reintentos automáticos
```

### 5. Cache Pattern (Scraper)
```python
def find_and_scrape(name, force=False):
    cached = _get_cached_data(name)
    if cached and not force and not has_changes(cached):
        return cached
    return scrape_fresh(name)
```

---

## 🚀 Roadmap Técnico

### Versión Actual: v1.2.1
- ✅ Scraping robusto con caché
- ✅ Persistencia triple (HTML + JSON + BD)
- ✅ Docker Compose para desarrollo
- ✅ Tests de integración

### Próximas Versiones

#### v1.3.0 - Análisis de Sentimiento
- [ ] Integración de modelo BERT español
- [ ] Worker asíncrono para procesamiento
- [ ] Análisis por aspectos
- [ ] Cache de análisis

#### v2.0.0 - API REST
- [ ] FastAPI con OpenAPI automático
- [ ] Endpoints para profesores, reseñas, estadísticas
- [ ] Autenticación JWT
- [ ] Paginación y filtros

#### v2.1.0 - Jobs Programados
- [ ] APScheduler para jobs
- [ ] Job incremental cada 6 horas
- [ ] Job nocturno masivo
- [ ] Monitoreo y alertas

#### v3.0.0 - Dashboard
- [ ] Frontend React/Vue
- [ ] Visualizaciones con gráficas
- [ ] Comparación entre profesores
- [ ] Búsqueda avanzada

---

## 📚 Referencias

- [Playwright Python](https://playwright.dev/python/)
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [Motor (MongoDB Async)](https://motor.readthedocs.io/)
- [FastAPI](https://fastapi.tiangolo.com/) (futuro)
- [Tenacity](https://tenacity.readthedocs.io/)

---

**Mantenedores**: Equipo SentimentInsightUAM - UAM Azcapotzalco
