# Instrucciones para GitHub Copilot - SentimentInsightUAM

Este archivo proporciona contexto permanente a GitHub Copilot para asistir efectivamente en el desarrollo de SentimentInsightUAM.

---

## 📁 Archivos de Referencia Críticos

**SIEMPRE consulta estos archivos antes de responder preguntas o implementar features:**

1. **`CHANGELOG.md`** - Estado actual del proyecto, features implementadas, roadmap
2. **`docs/TECHNICAL_DOCUMENTATION.md`** - Arquitectura técnica detallada, propuestas de diseño
3. **`README.md`** - Documentación de usuario, comandos, instalación
4. **`.github/CONTRIBUTING.md`** - Guía de contribución (si existe)
5. **`.github/COMMIT_CONVENTION.md`** - Convenciones de commits (si existe)

---

## 🎯 Contexto del Proyecto

### Propósito
Sistema de scraping y análisis de reseñas de profesores de la Universidad Autónoma Metropolitana (UAM) Azcapotzalco, extrayendo datos de MisProfesores.com para análisis de sentimiento.

### Tecnologías Core
- **Python 3.11+**
- **Playwright** - Web scraping con navegador real
- **BeautifulSoup4** - Parsing HTML
- **Slugify** - Normalización de nombres
- **Tenacity** - Reintentos con backoff exponencial
- **Pydantic** - Validación de datos (futuro)

### Stack Futuro Planificado
- **PostgreSQL** - Datos estructurados (profesores, reseñas, etiquetas)
- **MongoDB** - Opiniones textuales y análisis de sentimiento
- **FastAPI** - API REST
- **BERT** - Análisis de sentimiento en español
- **APScheduler** - Jobs programados
- **React/Vue** - Dashboard frontend

---

## 🏗️ Arquitectura Actual

```
src/
├── cli.py                 # 3 comandos: nombres-uam, prof, scrape-all
├── core/
│   └── browser.py         # Context manager async de Playwright
├── uam/
│   └── nombres_uam.py     # Scraper directorio UAM Azcapotzalco
└── mp/
    ├── parser.py          # Parser HTML especializado
    └── scrape_prof.py     # Scraper con caché inteligente

data/
├── inputs/
│   └── profesor_nombres.json  # Lista de profesores UAM
└── outputs/
    ├── html/              # HTML original (auditoría)
    └── profesores/        # JSON estructurado (consumo)
```

---

## 🔑 Características Implementadas (v1.0.0)

### ✅ Sistema de Caché Inteligente
**IMPORTANTE**: El scraper detecta automáticamente si un profesor necesita actualización.

```python
# Lógica de caché en src/mp/scrape_prof.py
# - Compara número de reseñas: caché vs actual
# - Tolerancia de ±5 reseñas
# - Solo re-scrapea si hay cambios detectados
```

**Funciones clave:**
- `_get_cached_data(prof_name)` - Lee caché existente
- `_save_html(prof_name, html)` - Guarda HTML original
- `_save_json(prof_name, data)` - Guarda JSON estructurado

### ✅ Persistencia Dual
**Dos formatos siempre:**
1. HTML en `data/outputs/html/{slug}.html` - Auditoría y re-parsing
2. JSON en `data/outputs/profesores/{slug}.json` - Consumo directo

### ✅ CLI con 3 Comandos

1. **`nombres-uam`** - Extrae profesores del directorio UAM
2. **`prof [--name "Nombre"]`** - Scrapea profesor (interactivo o directo)
3. **`scrape-all`** - Scrapea todos los profesores con caché inteligente

### ✅ Parser Robusto
**Pattern establecido para evitar AttributeError:**
```python
# ✅ CORRECTO
elem = soup.select_one(".selector")
value = elem.get_text(strip=True) if elem else None

# ❌ INCORRECTO (causa AttributeError)
value = (soup.select_one(".selector") or "").get_text(strip=True)
```

### ✅ Rate Limiting
- Delays variables 2-4s entre profesores
- Backoff exponencial con `tenacity` (4 reintentos)
- Timeouts: 45s navegación, 30s selectores

---

## 📋 Roadmap y Features Planificadas

### Fase 1: Bases de Datos (Próxima)
- [ ] Esquema PostgreSQL completo (ver `TECHNICAL_DOCUMENTATION.md` sección 4.1)
- [ ] Esquema MongoDB para opiniones (ver sección 4.2)
- [ ] Migración de persistencia JSON → BD
- [ ] Script de sincronización

