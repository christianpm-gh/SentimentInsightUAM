# SentimentInsightUAM

Sistema de scraping y análisis de reseñas de profesores de la Universidad Autónoma Metropolitana, Unidad Azcapotzalco. Este proyecto extrae información del directorio oficial de la UAM y de perfiles en MisProfesores.com para análisis de sentimiento y visualización de datos.

## 🎯 Características

- **Extracción de nombres**: Obtiene automáticamente la lista de profesores del [Directorio UAM Azcapotzalco](https://sistemas.azc.uam.mx/Somos/Directorio/)
- **Scraping robusto**: Navega y extrae perfiles completos de MisProfesores.com con:
  - Búsqueda normalizada (sin acentos, case-insensitive)
  - Navegación directa por URL para evitar timeouts
  - Paginación automática de reseñas
  - Reintentos con backoff exponencial
- **Scraping masivo**: Comando `scrape-all` para procesar todos los profesores automáticamente
  - Procesamiento secuencial con delays inteligentes
  - Detección automática de cambios por profesor
  - Resumen de progreso en tiempo real
  - Manejo robusto de errores sin interrumpir el proceso
- **Caché inteligente**: 
  - Detecta automáticamente si un profesor ya fue scrapeado
  - Compara número de reseñas para detectar cambios
  - Evita re-scraping innecesario (eficiencia y respeto al servidor)
  - Permite forzar actualización cuando sea necesario
- **Persistencia dual**:
  - HTML original guardado en `data/outputs/html/` (auditoría)
  - JSON estructurado en `data/outputs/profesores/` (consumo)
  - Nombres normalizados con slugify para consistencia
- **Parsing estructurado**: Extrae calificaciones, etiquetas, comentarios y metadatos
- **CLI interactivo**: Interfaz de línea de comandos con menú de selección

## 📋 Requisitos

### Opción A: Con Docker (Recomendado)

- **Docker** >= 20.10
- **Docker Compose** >= 2.0
- Python 3.11+ (solo para el scraper)

### Opción B: Sin Docker

- Python 3.11+
- PostgreSQL >= 15.0
- MongoDB >= 7.0
- Playwright (Chromium)
- BeautifulSoup4
- Dependencias listadas en `requirements.txt`

## 🚀 Instalación

### Opción A: Con Docker (Recomendado para Desarrollo)

Esta opción configura automáticamente las bases de datos PostgreSQL y MongoDB en contenedores aislados.

#### 1. Clonar el repositorio

```bash
git clone https://github.com/christianpm-gh/SentimentInsightUAM.git
cd SentimentInsightUAM
```

#### 2. Configurar variables de entorno

```bash
# Copiar archivo de configuración para Docker
cp .env.docker .env

# (Opcional) Editar contraseñas para producción
nano .env
```

#### 3. Iniciar bases de datos con Docker

```bash
# Opción 1: Con Makefile (más conveniente)
make docker-up

# Opción 2: Docker Compose directo
docker-compose up -d
```

Esto iniciará:
- ✅ PostgreSQL 15 en puerto 5432
- ✅ MongoDB 7.0 en puerto 27017
- ✅ Scripts de inicialización ejecutados automáticamente
- ✅ 8 tablas PostgreSQL creadas
- ✅ 2 colecciones MongoDB creadas
- ✅ 21 etiquetas iniciales insertadas

#### 4. Instalar dependencias de Python

```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o: .venv\Scripts\activate  # Windows

# Instalar dependencias
make install
# o manualmente:
pip install -r requirements.txt
python -m playwright install chromium
```

#### 5. Verificar configuración

```bash
# Verificar estado de bases de datos
make db-status

# Conectar a PostgreSQL
make db-psql

# Conectar a MongoDB
make db-mongo
```

**¡Listo!** Las bases de datos están configuradas y listas para usar.

**Comandos útiles con Docker:**

```bash
make help              # Ver todos los comandos disponibles
make docker-up         # Iniciar contenedores
make docker-down       # Detener contenedores
make docker-logs       # Ver logs en tiempo real
make db-status         # Verificar estado de bases de datos
make db-reset          # Reiniciar bases de datos (DESTRUYE DATOS)
```

**Documentación completa:** Ver [docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md)

---

### Opción B: Instalación Manual (Sin Docker)

Para instalación manual de PostgreSQL y MongoDB, consulta la guía completa en [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md).

#### 1. Clonar el repositorio

```bash
git clone https://github.com/christianpm-gh/SentimentInsightUAM.git
cd SentimentInsightUAM
```

#### 2. Crear entorno virtual

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### 3. Instalar dependencias

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

#### 4. Configurar bases de datos

Sigue la guía detallada en [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md) para:
- Instalar PostgreSQL 15+
- Instalar MongoDB 7.0+
- Ejecutar scripts de inicialización
- Configurar usuarios y permisos

#### 5. Configurar variables de entorno

```bash
# Crear archivo .env con tus credenciales
nano .env
```

Ver ejemplo en `.env.docker` para la estructura requerida.

## 💻 Uso

### 1. Extraer nombres de profesores UAM

Obtiene la lista completa de profesores del Departamento de Sistemas de la UAM Azcapotzalco:

```bash
python -m src.cli nombres-uam
```

Esto generará automáticamente `data/inputs/profesor_nombres.json` con la información de todos los profesores.

### 2. Scrapear perfil de un profesor

**Modo interactivo** (recomendado):
```bash
python -m src.cli prof
```
Se mostrará un menú numerado con todos los profesores disponibles.

**Modo directo** (por nombre):
```bash
python -m src.cli prof --name "Juan Pérez García"
```

### 3. Scrapear todos los profesores

Procesa automáticamente todos los profesores del directorio UAM con caché inteligente:

```bash
python -m src.cli scrape-all
```

**Características del scraping masivo:**

- Procesa todos los profesores secuencialmente
- Aplica delays de 2-4 segundos entre profesores para evitar bloqueos
- Detecta automáticamente si un profesor necesita actualización
- Solo re-scrapea cuando hay cambios en el número de reseñas
- Muestra progreso en tiempo real con contador
- Maneja errores de forma individual sin detener el proceso completo
- Genera resumen final con estadísticas

**Salida ejemplo:**

```
Iniciando scraping de 150 profesores...
================================================================================

[1/150] Procesando: Juan Perez Garcia
  -> Scrapeado exitosamente (47 reseñas)
  -> Esperando 2s antes del siguiente...

[2/150] Procesando: Maria Lopez Hernandez
  -> Cache vigente (32 reseñas)
  -> Esperando 4s antes del siguiente...

[3/150] Procesando: Carlos Rodriguez Torres
  -> Detectados cambios: 28 -> ~35 reseñas
  -> Scrapeado exitosamente (35 reseñas)
  -> Esperando 2s antes del siguiente...

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

**Prevención de bloqueos:**

- Delays variables (no detectables como patrón automático)
- User agent realista configurado en el navegador
- Reintentos automáticos con backoff exponencial (via tenacity)
- Timeouts apropiados para cada operación
- Respeto a los límites del servidor

### 4. Salida de datos

El scraper implementa **persistencia automática** con dos formatos:

#### JSON estructurado (`data/outputs/profesores/nombre-profesor.json`)

```json
{
  "name": "Nombre del Profesor",
  "overall_quality": 9.5,
  "difficulty": 7.2,
  "recommend_percent": 95.0,
  "cached": false,
  "tags": [
    {"label": "EXCELENTE CLASE", "count": 25},
    {"label": "INSPIRA", "count": 18}
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
      "tags": ["BUENA ONDA", "ACCESIBLE"],
      "comment": "Excelente profesor, explica muy bien..."
    }
  ]
}
```

#### HTML original (`data/outputs/html/nombre-profesor.html`)

- Guardado para auditoría y análisis offline
- Permite re-parsing sin re-scraping
- Útil para debugging y mejora del parser

#### Caché Inteligente

El sistema detecta automáticamente si un profesor ya fue scrapeado:

```bash
# Primera vez: scraping completo
python -m src.cli prof --name "Juan Pérez"
# ⚙ Scrapeando Juan Pérez (9 páginas)...
# ✓ Guardado: HTML en juan-perez.html, JSON en juan-perez.json
# ✓ Total reseñas extraídas: 43

