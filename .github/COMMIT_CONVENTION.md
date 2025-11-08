# Convención de Commits - SentimentInsightUAM

Este documento define la convención de commits que debe seguirse en el proyecto **SentimentInsightUAM**. Utilizamos **Conventional Commits** para mantener un historial claro y semántico.

## 📐 Formato General

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

**Última actualización**: Noviembre 2025  
**Mantenido por**: Equipo SentimentInsightUAM