### Fase 2: Análisis de Sentimiento
- [ ] Integración BERT modelo español
- [ ] Worker asíncrono para procesamiento
- [ ] Análisis por aspectos (explicación, disponibilidad, evaluación)

### Fase 3: API REST
- [ ] FastAPI con endpoints documentados (ver sección 5.3)
- [ ] Autenticación JWT
- [ ] Paginación y filtros
- [ ] Caché con Redis

### Fase 4: Jobs Programados
- [ ] APScheduler (ver sección 6)
- [ ] Jobs: incremental (6h), nocturno (2am), BERT (1h), mantenimiento (semanal)

### Fase 5: Frontend
- [ ] Dashboard React/Vue
- [ ] Visualizaciones y comparaciones

---

## 🛡️ Buenas Prácticas del Proyecto

### Al Escribir Código

1. **Siempre usar async/await** para I/O
   ```python
   async def my_function():
       async with browser_ctx() as ctx:
           page = await ctx.new_page()
   ```

2. **Normalizar nombres** con `slugify`
   ```python
   from slugify import slugify
   file_name = slugify(profesor_name)
   ```

3. **Implementar caché** cuando sea posible
   - Verificar existencia antes de scrapear
   - Comparar datos para detectar cambios

4. **Persistencia dual** siempre (HTML + JSON)
   - HTML para auditoría y re-parsing
   - JSON para consumo directo

5. **Manejo de errores robusto**
   ```python
   try:
       result = await scrape_function()
   except Exception as e:
       print(f"Error: {str(e)}")
       # Continuar, no interrumpir proceso completo
   ```

6. **Rate limiting obligatorio**
   ```python
   await asyncio.sleep(2 + (2 * random.random()))  # 2-4s variable
   ```

7. **Usar tenacity para reintentos**
   ```python
   from tenacity import retry, wait_random_exponential, stop_after_attempt
   
   @retry(wait=wait_random_exponential(min=1, max=8), stop=stop_after_attempt(4))
   async def fetch_data():
       ...
   ```

### Al Parsear HTML

1. **Pattern seguro** para selectores opcionales:
   ```python
   elem = soup.select_one(".selector")
   value = elem.get_text(strip=True) if elem else None
   ```

2. **Normalizar fechas** a ISO 8601 (YYYY-MM-DD)

3. **Extraer números** con regex robusto:
   ```python
   m = re.search(r"\d+(?:[.,]\d+)?", text.replace(",", "."))
   number = float(m.group(0)) if m else None
   ```

### Convenciones de Código

- **Docstrings** en español, estilo Google
- **Type hints** en todas las funciones
- **Nombres descriptivos** en español (profesores, resenias, etc.)
- **Comentarios** en español para lógica compleja

---

## 🔧 Comandos Frecuentes

### Desarrollo
```bash
# Instalar dependencias
pip install -r requirements.txt
python -m playwright install chromium

# Ejecutar scraping
python -m src.cli nombres-uam                    # Extraer nombres UAM
python -m src.cli prof                           # Modo interactivo
python -m src.cli prof --name "Nombre Completo"  # Directo
python -m src.cli scrape-all                     # Masivo con caché

# Ejecutar módulos directamente
python -m src.uam.nombres_uam                    # Scraper UAM
python -m src.mp.scrape_prof "Nombre Profesor"   # Scraper individual
```

### Variables de Entorno (.env)
```env
HEADLESS=true    # Modo headless del navegador (true/false)
```

---

## 🤖 Guía para Implementar Nuevas Features

### Antes de Empezar
1. ✅ Lee `CHANGELOG.md` - Estado actual
2. ✅ Revisa `docs/TECHNICAL_DOCUMENTATION.md` - Arquitectura propuesta
3. ✅ Verifica que la feature no esté implementada
4. ✅ Identifica dependencias de otras features

### Durante la Implementación
1. ✅ Sigue las buenas prácticas establecidas
2. ✅ Implementa tests si es posible
3. ✅ Documenta código con docstrings
4. ✅ Actualiza README.md si afecta uso

### Al Finalizar
1. ✅ Actualiza `CHANGELOG.md`:
   - Mueve feature de `[Unreleased]` a nueva versión
   - Documenta breaking changes
2. ✅ Actualiza documentación técnica si aplica
3. ✅ **Crea commit de versión** siguiendo versionado semántico