# Segunda vez (sin cambios): usa caché
python -m src.cli prof --name "Juan Pérez"
# ✓ Caché vigente para Juan Pérez (43 reseñas)
# Fuente: Caché

# Si hay nuevas reseñas: scraping automático
# ✓ Detectados cambios para Juan Pérez: 43 → ~48 reseñas
```

**Ventajas del caché:**
- ⚡ Respuesta instantánea para profesores ya scrapeados
- 🌐 Reduce carga en servidores externos
- ♻️ Evita scraping redundante
- 🎯 Solo actualiza cuando detecta cambios

## 🏗️ Arquitectura del Proyecto

```
SentimentInsightUAM/
├── src/
│   ├── __init__.py           # Paquete principal
│   ├── cli.py                # Interfaz de línea de comandos
│   ├── core/
│   │   ├── __init__.py
│   │   └── browser.py        # Context manager de Playwright
│   ├── uam/
│   │   ├── __init__.py
│   │   └── nombres_uam.py    # Scraper del directorio UAM
│   └── mp/
│       ├── __init__.py
│       ├── parser.py         # Parser HTML de MisProfesores
│       └── scrape_prof.py    # Scraper con caché inteligente
├── data/
│   ├── inputs/               # Listas de profesores
│   └── outputs/
│       ├── html/             # HTML original (auditoría)
│       └── profesores/       # JSONs estructurados
├── docs/
│   ├── TECHNICAL_DOCUMENTATION.md  # Documentación técnica completa
│   ├── DATABASE_DESIGN.md          # Diseño de bases de datos
│   ├── DATABASE_SETUP.md           # Configuración manual de BD
│   └── DOCKER_SETUP.md             # Configuración con Docker
├── scripts/
│   ├── init_postgres.sql     # Inicialización PostgreSQL
│   ├── init_mongo.js         # Inicialización MongoDB
│   └── setup_mongo_user.sh   # Setup de usuario MongoDB
├── docker-compose.yml        # Orquestación de contenedores
├── Makefile                  # Comandos útiles
├── .env.docker               # Template de variables de entorno
├── requirements.txt
├── .env                      # Variables de entorno (local)
└── README.md
```
│   │   ├── __init__.py
│   │   └── nombres_uam.py    # Scraper del directorio UAM
│   └── mp/
│       ├── __init__.py
│       ├── parser.py         # Parser HTML de MisProfesores
│       └── scrape_prof.py    # Scraper con caché inteligente
├── data/
│   ├── inputs/               # Listas de profesores
│   └── outputs/
│       ├── html/             # HTML original (auditoría)
│       └── profesores/       # JSONs estructurados
├── docs/
│   └── TECHNICAL_DOCUMENTATION.md  # Documentación técnica completa
├── requirements.txt
├── .env                      # Variables de entorno (opcional)
└── README.md
```

