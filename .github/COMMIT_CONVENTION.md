# Convención de Commits y Versionado - SentimentInsightUAM

Este documento define la convención de commits y versionado semántico que debe seguirse en el proyecto **SentimentInsightUAM**. Utilizamos **Conventional Commits** para mantener un historial claro y **Semantic Versioning** para numerar versiones.

---

## 📋 Tabla de Contenidos

1. [Versionado Semántico](#-versionado-semántico)
2. [Convención de Commits](#-convención-de-commits)
3. [Workflow de Versionado](#-workflow-de-versionado)
4. [Ejemplos Prácticos de Versionado](#-ejemplos-prácticos-de-versionado)

---

## 🏷️ Versionado Semántico

Seguimos [Semantic Versioning 2.0.0](https://semver.org/lang/es/).

### Formato: MAJOR.MINOR.PATCH

**Versión actual del proyecto**: Ver `CHANGELOG.md`

### Cuándo Incrementar Cada Dígito

#### MAJOR (X.0.0) - Cambios Incompatibles ⚠️
Incrementa cuando haces cambios incompatibles con versiones anteriores.

**Ejemplos que requieren MAJOR:**
- ✅ Cambiar estructura de JSON de salida
- ✅ Eliminar o renombrar comandos CLI existentes
- ✅ Cambiar parámetros requeridos de funciones públicas
- ✅ Modificar esquema de base de datos sin ruta de migración
- ✅ Cambiar contratos de API REST (eliminar endpoints, cambiar respuestas)

**Commit debe incluir `!` o `BREAKING CHANGE:`:**
```bash
git commit -m "feat!: cambiar formato de salida JSON a v2

BREAKING CHANGE: La estructura del JSON cambió de flat a nested.
Ver CHANGELOG.md para guía de migración."
```

#### MINOR (0.X.0) - Nueva Funcionalidad ✨
Incrementa cuando agregas funcionalidad de forma compatible.

**Ejemplos que requieren MINOR:**
- ✅ Nuevo comando CLI (`scrape-all`)
- ✅ Nueva tabla en base de datos
- ✅ Nuevo endpoint en API
- ✅ Nuevos parámetros opcionales con valores por defecto
- ✅ Implementación de módulo completo (API REST, BERT, etc.)

**Commit debe usar `feat:`:**
```bash
git commit -m "feat(cli): agrega comando scrape-all para scraping masivo"
```

#### PATCH (0.0.X) - Correcciones 🐛
Incrementa cuando haces correcciones compatibles.

**Ejemplos que requieren PATCH:**
- ✅ Corrección de bugs
- ✅ Refactorizaciones internas
- ✅ Optimizaciones de rendimiento menores
- ✅ Correcciones de documentación
- ✅ Actualización de dependencias sin breaking changes

**Commit debe usar `fix:`, `refactor:`, `docs:`, `perf:`:**
```bash
git commit -m "fix(parser): corrige AttributeError en elementos None"
```

### Árbol de Decisión

```
¿El cambio ROMPE código existente?
├─ SÍ → MAJOR (X.0.0)
│   Usa: feat! o BREAKING CHANGE
│
└─ NO ↓
   ¿El cambio AGREGA funcionalidad?
   ├─ SÍ → MINOR (0.X.0)
   │   Usa: feat:
   │
   └─ NO ↓
      ¿El cambio CORRIGE o MEJORA?
      └─ SÍ → PATCH (0.0.X)
          Usa: fix:, refactor:, docs:, perf:
```

---

## 📐 Convención de Commits

```
<tipo>(<alcance>): <resumen en imperativo en español>
```

**Nota**: La explicación detallada debe ir en la descripción del Pull Request, no en el cuerpo del commit.

### Componentes

1. **Tipo**: Define la naturaleza del cambio (obligatorio)
2. **Alcance**: Especifica el módulo o área afectada (recomendado)
3. **Resumen**: Descripción breve en imperativo (obligatorio, max 72 caracteres)

---

## 🏷️ Tipos de Commit

### Tipos Principales

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `feat` | Nueva funcionalidad | `feat(mp): agrega parseo de etiquetas` |
| `fix` | Corrección de bugs | `fix(core): corrige timeout en navegación` |
| `docs` | Documentación | `docs(readme): actualiza guía de instalación` |
| `refactor` | Refactorización de código | `refactor(parser): simplifica extracción de fechas` |
| `test` | Adición o modificación de pruebas | `test(mp): agrega casos para scraper` |
| `perf` | Mejoras de rendimiento | `perf(uam): optimiza búsqueda de profesores` |
| `style` | Cambios de formato (sin afectar lógica) | `style(cli): formatea con black` |
| `chore` | Tareas de mantenimiento | `chore(deps): actualiza playwright a 1.46` |
| `build` | Cambios en sistema de build | `build(setup): configura entorno Docker` |
| `ci` | Cambios en CI/CD | `ci(github): agrega workflow de tests` |
| `revert` | Reversión de commits anteriores | `revert: revierte "feat(mp): cache"` |

---

## 🎯 Alcances del Proyecto

### Alcances Actuales

| Alcance | Descripción | Archivos Típicos |
|---------|-------------|------------------|
| `core` | Funcionalidades centrales | `src/core/browser.py` |
| `mp` | Módulo MisProfesores | `src/mp/*.py` |
| `uam` | Módulo directorio UAM | `src/uam/*.py` |
| `cli` | Interfaz de línea de comandos | `src/cli.py` |
| `data` | Manejo de datos y persistencia | `data/` |
| `docs` | Documentación del proyecto | `docs/`, `README.md` |

### Alcances Futuros (Planeados)

| Alcance | Descripción |
|---------|-------------|
| `api` | API REST con FastAPI |
| `db` | Esquemas y migraciones de BD |
| `bert` | Análisis de sentimiento |
| `jobs` | Sistema de jobs programados |
| `frontend` | Dashboard de visualización |

---

## ✍️ Reglas de Redacción

### 1. Resumen (Primera Línea)

- **Imperativo**: "agrega", "corrige", "actualiza" (NO "agregado", "corrigiendo")
- **Español**: Todos los mensajes en español
- **Minúsculas**: Comienza con minúscula después del alcance
- **Sin punto final**: No terminar con punto
- **Máximo 72 caracteres**: Preferiblemente más corto

#### ✅ Correcto
```
feat(mp): agrega parseo de calificaciones del perfil
fix(core): corrige user-agent en contexto de navegador
docs(cli): documenta comando scrape-all
```

#### ❌ Incorrecto
```
feat(mp): Agregado el parseo de calificaciones.
fix(core): Corrigiendo el user-agent
docs: actualización de documentación
```

### 2. Contexto Adicional

- **Detalles**: Van en la descripción del Pull Request
- **POR QUÉ**: Explica el razonamiento en el PR
- **CÓMO**: Describe la implementación en el PR
- **Referencias**: Incluye enlaces a issues/tareas en el PR

El commit debe ser **simple y directo**. El PR proporciona el contexto completo.

---

## 📋 Ejemplos por Categoría

### Nuevas Funcionalidades (`feat`)

```bash
feat(mp): agrega paginación automática de reseñas

feat(uam): implementa clic automático en "Ver más Profesorado"

feat(cli): agrega comando scrape-all para procesamiento masivo
```

### Corrección de Bugs (`fix`)

```bash
fix(parser): corrige AttributeError en extracción de curso

fix(core): ajusta timeouts para evitar fallos en conexiones lentas
```

### Refactorización (`refactor`)

```bash
refactor(mp): extrae lógica de normalización a función auxiliar

refactor(parser): simplifica manejo de fechas con diccionario de meses
```

### Documentación (`docs`)

```bash
docs(readme): agrega sección de caché inteligente

docs(technical): expande propuesta de esquema PostgreSQL

docs(contributing): crea guía de contribución para el equipo
```

### Pruebas (`test`)

```bash
test(mp): agrega casos de prueba para find_and_scrape

test(parser): valida manejo de HTML sin reseñas
```

### Rendimiento (`perf`)

```bash
perf(mp): reduce delays entre scraping de profesores

perf(parser): optimiza parsing con selectores CSS específicos
```

### Mantenimiento (`chore`)

```bash
chore(deps): actualiza playwright de 1.44 a 1.46

chore(gitignore): agrega .venv y outputs al ignore
```

### CI/CD (`ci`)

```bash
ci(github): agrega workflow de pruebas automáticas

ci(pre-commit): configura hooks de linting
```

---

## 🔄 Commits Múltiples vs Squash

### Cuándo Hacer Múltiples Commits

Usa commits separados cuando:

- Cada cambio tiene una **razón diferente**
- Los cambios afectan **módulos independientes**
- Quieres mantener **historial detallado** para revisión

#### Ejemplo de Commits Separados

```bash
git commit -m "feat(mp): agrega función de caché"
git commit -m "test(mp): agrega pruebas para caché"
git commit -m "docs(mp): documenta sistema de caché"
```

### Cuándo Hacer Squash

Considera squash cuando:

- Tienes commits de "fix typo", "ajusta formato"
- Los commits son **trabajo en progreso** (WIP)
- Quieres **historial limpio** en `main`/`dev`

#### Rebase Interactivo

```bash
# Squash últimos 3 commits
git rebase -i HEAD~3

# En el editor, marca commits con 's' (squash)
pick abc1234 feat(mp): agrega caché
s def5678 fix: corrige typo
s ghi9012 refactor: limpia código
```

---

## 🚀 Flujo de Trabajo Completo

### 1. Desarrollo Local

```bash
# Crear rama
git checkout -b feat/mp/cache-inteligente

# Commits incrementales
git add src/mp/scrape_prof.py
git commit -m "feat(mp): agrega función _get_cached_data"

git add src/mp/scrape_prof.py
git commit -m "feat(mp): implementa comparación de reseñas"

git add README.md docs/TECHNICAL_DOCUMENTATION.md
git commit -m "docs(mp): documenta sistema de caché"
```

### 2. Antes del Pull Request

Opcional: Limpia el historial si tienes muchos commits pequeños

```bash
# Rebase interactivo (si es necesario)
git rebase -i origin/dev

# Verifica que todo funciona
python -m src.cli prof --name "Test"

# Push
git push origin feat/mp/cache-inteligente
```

### 3. Pull Request

El título del PR debe seguir la misma convención:

```
feat(mp): implementa sistema de caché inteligente
```

---

## ⚠️ Anti-patrones Comunes

### ❌ Evitar

```bash
# Mensaje genérico
git commit -m "update files"

# Sin alcance cuando debería tenerlo
git commit -m "fix: corrige bug"

# Mezcla de tipos
git commit -m "feat: agrega caché y corrige parser"

# Demasiado largo (>72 caracteres)
git commit -m "feat(mp): agrega sistema de caché inteligente que detecta cambios y evita scraping redundante"
```

### ✅ Hacer

```bash
# Específico con alcance
git commit -m "fix(parser): corrige extracción de fechas nulas"

# Separar cambios de distinto tipo
git commit -m "feat(mp): implementa sistema de caché"
git commit -m "fix(parser): corrige manejo de elementos None"

# Conciso y descriptivo (<72 caracteres)
git commit -m "feat(mp): agrega caché con detección de cambios"
```

---

## 🛠️ Herramientas Útiles

### Commitizen

Para generar commits interactivamente:

```bash
pip install commitizen
cz commit
```

### Pre-commit Hooks

Valida mensajes de commit antes de aceptarlos:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.0.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
```

---

## 📚 Referencias

- [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
- [Angular Commit Guidelines](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit)
- [Semantic Versioning](https://semver.org/)

---

## 🔄 Workflow de Versionado

### Proceso Completo al Implementar una Feature

```bash
# 1. Crear rama (opcional pero recomendado)
git checkout -b feat/nombre-descriptivo

# 2. Implementar el cambio
# ... código ...

# 3. Determinar tipo de versión
# PREGUNTA: ¿Rompe compatibilidad? → MAJOR
# PREGUNTA: ¿Agrega funcionalidad? → MINOR
# PREGUNTA: ¿Solo corrige/mejora? → PATCH

# 4. Actualizar CHANGELOG.md
# - Crear sección [X.Y.Z] con fecha actual
# - Mover items de [Unreleased] si existen
# - Documentar el cambio en la sección apropiada (Added/Changed/Fixed)

# 5. Hacer commit con tipo correcto
git add .

# Para MINOR (nueva feature)
git commit -m "feat(scope): descripción de la feature"

# Para PATCH (bug fix)
git commit -m "fix(scope): descripción del fix"

# Para MAJOR (breaking change)
git commit -m "feat(scope)!: descripción

BREAKING CHANGE: Explicación de qué se rompió y cómo migrar"

# 6. Crear tag de versión
git tag -a vX.Y.Z -m "Version X.Y.Z: Resumen de cambios"

# 7. Push con tags
git push origin main --tags
```

### Checklist Pre-Versión

Antes de crear una nueva versión, verifica:

- [ ] ¿Identifiqué correctamente el tipo de versión (MAJOR/MINOR/PATCH)?
- [ ] ¿Actualicé `CHANGELOG.md` con la nueva versión y fecha?
- [ ] ¿El commit sigue la convención (feat/fix/refactor)?
- [ ] ¿Documenté breaking changes si los hay?
- [ ] ¿Actualicé README.md si la feature afecta el uso?
- [ ] ¿El código funciona correctamente?

---

## 📚 Ejemplos Prácticos de Versionado

### Ejemplo 1: Nueva Feature (MINOR)

**Implementar comando `scrape-all`**

```bash
# Versión actual: 1.0.0 → Nueva: 1.1.0

# 1. Implementar
# ... código en src/cli.py ...

# 2. Actualizar CHANGELOG.md
# Crear sección [1.1.0] - 2024-11-08
# ### Added
# - Comando `scrape-all` para scraping masivo

# 3. Commit
git add .
git commit -m "feat(cli): agrega comando scrape-all para scraping masivo

Implementa procesamiento automático de todos los profesores con:
- Caché inteligente por profesor
- Rate limiting con delays variables
- Resumen final con estadísticas"

# 4. Tag
git tag -a v1.1.0 -m "Version 1.1.0: Comando scrape-all"

# 5. Push
git push origin main --tags
```

### Ejemplo 2: Bug Fix (PATCH)

**Corregir AttributeError en parser**

```bash
# Versión actual: 1.1.0 → Nueva: 1.1.1

# 1. Corregir
# ... código en src/mp/parser.py ...

# 2. Actualizar CHANGELOG.md
# Crear sección [1.1.1] - 2024-11-08
# ### Fixed
# - AttributeError en parser cuando elementos HTML son None

# 3. Commit
git add .
git commit -m "fix(parser): corrige AttributeError en parse_reviews

Aplica pattern seguro de verificación antes de .get_text()
en 7 ubicaciones del parser"

# 4. Tag
git tag -a v1.1.1 -m "Version 1.1.1: Fix AttributeError"

# 5. Push
git push origin main --tags
```

### Ejemplo 3: Breaking Change (MAJOR)

**Cambiar formato JSON de salida**

```bash
# Versión actual: 1.1.1 → Nueva: 2.0.0

# 1. Implementar
# ... código ...

# 2. Actualizar CHANGELOG.md
# Crear sección [2.0.0] - 2024-11-08
# ### BREAKING CHANGES
# - Estructura de JSON cambiada a formato anidado
# ### Changed
# - Campo 'name' renombrado a 'profesor.nombre'

# 3. Commit con BREAKING CHANGE
git add .
git commit -m "feat(scraper)!: cambiar formato JSON a estructura anidada

BREAKING CHANGE: La estructura del JSON cambió completamente.

Antes: {\"name\": \"...\", \"reviews\": [...]}
Ahora: {\"profesor\": {\"nombre\": \"...\"}, \"resenias\": [...]}

Migración: Actualizar parsers que consumen el JSON."

# 4. Tag
git tag -a v2.0.0 -m "Version 2.0.0: Nuevo formato JSON"

# 5. Push
git push origin main --tags
```

### Ejemplo 4: Implementar API REST (MINOR)

**Nueva funcionalidad mayor**

```bash
# Versión actual: 1.1.1 → Nueva: 1.2.0

# 1. Implementar
# ... código en src/api/ ...

# 2. Actualizar CHANGELOG.md
# Crear sección [1.2.0] - 2024-11-08
# ### Added
# - API REST con FastAPI
# - Endpoints: GET /profesores, GET /profesores/{id}

# 3. Commit
git add .
git commit -m "feat(api): implementa API REST con FastAPI

Nuevas funcionalidades:
- Endpoints para consulta de profesores y reseñas
- Documentación OpenAPI en /docs
- Validación con Pydantic
- Paginación en listados"

# 4. Tag
git tag -a v1.2.0 -m "Version 1.2.0: API REST"

# 5. Push
git push origin main --tags
```

---

## 🎯 Regla de Oro para Copilot/Agentes

**Al finalizar CUALQUIER implementación:**

1. **Determina la versión**: Usa el árbol de decisión
2. **Actualiza CHANGELOG.md**: Con nueva versión y fecha
3. **Commit con tipo correcto**: feat/fix/refactor según corresponda
4. **Crea tag**: `git tag -a vX.Y.Z -m "Version X.Y.Z: ..."`
5. **Sugiere push**: `git push origin main --tags`

---

**Última actualización**: 2024-11-08  
**Mantenido por**: Equipo SentimentInsightUAM

---

## 📚 Referencias

- [Semantic Versioning 2.0.0](https://semver.org/lang/es/)
- [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
- [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/)