---

## 🏷️ Versionado Semántico y Commits

**IMPORTANTE**: Cada implementación debe resultar en un commit de versión siguiendo [Versionado Semántico 2.0.0](https://semver.org/lang/es/).

### Formato de Versión: MAJOR.MINOR.PATCH

#### Cuándo incrementar cada dígito:

1. **MAJOR (X.0.0)** - Cambios incompatibles con versiones anteriores
   - Cambios en API pública que rompen compatibilidad
   - Eliminación de features existentes
   - Cambios en estructura de datos JSON que afectan consumidores
   - Cambios en comandos CLI que rompen scripts existentes
   - **Ejemplo**: Cambiar formato de salida JSON, eliminar comando CLI

2. **MINOR (0.X.0)** - Nueva funcionalidad compatible con versiones anteriores
   - Nuevas features que NO rompen código existente
   - Nuevos comandos CLI
   - Nuevos endpoints en API
   - Nuevas tablas en base de datos
   - Mejoras significativas de rendimiento
   - **Ejemplo**: Agregar comando `scrape-all`, implementar API REST

3. **PATCH (0.0.X)** - Correcciones de bugs compatibles
   - Fixes de bugs sin cambiar funcionalidad
   - Correcciones de documentación
   - Refactorizaciones internas
   - Mejoras de rendimiento menores
   - Actualizaciones de dependencias sin breaking changes
   - **Ejemplo**: Fix del AttributeError, optimización de búsqueda

### Workflow de Versionado Automático

Cuando implementes una feature, **SIEMPRE sigue estos pasos**:

```bash
# 1. Implementa el cambio
# 2. Determina el tipo de versión

# Para PATCH (bug fix, refactor, docs)
git add .
git commit -m "fix: Descripción del bug corregido"
# o
git commit -m "refactor: Descripción de la refactorización"
# o
git commit -m "docs: Actualización de documentación"

# Para MINOR (nueva feature)
git add .
git commit -m "feat: Descripción de la nueva característica"

# Para MAJOR (breaking change)
git add .
git commit -m "feat!: Descripción del cambio incompatible

BREAKING CHANGE: Explicación detallada de qué se rompió y cómo migrar"

# 3. Actualiza CHANGELOG.md con la nueva versión
# 4. Crea tag de versión
git tag -a vX.Y.Z -m "Version X.Y.Z: Resumen de cambios"
git push origin main --tags
```

### Convenciones de Commits (Conventional Commits)

**Formato**: `<tipo>[scope opcional]: <descripción>`

**Tipos principales**:
- `feat:` - Nueva feature → **Incrementa MINOR** (o MAJOR si hay `!` o BREAKING CHANGE)
- `fix:` - Corrección de bug → **Incrementa PATCH**
- `refactor:` - Refactorización sin cambio funcional → **Incrementa PATCH**
- `perf:` - Mejora de rendimiento → **Incrementa PATCH** (o MINOR si es significativa)
- `docs:` - Solo documentación → **Incrementa PATCH**
- `test:` - Agregar/modificar tests → No incrementa versión
- `chore:` - Tareas de mantenimiento → No incrementa versión
- `build:` - Cambios en sistema de build → No incrementa versión
- `ci:` - Cambios en CI/CD → No incrementa versión

**Indicador de Breaking Change**: Agregar `!` después del tipo o incluir `BREAKING CHANGE:` en el cuerpo del commit.

### Ejemplos Prácticos de Versionado

#### Ejemplo 1: Implementar Persistencia PostgreSQL
```bash
# Versión actual: 1.0.0
# Cambio: Nueva funcionalidad (base de datos)
# Tipo: MINOR (nueva feature compatible)

git commit -m "feat: Implementar persistencia en PostgreSQL

- Crear esquema de base de datos según TECHNICAL_DOCUMENTATION.md sección 4.1
- Implementar módulo src/db/postgres.py
- Migrar datos de JSON a PostgreSQL
- Mantener compatibilidad con lectura de JSON existente"

# Nueva versión: 1.1.0
git tag -a v1.1.0 -m "Version 1.1.0: Persistencia PostgreSQL"
```

#### Ejemplo 2: Fix de Bug en Parser
```bash
# Versión actual: 1.1.0
# Cambio: Corrección de bug
# Tipo: PATCH

git commit -m "fix: Corregir AttributeError en parser.py

- Aplicar pattern seguro en parse_reviews()
- Cambiar (elem or '').get_text() por verificación condicional
- Afecta 7 ubicaciones en el parser"

# Nueva versión: 1.1.1
git tag -a v1.1.1 -m "Version 1.1.1: Fix AttributeError en parser"
```

#### Ejemplo 3: Cambiar Formato de Salida JSON (Breaking Change)
```bash
# Versión actual: 1.1.1
# Cambio: Modificar estructura de JSON de salida
# Tipo: MAJOR (rompe compatibilidad)

git commit -m "feat!: Cambiar formato JSON de profesores a v2

BREAKING CHANGE: La estructura del JSON de salida ha cambiado.

Antes:
{
  'name': '...',
  'overall_quality': 9.5
}

Ahora:
{
  'profesor': {
    'nombre': '...',
    'metricas': {
      'calidad': 9.5
    }
  }
}

Para migrar, actualizar parsers que consumen el JSON."

# Nueva versión: 2.0.0
git tag -a v2.0.0 -m "Version 2.0.0: Nuevo formato JSON v2"
```

#### Ejemplo 4: Implementar API REST
```bash
# Versión actual: 1.1.1
# Cambio: Nueva funcionalidad mayor
# Tipo: MINOR (nueva feature)

git commit -m "feat: Implementar API REST con FastAPI

- Crear módulo src/api/main.py
- Implementar endpoints para profesores y reseñas
- Agregar documentación OpenAPI automática
- Mantener compatibilidad con CLI existente"

# Nueva versión: 1.2.0
git tag -a v1.2.0 -m "Version 1.2.0: API REST con FastAPI"
```

### Regla de Oro para Copilot

**Cuando implementes CUALQUIER cambio:**

1. **Determina el tipo de cambio**:
   - ❓ ¿Rompe compatibilidad? → MAJOR
   - ❓ ¿Agrega funcionalidad nueva? → MINOR
   - ❓ ¿Solo corrige bugs? → PATCH

2. **Actualiza CHANGELOG.md**:
   - Mueve items de `[Unreleased]` a nueva versión `[X.Y.Z]`
   - Añade fecha actual
   - Documenta breaking changes si aplica

3. **Crea commit con tipo correcto**:
   - `feat:` para MINOR
   - `feat!:` o `BREAKING CHANGE:` para MAJOR
   - `fix:` para PATCH

4. **Sugiere el comando de tag**:
   ```bash
   git tag -a vX.Y.Z -m "Version X.Y.Z: Resumen"
   ```

### Decisión Automática de Versión - Checklist

**Para ayudarte a decidir, responde estas preguntas:**

```
¿El cambio ROMPE código existente que funciona?
├─ SÍ → MAJOR (X.0.0)
└─ NO ↓

¿El cambio AGREGA nueva funcionalidad?
├─ SÍ → MINOR (0.X.0)
└─ NO ↓

¿El cambio CORRIGE un bug o mejora internamente?
└─ SÍ → PATCH (0.0.X)
```

**Ejemplos de Breaking Changes:**
- ✅ Cambiar nombre de función pública
- ✅ Cambiar parámetros requeridos de función
- ✅ Cambiar formato de salida JSON
- ✅ Eliminar comando CLI
- ✅ Cambiar estructura de base de datos sin migración
- ✅ Cambiar contrato de API REST

**NO son Breaking Changes:**
- ❌ Agregar parámetros opcionales con default
- ❌ Agregar nuevos campos a JSON (si no se eliminan existentes)
- ❌ Agregar nuevos comandos CLI
- ❌ Refactorizar código interno
- ❌ Mejorar documentación

---

## 📊 Estructura de Datos

### Formato JSON de Profesor
```json
{
  "name": "Nombre Completo",
  "overall_quality": 9.5,
  "difficulty": 7.2,
  "recommend_percent": 95.0,
  "cached": false,
  "tags": [
    {"label": "EXCELENTE CLASE", "count": 25}
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
      "tags": ["BUENA ONDA"],
      "comment": "Excelente..."
    }
  ]
}
```

### Esquema Propuesto PostgreSQL (Futuro)
Ver `docs/TECHNICAL_DOCUMENTATION.md` sección 4.1 para esquema completo.

**Tablas principales:**
- `profesores` - Información básica
- `perfiles` - Snapshot temporal de métricas
- `resenias_metadata` - Datos estructurados
- `etiquetas` - Catálogo de tags
- `cursos` - Catálogo de materias

### Esquema Propuesto MongoDB (Futuro)
Ver `docs/TECHNICAL_DOCUMENTATION.md` sección 4.2.

**Colección `opiniones`:**
```javascript
{
  "_id": ObjectId("..."),
  "profesor_id": 123,
  "comentario": "...",
  "sentimiento": {
    "puntuacion": 0.95,
    "clasificacion": "positivo",
    "aspectos": {...}
  }
}
```

---

## 🐛 Issues Conocidos y Soluciones

### AttributeError en Parser
**Problema:** `'str' object has no attribute 'get_text'`
**Solución:** Ver pattern seguro en sección "Buenas Prácticas"

### Timeouts en Búsqueda
**Solución implementada:** Navegación directa por href (no por clic)
Ver `src/mp/scrape_prof.py::find_and_scrape()` función `_norm()`

### Paginación Limitada
**Solución implementada:** URL directa `?pag={n}` sin límite artificial

---

## 📚 Recursos Externos

- **MisProfesores.com** - Fuente de reseñas
- **Directorio UAM** - https://sistemas.azc.uam.mx/Somos/Directorio/
- **Playwright Docs** - https://playwright.dev/python/
- **BeautifulSoup Docs** - https://www.crummy.com/software/BeautifulSoup/
- **Tenacity Docs** - https://tenacity.readthedocs.io/

---

## ⚠️ Restricciones y Consideraciones

### Ético/Legal
- ⚠️ Uso educativo únicamente
- ⚠️ Respetar Terms of Service de sitios scrapeados
- ⚠️ Rate limiting obligatorio (evitar sobrecarga)
- ⚠️ User agent realista configurado

### Técnico
- ⚠️ Timeouts conservadores (45s navegación, 30s selectores)
- ⚠️ Máximo 4 reintentos con backoff exponencial
- ⚠️ Delays variables 2-4s entre requests
- ⚠️ Caché para evitar scraping redundante

---

## 🎓 Ejemplos de Uso para Copilot

### "Implementa persistencia en PostgreSQL"
1. Leer `docs/TECHNICAL_DOCUMENTATION.md` sección 4.1
2. Crear módulo `src/db/postgres.py`
3. Implementar esquema propuesto
4. Crear función `guardar_profesor_completo()`
5. Integrar con `scrape_prof.py`
6. Actualizar `CHANGELOG.md`

### "Agrega análisis de sentimiento"
1. Leer `docs/TECHNICAL_DOCUMENTATION.md` sección 6 (Job 3)
2. Crear módulo `src/ml/sentiment.py`
3. Cargar modelo BERT español
4. Implementar `analizar_sentimiento(comentario)`
5. Crear worker asíncrono
6. Actualizar esquema MongoDB

### "Crea API REST endpoint para profesores"
1. Leer `docs/TECHNICAL_DOCUMENTATION.md` sección 5.3.1
2. Crear módulo `src/api/main.py` con FastAPI
3. Implementar endpoints propuestos
4. Añadir validación con Pydantic
5. Documentar con OpenAPI
6. Actualizar README con endpoints

---

## 🔄 Workflow de Desarrollo Recomendado

1. **Leer contexto** - Este archivo + CHANGELOG + TECHNICAL_DOCUMENTATION
2. **Planificar** - Identificar módulos afectados
3. **Implementar** - Seguir buenas prácticas
4. **Probar** - Validar con casos reales
5. **Documentar** - Actualizar archivos relevantes
6. **Commit** - Convención establecida

---

**Última actualización:** 2024-11-08
**Versión del proyecto:** 1.0.0
**Mantenedores:** Equipo SentimentInsightUAM - UAM Azcapotzalco

---

## 📝 Notas Adicionales para Copilot

- Siempre prioriza **código async** sobre sync
- Siempre implementa **manejo de errores robusto**
- Siempre respeta **rate limiting** (evitar bloqueos)
- Siempre consulta **CHANGELOG.md** antes de sugerir features
- Siempre mantén **consistencia con código existente**
- Prefiere **código explícito** sobre implícito
- Documenta **decisiones de diseño** importantes
- **Siempre determina y sugiere la nueva versión** al finalizar implementación
- **Siempre actualiza CHANGELOG.md** con la nueva versión antes de commit
- **Siempre indica el tipo de commit** (feat/fix/refactor) apropiado