## 🔧 Módulos Principales

### `src.uam.nombres_uam`

Extrae nombres de profesores del directorio oficial UAM usando:

- Playwright para navegación dinámica
- Clic automático en "Ver más Profesorado"
- Normalización de nombres con slugify

### `src.mp.parser`

Parser HTML especializado que extrae:

- Calificaciones (calidad, dificultad, recomendación)
- Etiquetas con contadores
- Reseñas completas con metadatos
- Conteo automático de páginas

### `src.mp.scrape_prof`

Scraper robusto con:

- Búsqueda normalizada (elimina acentos)
- Navegación directa por href
- Esperas explícitas de selectores
- Paginación automática por URL
- Manejo de errores con reintentos
- **Caché inteligente**: Detecta cambios en reseñas
- **Persistencia dual**: HTML + JSON
- **Eficiencia**: Evita re-scraping innecesario

### `src.cli`

CLI con tres comandos principales:

- `nombres-uam`: Extrae lista de profesores del directorio UAM
- `prof`: Scrapea perfil individual (interactivo o directo)
- `scrape-all`: Scrapea todos los profesores con caché inteligente

## ⚙️ Configuración

### Variables de Entorno (`.env`)

#### Con Docker

El archivo `.env.docker` contiene todas las configuraciones necesarias:

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sentiment_uam_db
POSTGRES_USER=sentiment_admin
POSTGRES_PASSWORD=dev_password_2024

# MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB=sentiment_uam_nlp
MONGO_USER=sentiment_admin
MONGO_PASSWORD=dev_password_2024

# URLs de conexión
DATABASE_URL=postgresql+asyncpg://sentiment_admin:dev_password_2024@localhost:5432/sentiment_uam_db
MONGO_URL=mongodb://sentiment_admin:dev_password_2024@localhost:27017/sentiment_uam_nlp?authSource=sentiment_uam_nlp

# Scraper
HEADLESS=true
RATE_MIN_MS=400
RATE_MAX_MS=1200
```

#### Sin Docker (Instalación Manual)

Crea un archivo `.env` con tus credenciales personalizadas. Ver [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md) para más detalles.

### Comandos con Docker

```bash
# Ver ayuda completa
make help

# Gestión de contenedores
make docker-up         # Iniciar bases de datos
make docker-down       # Detener bases de datos
make docker-restart    # Reiniciar bases de datos
make docker-logs       # Ver logs en tiempo real

# Gestión de bases de datos
make db-status         # Verificar estado
make db-psql           # Conectar a PostgreSQL
make db-mongo          # Conectar a MongoDB
make db-reset          # Reiniciar (DESTRUYE DATOS)

# Desarrollo
make install           # Instalar dependencias Python
```

## 📝 Notas Importantes

- **Uso responsable**: Este scraper es para fines educativos. Respeta los Términos de Servicio de los sitios web.
- **Rate limiting**: El código incluye delays aleatorios para evitar sobrecarga de servidores.
- **Caché automático**: El sistema detecta automáticamente si un profesor ya fue scrapeado y evita scraping redundante.
- **Persistencia**: Todos los datos se guardan en disco automáticamente (HTML + JSON).
- **Bases de datos**: PostgreSQL para datos estructurados, MongoDB para análisis de sentimiento (v1.1.0+).
- **Docker**: Configuración con contenedores para desarrollo rápido y reproducible (v1.1.1+).
- **Timeouts**: Los timeouts están configurados para 45 segundos en navegación y 30 segundos en selectores.
- **Próximas características**: API REST con FastAPI, análisis de sentimiento con BERT, dashboard de visualización.

## 🔮 Próximas Características

- [ ] Persistencia en PostgreSQL (datos estructurados)
- [ ] Persistencia en MongoDB (comentarios/opiniones)
- [ ] Análisis de sentimiento con BERT
- [ ] API REST para consulta de datos
- [ ] Jobs programados con scheduler
- [ ] Dashboard de visualización

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, consulta la documentación en `.github/`:

- **[CONTRIBUTING.md](.github/CONTRIBUTING.md)** - Guía completa de contribución
- **[COMMIT_CONVENTION.md](.github/COMMIT_CONVENTION.md)** - Convención de mensajes de commit
- **[BRANCH_NAMING.md](.github/BRANCH_NAMING.md)** - Convención de nombres de ramas
- **[PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md)** - Plantilla para PRs

## 📄 Licencia

Este proyecto es de código abierto para fines educativos.

## 👥 Equipo

Desarrollado por el equipo de SentimentInsightUAM - UAM Azcapotzalco

---

**⚠️ Disclaimer**: Este proyecto es con fines educativos y de investigación. El uso debe cumplir con los Términos de Servicio de los sitios web utilizados.
