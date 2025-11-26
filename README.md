# SentimentInsightUAM

Sistema de scraping y análisis de reseñas de profesores de la **Universidad Autónoma Metropolitana, Unidad Azcapotzalco**. Este proyecto extrae información del directorio oficial de la UAM y de perfiles en MisProfesores.com para análisis de sentimiento y visualización de datos.

**Versión**: 1.2.1 | [CHANGELOG](CHANGELOG.md)

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Flujos Críticos](#-flujos-críticos)
- [Configuración](#-configuración)
- [Desarrollo](#-desarrollo)
- [Documentación](#-documentación)
- [Contribuciones](#-contribuciones)

---

## 🎯 Características

### Extracción de Datos
- **Directorio UAM**: Extracción automática de lista de profesores del [Directorio UAM Azcapotzalco](https://sistemas.azc.uam.mx/Somos/Directorio/)
- **MisProfesores.com**: Scraping de perfiles completos con calificaciones, etiquetas y reseñas
- **Paginación automática**: Sin límite artificial de páginas

### Sistema de Caché Inteligente
- Detección automática de cambios en número de reseñas
- Tolerancia de ±5 reseñas para evitar re-scraping innecesario
- Opción para forzar actualización cuando sea necesario

### Persistencia Triple
| Formato | Ubicación | Propósito |
|---------|-----------|-----------|
| HTML | `data/outputs/html/` | Auditoría y re-parsing |
| JSON | `data/outputs/profesores/` | Consumo local |
| Base de Datos | PostgreSQL + MongoDB | Consultas y análisis |

### CLI Interactivo
```bash
python -m src.cli nombres-uam    # Extraer lista de profesores
python -m src.cli prof           # Scrapear profesor (interactivo)
python -m src.cli scrape-all     # Scrapear todos con caché
```

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                   SentimentInsightUAM                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │    CLI      │────▶│  Scrapers   │────▶│   Parser    │   │
│  │  (cli.py)   │     │  (mp/uam)   │     │ (parser.py) │   │
│  └─────────────┘     └─────────────┘     └─────────────┘   │
│                             │                               │
│                             ▼                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Persistencia                         │  │
│  │  ┌─────────┐   ┌─────────┐   ┌───────────────────┐   │  │
│  │  │  HTML   │   │  JSON   │   │ PostgreSQL+MongoDB│   │  │
│  │  └─────────┘   └─────────┘   └───────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Estructura del Proyecto

```
SentimentInsightUAM/
├── src/
│   ├── cli.py                 # Interfaz de línea de comandos
│   ├── core/
│   │   └── browser.py         # Context manager Playwright
│   ├── db/
│   │   ├── __init__.py        # Conexiones async
│   │   ├── models.py          # Modelos ORM SQLAlchemy
│   │   └── repository.py      # Persistencia dual
│   ├── mp/
│   │   ├── parser.py          # Parser HTML
│   │   └── scrape_prof.py     # Scraper con caché
│   └── uam/
│       └── nombres_uam.py     # Scraper directorio UAM
├── data/
│   ├── inputs/                # Lista de profesores
│   └── outputs/
│       ├── html/              # HTML original
│       └── profesores/        # JSON estructurado
├── scripts/                   # Scripts de utilidad
├── tests/                     # Tests de integración
├── docs/                      # Documentación técnica
├── docker-compose.yml         # Orquestación Docker
├── Makefile                   # Comandos de desarrollo
└── requirements.txt           # Dependencias Python
```

Para más detalles, consulta [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 🚀 Instalación

### Opción A: Con Docker (Recomendado)

**Requisitos**: Docker >= 20.10, Python 3.11+

```bash
# 1. Clonar repositorio
git clone https://github.com/christianpm-gh/SentimentInsightUAM.git
cd SentimentInsightUAM

# 2. Configurar variables de entorno
cp .env.docker .env

# 3. Iniciar bases de datos
make docker-up

# 4. Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python -m playwright install chromium

# 5. Verificar instalación
make db-status
python -m src.cli --help
```

### Opción B: Sin Docker

Consulta [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md) para instalación manual de PostgreSQL y MongoDB.

---

## 💻 Uso

### 1. Extraer Lista de Profesores UAM
```bash
python -m src.cli nombres-uam
```
Genera `data/inputs/profesor_nombres.json` con la lista de profesores.

### 2. Scrapear Profesor Individual

**Modo interactivo:**
```bash
python -m src.cli prof
```

**Por nombre:**
```bash
python -m src.cli prof --name "Juan Pérez García"
```

### 3. Scrapear Todos los Profesores
```bash
python -m src.cli scrape-all
```

**Salida ejemplo:**
```
Iniciando scraping de 150 profesores...
================================================================================

[1/150] Procesando: Juan Perez Garcia
  -> Scrapeado exitosamente (47 reseñas)

[2/150] Procesando: Maria Lopez Hernandez
  -> Cache vigente (32 reseñas)

================================================================================
RESUMEN DE SCRAPING
================================================================================
Total profesores procesados: 150
Scrapeados exitosamente: 28
Obtenidos de cache: 119
Errores: 3
================================================================================
```

### Formato de Salida JSON

```json
{
  "name": "Nombre del Profesor",
  "overall_quality": 9.5,
  "difficulty": 7.2,
  "recommend_percent": 95.0,
  "cached": false,
  "tags": [{"label": "EXCELENTE CLASE", "count": 25}],
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
      "comment": "Excelente profesor..."
    }
  ]
}
```

---

## 🔄 Flujos Críticos

### Flujo de Caché Inteligente

```
┌─────────────────┐
│ Solicitar datos │
│ de profesor     │
└────────┬────────┘
         │
         ▼
┌────────────────────┐     ┌─────────────────┐
│ ¿Existe caché?     │──No─▶ Scrapear nuevo  │
└────────┬───────────┘     └─────────────────┘
         │ Sí
         ▼
┌────────────────────┐     ┌─────────────────┐
│ ¿Cambió número de  │──No─▶ Retornar caché  │
│ reseñas (±5)?      │     └─────────────────┘
└────────┬───────────┘
         │ Sí
         ▼
┌─────────────────┐
│ Scrapear nuevo  │
│ y actualizar    │
└─────────────────┘
```

### Flujo de Persistencia

```
Datos scrapeados
       │
       ├──▶ Guardar HTML (auditoría)
       ├──▶ Guardar JSON (local)
       └──▶ Guardar en BD (PostgreSQL + MongoDB)
```

---

## ⚙️ Configuración

### Variables de Entorno (`.env`)

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

# Scraper
HEADLESS=true
```

### Comandos Make

```bash
make help              # Ver comandos disponibles
make docker-up         # Iniciar BD
make docker-down       # Detener BD
make db-status         # Estado de BD
make db-psql           # Shell PostgreSQL
make db-mongo          # Shell MongoDB
make install           # Instalar dependencias
```

### Script de Limpieza de BD

```bash
python scripts/clean_databases.py          # Modo interactivo
python scripts/clean_databases.py --all    # Limpiar todo
python scripts/clean_databases.py --verify # Solo verificar
```

---

## 🛠️ Desarrollo

### Configuración del Entorno

```bash
# Clonar y entrar al directorio
git clone https://github.com/christianpm-gh/SentimentInsightUAM.git
cd SentimentInsightUAM

# Crear y activar venv
python -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
python -m playwright install chromium

# Iniciar BD
make docker-up
```

### Ejecutar Tests

```bash
# Test de integración de BD
python tests/test_database_integration.py

# Test de scraping
python tests/test_scrape_josue_padilla.py
```

Para más detalles, consulta [docs/DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md).

---

## 📚 Documentación

| Documento | Descripción |
|-----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitectura del sistema |
| [TECHNICAL_DOCUMENTATION.md](docs/TECHNICAL_DOCUMENTATION.md) | Documentación técnica detallada |
| [DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md) | Guía para desarrolladores |
| [DATABASE_DESIGN.md](docs/DATABASE_DESIGN.md) | Diseño de bases de datos |
| [DATABASE_SETUP.md](docs/DATABASE_SETUP.md) | Configuración manual de BD |
| [DOCKER_SETUP.md](docs/DOCKER_SETUP.md) | Configuración con Docker |

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Consulta:

- [CONTRIBUTING.md](.github/CONTRIBUTING.md) - Guía de contribución
- [COMMIT_CONVENTION.md](.github/COMMIT_CONVENTION.md) - Convención de commits
- [BRANCH_NAMING.md](.github/BRANCH_NAMING.md) - Nombres de ramas
- [PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md) - Template para PRs

---

## 🔮 Roadmap

- [x] Persistencia en PostgreSQL + MongoDB (v1.2.0)
- [x] Script de limpieza de BD (v1.2.0)
- [x] Fix de bug de paginación (v1.2.1)
- [ ] Análisis de sentimiento con BERT
- [ ] API REST con FastAPI
- [ ] Jobs programados
- [ ] Dashboard de visualización

---

## 📝 Notas Importantes

- **Uso responsable**: Este scraper es para fines educativos
- **Rate limiting**: Incluye delays aleatorios para evitar sobrecarga
- **Caché automático**: Evita scraping redundante
- **Timeouts**: 45s navegación, 30s selectores

---

## 📄 Licencia

Este proyecto es de código abierto para fines educativos.

## 👥 Equipo

Desarrollado por el equipo de SentimentInsightUAM - UAM Azcapotzalco

---

**⚠️ Disclaimer**: Este proyecto es con fines educativos y de investigación. El uso debe cumplir con los Términos de Servicio de los sitios web utilizados.
