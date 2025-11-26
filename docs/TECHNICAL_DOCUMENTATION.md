# Documentación Técnica - SentimentInsightUAM

## Tabla de Contenidos
1. [Extracción de Nombres del Directorio UAM](#1-extracción-de-nombres-del-directorio-uam)
2. [Parser y Evolución de la Implementación](#2-parser-y-evolución-de-la-implementación)
3. [Scraper de Profesores y CLI](#3-scraper-de-profesores-y-cli)
4. [Propuesta de Esquemas de Bases de Datos](#4-propuesta-de-esquemas-de-bases-de-datos)
5. [Propuesta de API REST](#5-propuesta-de-api-rest)
6. [Propuesta de Sistema de Jobs Programados](#6-propuesta-de-sistema-de-jobs-programados)

---

## 1. Extracción de Nombres del Directorio UAM

### Contexto
El **Departamento de Sistemas de la UAM Azcapotzalco** (Universidad Autónoma Metropolitana, Unidad Azcapotzalco) mantiene un directorio oficial en línea donde se listan todos los profesores de la institución. Este directorio es la fuente primaria de datos para nuestro sistema.

### Implementación (`src/uam/nombres_uam.py`)

#### URL Base
```python
UAM_DIR = "https://sistemas.azc.uam.mx/Somos/Directorio/"
```

#### Proceso de Extracción

**1. Navegación Inicial**
- Se utiliza Playwright con un contexto de navegador configurado
- Se navega a la página del directorio con timeout de 45 segundos
- Se espera a que el DOM se cargue completamente

**2. Carga Dinámica de Contenido**
El directorio implementa paginación dinámica con un botón "Ver más Profesorado". El scraper:
```python
while True:
    try:
        boton = await page.wait_for_selector(
            "span:has-text('Ver más Profesorado')", 
            timeout=3000
        )
        await boton.click()
        await page.wait_for_timeout(700)  # Delay entre clics
    except PlaywrightTimeoutError:
        # No hay más profesores que cargar
        break
```

**3. Parsing del HTML**
Una vez cargado todo el contenido:
- Se busca la sección con encabezado "Profesorado"
- Se extraen todas las tarjetas de profesores (elementos `<a>` con clase `svelte`)
- Para cada tarjeta se extrae:
  - **Nombre** (elemento `<h4>`)
  - **Apellido** (elemento `<h5>`)
  - **Slug** (versión normalizada del nombre usando `slugify`)
  - **URL** completa del perfil

**4. Salida de Datos**
```json
[
  {
    "name": "Juan Pérez García",
    "slug": "juan-perez-garcia",
    "url": "https://sistemas.azc.uam.mx/profesor/123"
  }
]
```

#### Ventajas de este Enfoque
- ✅ Extracción completa y automática
- ✅ Manejo robusto de contenido dinámico
- ✅ Normalización de nombres para búsquedas posteriores
- ✅ Captura de errores con timeout específico

---

## 2. Parser y Evolución de la Implementación

### Módulo: `src/mp/parser.py`

El parser es el componente central que transforma HTML crudo de MisProfesores.com en datos estructurados.

### 2.1 Funciones Auxiliares

#### `_num(txt: str) -> Optional[float]`
Extrae números de texto que puede contener símbolos y formatos diversos:
- Maneja números decimales con punto o coma
- Retorna `None` si no encuentra números
- **Ejemplo**: `"Calidad: 9.5"` → `9.5`

#### `_date_ddMonYYYY(s: str) -> Optional[str]`
Convierte fechas del formato español a ISO 8601:
- **Entrada**: `"15/Ene/2024"`
- **Salida**: `"2024-01-15"`
- Usa diccionario de meses en español

### 2.2 Parser de Perfil (`parse_profile`)

#### Información Extraída

**Calificaciones Principales:**
```python
{
    "name": "Nombre del Profesor",
    "overall_quality": 9.5,      # Calificación general
    "difficulty": 7.2,           # Nivel de dificultad
    "recommend_percent": 95.0,   # % que lo recomiendan
    "tags": [...]                # Etiquetas frecuentes
}
```

**Proceso de Extracción:**
1. Busca el contenedor `.rating-breakdown`
2. Extrae calificaciones de elementos con clase `.grade`
3. Parsea etiquetas con formato `"ETIQUETA (contador)"`
4. Maneja casos donde no hay datos disponibles

#### Evolución: Problema del AttributeError

**Problema Inicial:**
```python
# ❌ Patrón problemático
course = (td_c.select_one(".name .response") or "").get_text(strip=True)
```

Cuando `select_one()` retornaba `None`, el operador `or ""` convertía a string, causando:
```
AttributeError: 'str' object has no attribute 'get_text'
```

**Solución Implementada:**
```python
# ✅ Patrón correcto
course_elem = td_c.select_one(".name .response")
course = course_elem.get_text(strip=True) if course_elem else None
```

Esta corrección se aplicó en **7 lugares diferentes** del parser.

### 2.3 Parser de Reseñas (`parse_reviews`)

#### Estructura de Datos
```python
{
    "date": "2024-01-15",
    "course": "Estructura de Datos",
    "overall": 10.0,
    "ease": 8.0,
    "attendance": "Obligatoria",
    "grade_received": "10",
    "interest": "Alta",
    "tags": ["BUENA ONDA", "ACCESIBLE"],
    "comment": "Excelente profesor, explica muy bien..."
}
```

#### Proceso de Extracción

**1. Localización de Filas**
```python
rows = s.select("div.rating-filter.togglable table.tftable tr")[1:]  # Salta header
```

**2. Por Cada Reseña:**
- **Fecha**: Extrae y convierte a ISO 8601
- **Calificaciones**: Itera sobre contenedores `.descriptor-container`
- **Metadatos**: Curso, asistencia, calificación recibida, interés
- **Comentario**: Texto libre del estudiante
- **Etiquetas**: Lista de descriptores aplicados

**3. Normalización**
- Todos los números se convierten a `float`
- Strings vacíos se convierten a `None`
- Fechas siempre en formato ISO

### 2.4 Conteo de Páginas (`page_count`)

Determina cuántas páginas de reseñas existen:

**Método Principal:**
```python
# Extrae contador total (ej: "125 reseñas")
# Calcula: ceil(125 / 5) = 25 páginas
n_reviews = _num(cnt.get_text())
pages = max(1, math.ceil(n_reviews / 5))
```

**Fallback:**
```python
# Si no hay contador, busca número máximo en paginación
nums = [int(m.group()) for a in s.select("ul.pagination li a") ...]
return max(nums) if nums else 1
```

---

## 3. Scraper de Profesores y CLI

### 3.1 Módulo: `src/mp/scrape_prof.py`

#### Características Principales

**1. Caché Inteligente**
El scraper implementa un sistema de caché que detecta automáticamente si un profesor necesita actualizarse:

```python
def _get_cached_data(prof_name: str) -> Optional[Dict[str, Any]]:
    """
    Busca datos cacheados del profesor.
    Retorna None si no existe o está corrupto.
    """
    slug = slugify(prof_name)
    json_file = JSON_OUTPUT_DIR / f"{slug}.json"
    
    if json_file.exists():
        return json.loads(json_file.read_text(encoding="utf-8"))
    return None
```

**2. Detección de Cambios**
Compara el número de reseñas actual con el cacheado:

```python
# Calcular número esperado de reseñas
expected_reviews = pages * 5  # 5 reseñas por página

if cached_data and not force:
    cached_reviews_count = len(cached_data.get("reviews", []))
    
    # Tolerancia de ±5 reseñas
    if abs(cached_reviews_count - expected_reviews) <= 5:
        print(f"✓ Caché vigente para {prof_name}")
        return cached_data  # Retorna caché
    else:
        print(f"✓ Detectados cambios: {cached_reviews_count} → ~{expected_reviews}")
        # Continúa con scraping
```

**3. Persistencia Dual**

El sistema guarda dos versiones de cada scraping:

**HTML Original** (`data/outputs/html/nombre-profesor.html`):
```python
def _save_html(prof_name: str, html: str) -> Path:
    """Guarda HTML para auditoría y re-parsing offline"""
    slug = slugify(prof_name)
    html_file = HTML_OUTPUT_DIR / f"{slug}.html"
    html_file.write_text(html, encoding="utf-8")
    return html_file
```

**JSON Estructurado** (`data/outputs/profesores/nombre-profesor.json`):
```python
def _save_json(prof_name: str, data: Dict[str, Any]) -> Path:
    """Guarda datos estructurados para consumo directo"""
    slug = slugify(prof_name)
    json_file = JSON_OUTPUT_DIR / f"{slug}.json"
    json_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), 
        encoding="utf-8"
    )
    return json_file
```

**Ventajas de la persistencia dual:**
- ✅ HTML permite re-parsing sin re-scraping
- ✅ JSON listo para consumo por aplicaciones
- ✅ Auditoría completa del proceso
- ✅ Debugging facilitado
- ✅ Análisis offline sin conexión

#### Flujo de Ejecución con Caché

```
┌─────────────────────────────────┐
│  find_and_scrape(prof_name)     │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  ¿Existe caché?                 │
│  _get_cached_data()             │
└────────┬────────────────────────┘
         │
    ┌────┴────┐
    │         │
   Sí        No
    │         │
    ▼         ▼
┌────────┐ ┌──────────────────────┐
│ Caché  │ │ Navegar a perfil     │
│ existe │ │ Extraer page_count() │
└───┬────┘ └─────────┬────────────┘
    │                │
    ▼                ▼
┌────────────────────────────────┐
│ Comparar número de reseñas     │
│ cached vs actual               │
└────────┬───────────────────────┘
         │
    ┌────┴────┐
    │         │
  Igual    Diferente
    │         │
    ▼         ▼
┌────────┐ ┌──────────────────────┐
│Retornar│ │ Scrapear completo    │
│ caché  │ │ Guardar HTML + JSON  │
└────────┘ └──────────────────────┘
```

#### Evolución de la Búsqueda

**Versión 1 (Inicial):**
```python
# Problema: Timeouts frecuentes
await page.get_by_role("textbox").fill(name)
await page.wait_for_timeout(1200)
row = page.get_by_role("link", name=name).first
await row.click()
```

**Versión 2 (Con normalización):**
```python
# Mejora: Añade Enter y espera networkidle
await search.fill(name)
await page.keyboard.press("Enter")
await page.wait_for_load_state("networkidle")  # ⚠️ Puede ser lento
```

**Versión 3 (Actual - Navegación por href):**
```python
# ✅ Óptimo: Navega directamente sin clic
def _norm(s: str) -> str:
    """Elimina acentos y normaliza espacios"""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()

# Busca coincidencia exacta normalizada
href = await cands.nth(idx).get_attribute("href")
if href.startswith("/"):
    href = f"{BASE}{href}"

# Navega directamente y espera contenedores específicos
await page.goto(href, wait_until="domcontentloaded", timeout=45000)
await page.wait_for_selector(
    "div.rating-breakdown, div.rating-filter.togglable", 
    timeout=30000
)
```

**Ventajas:**
- ✅ Evita problemas de scroll y clic
- ✅ No depende de `networkidle` (más rápido)
- ✅ Esperas específicas de contenido
- ✅ Matching robusto sin acentos

#### Paginación Mejorada

**Problema Inicial:**
```python
# Limitado a 9 páginas, hace clic en botones
for n in range(2, 9):
    if not await page.get_by_role("link", name=str(n)).count():
        break
    await page.get_by_role("link", name=str(n)).click()
```

**Solución Actual:**
```python
# Usa page_count() y navega por URL
pages = page_count(html)
for p in range(1, pages + 1):
    url = profile_url if p == 1 else f"{profile_url}?pag={p}"
    if p > 1:
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_selector("div.rating-filter.togglable table.tftable")
    all_reviews += parse_reviews(html)
```

**Ventajas:**
- ✅ Sin límite artificial de páginas
- ✅ Navegación directa más confiable
- ✅ Espera explícita de tabla antes de parsear

#### Reintentos con Backoff

```python
from tenacity import retry, wait_random_exponential, stop_after_attempt

@retry(wait=wait_random_exponential(min=1, max=8), stop=stop_after_attempt(4))
async def fetch_prof_html(ctx, prof_url: str) -> str:
    # Intenta hasta 4 veces con esperas exponenciales
```

### 3.2 CLI (`src/cli.py`)

#### Comandos Disponibles

**1. Extraer nombres de UAM**
```bash
python -m src.cli nombres-uam
```
- Ejecuta `get_prof_names()`
- Imprime JSON a stdout
- Se puede redirigir a archivo

**2. Scrapear profesor (modo interactivo)**
```bash
python -m src.cli prof
```
- Carga lista desde `data/inputs/profesor_nombres.json`
- Si no existe, la obtiene automáticamente de UAM
- Muestra menú numerado en columnas (4 por fila)
- Solicita selección al usuario
- Scrapea y muestra resultado

**3. Scrapear profesor (modo directo)**
```bash
python -m src.cli prof --name "Nombre Completo"
```
- Búsqueda directa sin menú
- Útil para automatización

**4. Scrapear todos los profesores (modo masivo)**
```bash
python -m src.cli scrape-all
```
- Scrapea automáticamente todos los profesores del directorio UAM
- Implementa caché inteligente por profesor
- Solo re-scrapea si detecta cambios en el número de reseñas
- Aplica delays entre requests para evitar bloqueos
- Muestra progreso en tiempo real
- Genera resumen final con estadísticas

**Características del Scraping Masivo:**

1. **Detección de Cambios Automática**
   ```python
   # Para cada profesor:
   # 1. Verifica si existe caché
   # 2. Si existe, compara número de reseñas
   # 3. Solo scrapea si hay diferencias
   cached_reviews = len(cached_data.get("reviews", []))
   current_reviews = page_count(html) * 5
   
   if abs(cached_reviews - current_reviews) <= 5:
       # Usa caché (tolerancia de 5 reseñas)
       return cached_data
   ```

2. **Rate Limiting Inteligente**
   ```python
   # Delays variables entre profesores (2-4 segundos)
   delay = 2 + (2 * (idx % 3))
   await asyncio.sleep(delay)
   ```

3. **Manejo de Errores Robusto**
   - Captura excepciones por profesor individual
   - Continúa con el siguiente en caso de error
   - No interrumpe el proceso completo
   - Registra errores en el resumen final

4. **Salida del Comando**
   ```
   Iniciando scraping de 150 profesores...
   ================================================================================
   
   [1/150] Procesando: Juan Perez Garcia
     -> Scrapeado exitosamente (47 reseñas)
     -> Esperando 2s antes del siguiente...
   
   [2/150] Procesando: Maria Lopez Hernandez
     -> Cache vigente (32 reseñas)
     -> Esperando 4s antes del siguiente...
   
   ...
   
   ================================================================================
   RESUMEN DE SCRAPING
   ================================================================================
   Total profesores procesados: 150
   Scrapeados exitosamente: 28
   Obtenidos de cache: 119
   Errores: 3
   ================================================================================
   ```

5. **Integración con Sistema Existente**
   - Reutiliza `find_and_scrape()` con toda su lógica de caché
   - Compatible con sistema de reintentos (tenacity)
   - Guarda HTML y JSON automáticamente
   - No requiere configuración adicional

6. **Prevención de Bloqueos**
   - Delays variables entre profesores evitan patrones detectables
   - Backoff exponencial en caso de errores (via tenacity)
   - User agent realista configurado en browser_ctx()
   - Timeouts apropiados para cada operación

#### Flujo de Datos

```
┌─────────────────────┐
│   nombres-uam       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────┐
│ data/inputs/                    │
│   profesor_nombres.json         │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────┐
│   prof (CLI)        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ find_and_scrape()   │
│   - Busca           │
│   - Navega          │
│   - Parsea          │
│   - Pagina          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────┐
│ data/outputs/profesores/        │
│   Nombre_Profesor.json          │
└─────────────────────────────────┘
```

---

## 4. Propuesta de Esquemas de Bases de Datos

### 4.1 PostgreSQL (Datos Estructurados)

#### Esquema Relacional

```sql
-- Tabla: profesores
CREATE TABLE profesores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    url_directorio_uam TEXT,
    url_misprofesores TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_profesores_slug ON profesores(slug);
CREATE INDEX idx_profesores_nombre ON profesores(nombre);

-- Tabla: perfiles (snapshot temporal de métricas)
CREATE TABLE perfiles (
    id SERIAL PRIMARY KEY,
    profesor_id INTEGER REFERENCES profesores(id) ON DELETE CASCADE,
    calidad_general DECIMAL(3, 2),        -- 0.00 a 10.00
    dificultad DECIMAL(3, 2),             -- 0.00 a 10.00
    porcentaje_recomendacion DECIMAL(5, 2), -- 0.00 a 100.00
    fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_profesor FOREIGN KEY (profesor_id) 
        REFERENCES profesores(id)
);

CREATE INDEX idx_perfiles_profesor ON perfiles(profesor_id);
CREATE INDEX idx_perfiles_fecha ON perfiles(fecha_extraccion);

-- Tabla: etiquetas (catálogo)
CREATE TABLE etiquetas (
    id SERIAL PRIMARY KEY,
    etiqueta VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_etiquetas_nombre ON etiquetas(etiqueta);

-- Tabla: perfil_etiquetas (relación many-to-many con contador)
CREATE TABLE perfil_etiquetas (
    id SERIAL PRIMARY KEY,
    perfil_id INTEGER REFERENCES perfiles(id) ON DELETE CASCADE,
    etiqueta_id INTEGER REFERENCES etiquetas(id) ON DELETE CASCADE,
    contador INTEGER DEFAULT 0,
    UNIQUE(perfil_id, etiqueta_id)
);

CREATE INDEX idx_perfil_etiquetas_perfil ON perfil_etiquetas(perfil_id);
CREATE INDEX idx_perfil_etiquetas_etiqueta ON perfil_etiquetas(etiqueta_id);

-- Tabla: cursos (catálogo de materias)
CREATE TABLE cursos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    codigo VARCHAR(50),
    departamento VARCHAR(100),
    UNIQUE(nombre, departamento)
);

CREATE INDEX idx_cursos_nombre ON cursos(nombre);

-- Tabla: resenias_metadata (solo datos estructurados)
CREATE TABLE resenias_metadata (
    id SERIAL PRIMARY KEY,
    profesor_id INTEGER REFERENCES profesores(id) ON DELETE CASCADE,
    curso_id INTEGER REFERENCES cursos(id) ON DELETE SET NULL,
    fecha_resenia DATE,
    calidad_general DECIMAL(3, 2),
    facilidad DECIMAL(3, 2),
    asistencia VARCHAR(50),        -- Obligatoria, No obligatoria, etc.
    calificacion_recibida VARCHAR(10), -- 10, 9, MB, etc.
    nivel_interes VARCHAR(50),     -- Alta, Media, Baja
    mongo_opinion_id VARCHAR(24),  -- Referencia a MongoDB ObjectId
    fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_profesor_resenia FOREIGN KEY (profesor_id) 
        REFERENCES profesores(id),
    CONSTRAINT fk_curso_resenia FOREIGN KEY (curso_id) 
        REFERENCES cursos(id)
);

CREATE INDEX idx_resenias_profesor ON resenias_metadata(profesor_id);
CREATE INDEX idx_resenias_curso ON resenias_metadata(curso_id);
CREATE INDEX idx_resenias_fecha ON resenias_metadata(fecha_resenia);
CREATE INDEX idx_resenias_mongo ON resenias_metadata(mongo_opinion_id);

-- Tabla: resenia_etiquetas
CREATE TABLE resenia_etiquetas (
    id SERIAL PRIMARY KEY,
    resenia_id INTEGER REFERENCES resenias_metadata(id) ON DELETE CASCADE,
    etiqueta_id INTEGER REFERENCES etiquetas(id) ON DELETE CASCADE,
    UNIQUE(resenia_id, etiqueta_id)
);

CREATE INDEX idx_resenia_etiquetas_resenia ON resenia_etiquetas(resenia_id);
CREATE INDEX idx_resenia_etiquetas_etiqueta ON resenia_etiquetas(etiqueta_id);

-- Tabla: historial_scraping (auditoría)
CREATE TABLE historial_scraping (
    id SERIAL PRIMARY KEY,
    profesor_id INTEGER REFERENCES profesores(id) ON DELETE CASCADE,
    estado VARCHAR(50),  -- 'exito', 'error', 'parcial'
    resenias_encontradas INTEGER DEFAULT 0,
    mensaje_error TEXT,
    duracion_segundos INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_historial_profesor ON historial_scraping(profesor_id);
CREATE INDEX idx_historial_timestamp ON historial_scraping(timestamp);
```

#### Diagrama de Relaciones

```
profesores ──┬── perfiles ──── perfil_etiquetas ──── etiquetas
             │
             ├── resenias_metadata ──┬── resenia_etiquetas ──── etiquetas
             │                       │
             │                       └── cursos
             │
             └── historial_scraping
```

### 4.2 MongoDB (Opiniones Textuales)

#### Colección: `opiniones`

```javascript
{
    "_id": ObjectId("..."),
    "profesor_id": 123,              // Referencia a PostgreSQL
    "profesor_nombre": "Juan Pérez",
    "resenia_id": 456,               // Referencia a PostgreSQL
    "fecha_opinion": ISODate("2024-01-15T00:00:00Z"),
    "curso": "Estructura de Datos",
    
    // Texto original
    "comentario": "Excelente profesor, explica muy bien los conceptos...",
    
    // Análisis de sentimiento (será poblado por BERT)
    "sentimiento": {
        "analizado": true,
        "puntuacion": 0.95,          // -1 (negativo) a 1 (positivo)
        "confianza": 0.87,           // 0 a 1
        "clasificacion": "positivo", // positivo, neutral, negativo
        "aspectos": {
            "explicacion": 0.95,
            "disponibilidad": 0.80,
            "evaluacion": 0.60
        },
        "modelo_version": "bert-base-spanish-sentiment-v1",
        "fecha_analisis": ISODate("2024-01-20T10:30:00Z")
    },
    
    // Metadatos
    "idioma": "es",
    "longitud_caracteres": 145,
    "longitud_palabras": 24,
    
    // Auditoría
    "fecha_extraccion": ISODate("2024-01-20T08:00:00Z"),
    "fuente": "misprofesores.com"
}
```

#### Índices MongoDB

```javascript
// Índice compuesto para búsquedas por profesor
db.opiniones.createIndex({ "profesor_id": 1, "fecha_opinion": -1 })

// Índice para búsqueda por sentimiento
db.opiniones.createIndex({ "sentimiento.clasificacion": 1 })

// Índice de texto para búsqueda full-text
db.opiniones.createIndex({ "comentario": "text", "curso": "text" })

// Índice para análisis no procesados
db.opiniones.createIndex({ "sentimiento.analizado": 1 })

// Índice temporal
db.opiniones.createIndex({ "fecha_opinion": -1 })
```

#### Ventajas de Esta Arquitectura

**PostgreSQL (Relacional):**
- ✅ Consultas complejas con JOINs
- ✅ Integridad referencial
- ✅ Agregaciones numéricas eficientes
- ✅ Historial temporal de métricas
- ✅ Ideal para dashboards y estadísticas

**MongoDB (No Relacional):**
- ✅ Almacenamiento flexible de texto
- ✅ Documentos con estructura anidada (análisis de sentimiento)
- ✅ Búsqueda full-text optimizada
- ✅ Escalabilidad horizontal para grandes volúmenes
- ✅ Ideal para procesamiento de NLP con BERT

**Sincronización:**
```
PostgreSQL.resenias_metadata.mongo_opinion_id 
    ↔ 
MongoDB.opiniones._id
```

---

## 5. Propuesta de API REST

### 5.1 Arquitectura General

```
┌────────────────────────────────────────────┐
│         SentimentInsightUAM API            │
│         (FastAPI + Python 3.11+)           │
├────────────────────────────────────────────┤
│                                            │
│  ┌──────────────┐      ┌──────────────┐  │
│  │  PostgreSQL  │      │   MongoDB    │  │
│  │  (Datos      │      │  (Opiniones  │  │
│  │ estructurados)│      │  textuales)  │  │
│  └──────────────┘      └──────────────┘  │
│         ▲                     ▲            │
│         │                     │            │
│         └─────────┬───────────┘            │
│                   │                        │
└───────────────────┼────────────────────────┘
                    │
            ┌───────▼────────┐
            │   Frontend/    │
            │   Consumers    │
            └────────────────┘
```

### 5.2 Stack Tecnológico Propuesto

- **Framework**: FastAPI (asíncrono, OpenAPI automático)
- **ORM PostgreSQL**: SQLAlchemy 2.0 (async)
- **Cliente MongoDB**: Motor (async MongoDB driver)
- **Validación**: Pydantic v2
- **Autenticación**: JWT (opcional para endpoints protegidos)
- **Documentación**: Swagger UI (automático con FastAPI)
- **Caché**: Redis (opcional, para consultas frecuentes)

### 5.3 Endpoints Indispensables

#### 5.3.1 Profesores

```python
# GET /api/v1/profesores
# Listar todos los profesores con paginación
Response: {
    "total": 150,
    "page": 1,
    "page_size": 20,
    "data": [
        {
            "id": 1,
            "nombre": "Juan Pérez García",
            "slug": "juan-perez-garcia",
            "ultima_actualizacion": "2024-01-20T10:30:00Z"
        }
    ]
}

# GET /api/v1/profesores/{id}
# Obtener perfil completo de un profesor
Response: {
    "id": 1,
    "nombre": "Juan Pérez García",
    "slug": "juan-perez-garcia",
    "metricas_actuales": {
        "calidad_general": 9.5,
        "dificultad": 7.2,
        "porcentaje_recomendacion": 95.0,
        "total_resenias": 47
    },
    "etiquetas_frecuentes": [
        {"etiqueta": "EXCELENTE CLASE", "contador": 25},
        {"etiqueta": "INSPIRA", "contador": 18}
    ]
}

# GET /api/v1/profesores/buscar?q={nombre}
# Búsqueda por nombre (normalizada)
Query: q=juan perez
Response: [...]
```

#### 5.3.2 Reseñas

```python
# GET /api/v1/profesores/{id}/resenias
# Obtener reseñas de un profesor con filtros
Query Params:
    - fecha_desde: ISO date
    - fecha_hasta: ISO date
    - curso: nombre del curso
    - calidad_min: float
    - page, page_size
Response: {
    "total": 47,
    "promedio_calidad": 9.2,
    "data": [
        {
            "id": 123,
            "fecha": "2024-01-15",
            "curso": "Estructura de Datos",
            "calidad_general": 10.0,
            "facilidad": 8.0,
            "tiene_comentario": true
        }
    ]
}

# GET /api/v1/resenias/{id}/opinion
# Obtener opinión textual con análisis de sentimiento
Response: {
    "resenia_id": 123,
    "comentario": "Excelente profesor...",
    "sentimiento": {
        "puntuacion": 0.95,
        "clasificacion": "positivo",
        "confianza": 0.87,
        "aspectos": {
            "explicacion": 0.95,
            "disponibilidad": 0.80
        }
    },
    "fecha_analisis": "2024-01-20T10:30:00Z"
}
```

#### 5.3.3 Estadísticas

```python
# GET /api/v1/estadisticas/general
# Estadísticas generales del sistema
Response: {
    "total_profesores": 150,
    "total_resenias": 4523,
    "total_opiniones_analizadas": 4100,
    "promedio_calidad_global": 8.7,
    "ultima_actualizacion": "2024-01-20T10:30:00Z"
}

# GET /api/v1/estadisticas/profesor/{id}
# Estadísticas detalladas de un profesor
Response: {
    "profesor_id": 1,
    "distribucion_calificaciones": {
        "10": 25,
        "9": 15,
        "8": 5,
        "7": 2
    },
    "tendencia_temporal": [
        {"mes": "2024-01", "calidad_promedio": 9.3},
        {"mes": "2023-12", "calidad_promedio": 9.5}
    ],
    "cursos_impartidos": [
        {"curso": "Estructura de Datos", "total_resenias": 20},
        {"curso": "Algoritmos", "total_resenias": 15}
    ],
    "sentimiento_general": {
        "positivo": 85,
        "neutral": 10,
        "negativo": 5
    }
}
```

#### 5.3.4 Etiquetas

```python
# GET /api/v1/etiquetas
# Listar todas las etiquetas con frecuencias
Response: [
    {"id": 1, "etiqueta": "EXCELENTE CLASE", "uso_total": 450},
    {"id": 2, "etiqueta": "INSPIRA", "uso_total": 320}
]

# GET /api/v1/etiquetas/{id}/profesores
# Profesores asociados a una etiqueta
Response: [
    {
        "profesor_id": 1,
        "nombre": "Juan Pérez",
        "veces_etiquetado": 25
    }
]
```

#### 5.3.5 Análisis de Sentimiento

```python
# GET /api/v1/sentimiento/pendientes
# Opiniones pendientes de análisis (para procesamiento BERT)
Response: {
    "total_pendientes": 423,
    "opiniones": [
        {
            "opinion_id": "507f1f77bcf86cd799439011",
            "profesor_id": 1,
            "comentario": "...",
            "fecha_extraccion": "2024-01-20T08:00:00Z"
        }
    ]
}

# POST /api/v1/sentimiento/analizar
# Actualizar análisis de sentimiento (usado por worker BERT)
Request: {
    "opinion_id": "507f1f77bcf86cd799439011",
    "sentimiento": {
        "puntuacion": 0.95,
        "clasificacion": "positivo",
        "confianza": 0.87,
        "aspectos": {...}
    },
    "modelo_version": "bert-base-spanish-sentiment-v1"
}
Response: {
    "status": "updated",
    "opinion_id": "507f1f77bcf86cd799439011"
}
```

#### 5.3.6 Health & Metadata

```python
# GET /api/v1/health
# Estado del sistema
Response: {
    "status": "healthy",
    "postgres": "connected",
    "mongodb": "connected",
    "redis": "connected",
    "timestamp": "2024-01-20T10:30:00Z"
}

# GET /api/v1/metadata/ultima-actualizacion
# Información de última sincronización
Response: {
    "ultima_ejecucion_scraper": "2024-01-20T06:00:00Z",
    "profesores_actualizados": 25,
    "resenias_nuevas": 134,
    "proxima_ejecucion_programada": "2024-01-21T06:00:00Z"
}
```

### 5.4 Ejemplo de Implementación (FastAPI)

```python
# main.py
from fastapi import FastAPI, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional

app = FastAPI(
    title="SentimentInsightUAM API",
    version="1.0.0",
    description="API para consulta de reseñas y análisis de profesores UAM"
)

# Dependencias
async def get_db() -> AsyncSession:
    """PostgreSQL session"""
    async with async_session() as session:
        yield session

async def get_mongo() -> AsyncIOMotorClient:
    """MongoDB client"""
    return mongo_client

# Endpoints
@app.get("/api/v1/profesores", response_model=PaginatedProfesores)
async def listar_profesores(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Lista todos los profesores con paginación"""
    # Implementación con SQLAlchemy
    pass

@app.get("/api/v1/profesores/{id}", response_model=ProfesorDetalle)
async def obtener_profesor(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """Obtiene perfil completo de un profesor"""
    # Implementación
    pass

@app.get("/api/v1/profesores/{id}/resenias", response_model=PaginatedResenias)
async def listar_resenias_profesor(
    id: int,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    curso: Optional[str] = None,
    calidad_min: Optional[float] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Lista reseñas de un profesor con filtros"""
    # Implementación
    pass

@app.get("/api/v1/resenias/{id}/opinion", response_model=OpinionConSentimiento)
async def obtener_opinion(
    id: int,
    db: AsyncSession = Depends(get_db),
    mongo: AsyncIOMotorClient = Depends(get_mongo)
):
    """Obtiene opinión textual con análisis de sentimiento"""
    # 1. Obtener resenia_metadata de PostgreSQL
    # 2. Usar mongo_opinion_id para buscar en MongoDB
    # 3. Combinar ambos
    pass
```

### 5.5 Integración con el Scraper

El proyecto actual alimentará las bases de datos mediante:

```python
# Ejemplo de inserción después del scraping
async def guardar_profesor_completo(data: dict):
    async with async_session() as db:
        # 1. Insertar/actualizar profesor
        profesor = await db.merge(Profesor(
            nombre=data['name'],
            slug=slugify(data['name']),
            url_misprofesores=profile_url
        ))
        await db.flush()
        
        # 2. Insertar perfil (snapshot)
        perfil = Perfil(
            profesor_id=profesor.id,
            calidad_general=data['overall_quality'],
            dificultad=data['difficulty'],
            porcentaje_recomendacion=data['recommend_percent']
        )
        db.add(perfil)
        await db.flush()
        
        # 3. Insertar etiquetas
        for tag in data['tags']:
            etiqueta = await obtener_o_crear_etiqueta(db, tag['label'])
            db.add(PerfilEtiqueta(
                perfil_id=perfil.id,
                etiqueta_id=etiqueta.id,
                contador=tag['count']
            ))
        
        # 4. Insertar reseñas
        for review in data['reviews']:
            # PostgreSQL: metadata
            curso = await obtener_o_crear_curso(db, review['course'])
            
            # MongoDB: opinión textual
            mongo_result = await mongo_client.opiniones.insert_one({
                'profesor_id': profesor.id,
                'profesor_nombre': data['name'],
                'fecha_opinion': review['date'],
                'curso': review['course'],
                'comentario': review['comment'],
                'sentimiento': {'analizado': False},
                'fecha_extraccion': datetime.utcnow()
            })
            
            # Vincular con PostgreSQL
            resenia = ReseniaMetadata(
                profesor_id=profesor.id,
                curso_id=curso.id if curso else None,
                fecha_resenia=review['date'],
                calidad_general=review['overall'],
                facilidad=review['ease'],
                asistencia=review['attendance'],
                calificacion_recibida=review['grade_received'],
                nivel_interes=review['interest'],
                mongo_opinion_id=str(mongo_result.inserted_id)
            )
            db.add(resenia)
            await db.flush()
            
            # Etiquetas de reseña
            for tag_name in review['tags']:
                etiqueta = await obtener_o_crear_etiqueta(db, tag_name)
                db.add(ReseniaEtiqueta(
                    resenia_id=resenia.id,
                    etiqueta_id=etiqueta.id
                ))
        
        await db.commit()
```

---

## 6. Propuesta de Sistema de Jobs Programados

### 6.1 Arquitectura del Scheduler

```
┌─────────────────────────────────────────────────────┐
│           Kernel de Jobs (APScheduler)              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌────────────────────────────────────────────┐   │
│  │     JobStore (PostgreSQL)                  │   │
│  │  - Configuración de jobs                   │   │
│  │  - Estado de ejecuciones                   │   │
│  │  - Logs de errores                         │   │
│  └────────────────────────────────────────────┘   │
│                                                     │
│  ┌────────────────────────────────────────────┐   │
│  │     Executors Pool                         │   │
│  │  - ThreadPoolExecutor (I/O bound)          │   │
│  │  - ProcessPoolExecutor (CPU bound)         │   │
│  └────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
         │         │         │         │
         ▼         ▼         ▼         ▼
    ┌────────┐┌────────┐┌────────┐┌────────┐
    │ Job 1  ││ Job 2  ││ Job 3  ││ Job N  │
    │06:00 AM││12:00 PM││18:00 PM││02:00 AM│
    └────────┘└────────┘└────────┘└────────┘
```

### 6.2 Tecnologías Propuestas

**Scheduler**: APScheduler (Advanced Python Scheduler)
- ✅ Soporte para CronTrigger, IntervalTrigger, DateTrigger
- ✅ Persistencia en PostgreSQL
- ✅ Ejecución paralela con thread/process pools
- ✅ Manejo de fallos y reintentos
- ✅ Integración con asyncio

**Alternativa Enterprise**: Celery + Redis/RabbitMQ
- Para mayor escalabilidad y distribución

### 6.3 Tipos de Jobs a Implementar

#### Job 1: Scraping Incremental de Profesores
```python
# Ejecutar cada 6 horas: 00:00, 06:00, 12:00, 18:00
@scheduler.scheduled_job('cron', hour='0,6,12,18', id='scrape_incremental')
async def job_scrape_incremental():
    """
    Scrapea un subset de profesores por ejecución
    """
    # 1. Obtener profesores que necesitan actualización
    profesores = await obtener_profesores_desactualizados(limit=10)
    
    # 2. Para cada profesor
    for prof in profesores:
        try:
            data = await find_and_scrape(prof['nombre'])
            await guardar_profesor_completo(data)
            await marcar_como_actualizado(prof['id'])
            
        except Exception as e:
            await registrar_error_scraping(prof['id'], str(e))
            
        # Rate limiting
        await asyncio.sleep(random.uniform(5, 10))
```

#### Job 2: Scraping Nocturno Masivo
```python
# Ejecutar diariamente a las 2:00 AM
@scheduler.scheduled_job('cron', hour=2, id='scrape_nocturno')
async def job_scrape_nocturno():
    """
    Actualización masiva en horario de baja carga
    """
    # 1. Obtener todos los profesores ordenados por antigüedad
    profesores = await obtener_todos_profesores_ordenados()
    
    # 2. Procesar en lotes de 50
    for batch in chunks(profesores, 50):
        tasks = [find_and_scrape(p['nombre']) for p in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for prof, result in zip(batch, results):
            if isinstance(result, Exception):
                await registrar_error_scraping(prof['id'], str(result))
            else:
                await guardar_profesor_completo(result)
        
        # Delay entre lotes
        await asyncio.sleep(60)
```

#### Job 3: Análisis de Sentimiento con BERT
```python
# Ejecutar cada hora
@scheduler.scheduled_job('interval', hours=1, id='bert_sentiment')
async def job_analizar_sentimiento():
    """
    Procesa opiniones pendientes con modelo BERT
    """
    # 1. Obtener opiniones sin analizar
    opiniones = await mongo_client.opiniones.find({
        'sentimiento.analizado': False
    }).limit(100).to_list(length=100)
    
    # 2. Cargar modelo BERT
    modelo = cargar_modelo_bert()
    
    # 3. Análisis en batch
    for batch in chunks(opiniones, 10):
        comentarios = [op['comentario'] for op in batch]
        sentimientos = modelo.predecir_batch(comentarios)
        
        for opinion, sent in zip(batch, sentimientos):
            await mongo_client.opiniones.update_one(
                {'_id': opinion['_id']},
                {'$set': {
                    'sentimiento': {
                        'analizado': True,
                        'puntuacion': sent['score'],
                        'clasificacion': sent['label'],
                        'confianza': sent['confidence'],
                        'aspectos': sent['aspects'],
                        'modelo_version': 'bert-base-spanish-v1',
                        'fecha_analisis': datetime.utcnow()
                    }
                }}
            )
```

#### Job 4: Limpieza y Mantenimiento
```python
# Ejecutar semanalmente los domingos a las 3:00 AM
@scheduler.scheduled_job('cron', day_of_week='sun', hour=3, id='mantenimiento')
async def job_mantenimiento():
    """
    Tareas de limpieza y optimización
    """
    # 1. Eliminar logs antiguos (>90 días)
    await limpiar_logs_antiguos(dias=90)
    
    # 2. Consolidar duplicados
    await eliminar_resenias_duplicadas()
    
    # 3. Actualizar estadísticas precalculadas
    await actualizar_vistas_materializadas()
    
    # 4. VACUUM en PostgreSQL
    await ejecutar_vacuum()
```

#### Job 5: Reportes Automáticos
```python
# Ejecutar diariamente a las 8:00 AM
@scheduler.scheduled_job('cron', hour=8, id='reporte_diario')
async def job_reporte_diario():
    """
    Genera y envía reportes diarios
    """
    # 1. Calcular métricas del día anterior
    metricas = await calcular_metricas_diarias()
    
    # 2. Generar reporte
    reporte = {
        'fecha': date.today(),
        'profesores_actualizados': metricas['prof_actualizados'],
        'resenias_nuevas': metricas['resenias_nuevas'],
        'opiniones_analizadas': metricas['opiniones_analizadas'],
        'errores': metricas['errores'],
        'tiempo_total': metricas['duracion']
    }
    
    # 3. Guardar en PostgreSQL
    await guardar_reporte(reporte)
    
    # 4. Enviar notificación (opcional)
    # await enviar_email_reporte(reporte)
```

### 6.4 Distribución de Profesores por Horario

**Estrategia: Round-Robin con Prioridad**

```python
# Configuración
TOTAL_PROFESORES = 150
GRUPOS = {
    'madrugada': {  # 02:00 - 06:00
        'profesores': range(0, 38),    # 38 profesores
        'intervalo': 15  # minutos entre cada uno
    },
    'maniana': {     # 06:00 - 12:00
        'profesores': range(38, 75),   # 37 profesores
        'intervalo': 10
    },
    'tarde': {       # 12:00 - 18:00
        'profesores': range(75, 113),  # 38 profesores
        'intervalo': 10
    },
    'noche': {       # 18:00 - 00:00
        'profesores': range(113, 150), # 37 profesores
        'intervalo': 10
    }
}

async def programar_por_grupos():
    """
    Programa jobs individuales para cada profesor
    """
    profesores = await obtener_todos_profesores()
    
    for grupo, config in GRUPOS.items():
        hora_inicio = HORARIOS[grupo]['inicio']
        
        for idx in config['profesores']:
            if idx >= len(profesores):
                break
                
            profesor = profesores[idx]
            
            # Calcular offset en minutos
            offset = (idx - config['profesores'].start) * config['intervalo']
            hora = hora_inicio.hour + (offset // 60)
            minuto = offset % 60
            
            # Crear job
            scheduler.add_job(
                func=scrape_profesor_individual,
                trigger='cron',
                hour=hora,
                minute=minuto,
                args=[profesor['id']],
                id=f"scrape_prof_{profesor['id']}",
                replace_existing=True
            )
```

### 6.5 Implementación Completa del Kernel

```python
# scheduler_kernel.py
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime
import logging

# Configuración
jobstores = {
    'default': SQLAlchemyJobStore(url='postgresql://user:pass@localhost/jobs_db')
}

executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}

job_defaults = {
    'coalesce': False,  # Ejecutar todos los jobs perdidos
    'max_instances': 3  # Máximo 3 instancias concurrentes por job
}

# Inicializar scheduler
scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone='America/Mexico_City'
)

# Listener para eventos
def job_listener(event):
    if event.exception:
        logging.error(f"Job {event.job_id} falló: {event.exception}")
        # Registrar en BD
        asyncio.create_task(registrar_fallo_job(event))
    else:
        logging.info(f"Job {event.job_id} completado exitosamente")

scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

# Iniciar kernel
async def iniciar_kernel():
    """Punto de entrada del kernel de jobs"""
    logging.info("Iniciando Kernel de Jobs...")
    
    # Registrar todos los jobs
    scheduler.add_job(job_scrape_incremental, 'cron', hour='0,6,12,18')
    scheduler.add_job(job_scrape_nocturno, 'cron', hour=2)
    scheduler.add_job(job_analizar_sentimiento, 'interval', hours=1)
    scheduler.add_job(job_mantenimiento, 'cron', day_of_week='sun', hour=3)
    scheduler.add_job(job_reporte_diario, 'cron', hour=8)
    
    # Programar jobs individuales por profesor
    await programar_por_grupos()
    
    # Iniciar
    scheduler.start()
    logging.info("Kernel activo. Jobs programados:")
    scheduler.print_jobs()
    
    # Mantener vivo
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Deteniendo Kernel...")
        scheduler.shutdown()

if __name__ == '__main__':
    asyncio.run(iniciar_kernel())
```

### 6.6 Monitoreo y Dashboard

**Métricas a Rastrear:**
```python
# Tabla: job_metrics
CREATE TABLE job_metrics (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100),
    job_name VARCHAR(200),
    inicio TIMESTAMP,
    fin TIMESTAMP,
    duracion_segundos INTEGER,
    estado VARCHAR(50),  -- 'success', 'error', 'timeout'
    profesor_id INTEGER,
    resenias_procesadas INTEGER,
    errores_count INTEGER,
    mensaje_error TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_job_metrics_job_id ON job_metrics(job_id);
CREATE INDEX idx_job_metrics_timestamp ON job_metrics(timestamp);
```

**Endpoint de Monitoreo:**
```python
@app.get("/api/v1/jobs/status")
async def status_jobs():
    """Estado actual de todos los jobs"""
    return {
        'jobs_activos': scheduler.get_jobs(),
        'proximas_ejecuciones': [
            {
                'job_id': job.id,
                'proxima_ejecucion': job.next_run_time,
                'ultima_ejecucion': await obtener_ultima_ejecucion(job.id)
            }
            for job in scheduler.get_jobs()
        ],
        'metricas_24h': await obtener_metricas_ultimas_24h()
    }
```

---

## Conclusión

Este documento proporciona una visión completa del proyecto SentimentInsightUAM, desde la extracción inicial de datos hasta la propuesta de arquitectura completa con bases de datos, API y sistema de jobs programados. La implementación actual (scraping sin persistencia) es la base sólida sobre la cual se construirán las siguientes iteraciones del proyecto.

**Próximos Pasos Sugeridos:**
1. Implementar capa de persistencia en PostgreSQL y MongoDB
2. Desarrollar worker de análisis de sentimiento con BERT
3. Crear API REST con FastAPI
4. Implementar kernel de jobs con APScheduler
5. Desarrollar frontend para visualización de datos

---

**Fecha de Documentación**: 26 de Noviembre, 2025  
**Versión**: 1.2.1  
**Autor**: Equipo SentimentInsightUAM

---

## 📚 Documentación Relacionada

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Arquitectura del sistema
- [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) - Guía de desarrollo
- [DATABASE_DESIGN.md](./DATABASE_DESIGN.md) - Diseño de bases de datos
- [DATABASE_SETUP.md](./DATABASE_SETUP.md) - Configuración de BD
- [DOCKER_SETUP.md](./DOCKER_SETUP.md) - Configuración con Docker

