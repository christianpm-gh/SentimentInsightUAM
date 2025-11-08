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

- Python 3.11+
- Playwright (Chromium)
- BeautifulSoup4
- Dependencias listadas en `requirements.txt`

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/christianpm-gh/SentimentInsightUAM.git
cd SentimentInsightUAM
```

### 2. Crear entorno virtual

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### 4. Configurar variables de entorno (opcional)

```bash
# Crear archivo .env
echo HEADLESS=true > .env
```

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

```env
# Modo headless del navegador (true/false)
HEADLESS=true
```

## 📝 Notas Importantes

- **Uso responsable**: Este scraper es para fines educativos. Respeta los Términos de Servicio de los sitios web.
- **Rate limiting**: El código incluye delays aleatorios para evitar sobrecarga de servidores.
- **Caché automático**: El sistema detecta automáticamente si un profesor ya fue scrapeado y evita scraping redundante.
- **Persistencia**: Todos los datos se guardan en disco automáticamente (HTML + JSON).
- **Timeouts**: Los timeouts están configurados para 45 segundos en navegación y 30 segundos en selectores.
- **Próximas características**: Persistencia en PostgreSQL y MongoDB, análisis de sentimiento con BERT.

## 🔮 Próximas Características

- [ ] Persistencia en PostgreSQL (datos estructurados)
- [ ] Persistencia en MongoDB (comentarios/opiniones)
- [ ] Análisis de sentimiento con BERT
- [ ] API REST para consulta de datos
- [ ] Jobs programados con scheduler
- [ ] Dashboard de visualización

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, sigue el flujo de trabajo de Git establecido en `git_workflow.md`.

## 📄 Licencia

Este proyecto es de código abierto para fines educativos.

## 👥 Equipo

Desarrollado por el equipo de SentimentInsightUAM - UAM Azcapotzalco

---

**⚠️ Disclaimer**: Este proyecto es con fines educativos y de investigación. El uso debe cumplir con los Términos de Servicio de los sitios web utilizados.
