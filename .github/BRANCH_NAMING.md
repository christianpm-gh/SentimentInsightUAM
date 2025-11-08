# Convención de Nombres de Ramas - SentimentInsightUAM

Este documento define la convención para nombrar ramas en el proyecto **SentimentInsightUAM**.

## 🌿 Formato General

```
<tipo>/<alcance>/<descripcion-en-kebab-case>
```

### Componentes

1. **Tipo**: Categoría del trabajo (feat, fix, docs, etc.)
2. **Alcance**: Módulo o área afectada (mp, uam, core, etc.)
3. **Descripción**: Resumen breve en kebab-case (palabras separadas por guiones)

---

## 🏷️ Tipos de Rama

| Tipo | Uso | Ejemplo |
|------|-----|---------|
| `feat` | Nueva funcionalidad | `feat/mp/paginacion-resenas` |
| `fix` | Corrección de bugs | `fix/core/timeout-navegacion` |
| `refactor` | Refactorización | `refactor/parser/simplifica-fechas` |
| `docs` | Documentación | `docs/readme/guia-instalacion` |
| `test` | Pruebas | `test/mp/casos-cache` |
| `perf` | Optimización | `perf/uam/busqueda-profesores` |
| `chore` | Mantenimiento | `chore/deps/actualiza-playwright` |
| `style` | Formato de código | `style/cli/aplica-black` |
| `build` | Sistema de build | `build/docker/configura-entorno` |
| `ci` | CI/CD | `ci/github/workflow-tests` |

---

## 🎯 Alcances Válidos

### Alcances Actuales

- `core` - Funcionalidades centrales (`src/core/`)
- `mp` - Módulo MisProfesores (`src/mp/`)
- `uam` - Módulo UAM (`src/uam/`)
- `cli` - Interfaz CLI (`src/cli.py`)
- `data` - Datos y persistencia (`data/`)
- `docs` - Documentación general
- `workflow` - Git workflow y procesos

### Alcances Futuros

- `api` - API REST
- `db` - Base de datos
- `bert` - Análisis de sentimiento
- `jobs` - Jobs programados
- `frontend` - Dashboard

---

## ✍️ Reglas de Descripción

1. **Kebab-case**: Palabras en minúsculas separadas por guiones
2. **Conciso**: 2-4 palabras que describan el cambio
3. **Descriptivo**: Debe indicar QUÉ se está trabajando
4. **Español**: Preferiblemente en español

### ✅ Ejemplos Correctos

```
feat/mp/paginacion-resenas
fix/parser/atributo-error-fechas
refactor/uam/extraccion-nombres
docs/technical/propuesta-api
test/mp/scraper-cache
perf/core/optimiza-timeouts
chore/gitignore/agrega-venv
```

### ❌ Ejemplos Incorrectos

```
feature/mp/pagination  # Usar 'feat', no 'feature'
fix/bug-in-parser      # Falta alcance específico
mp/fix/dates           # Orden incorrecto
feat-mp-pagination     # Usar '/', no '-' entre secciones
FEAT/MP/PAGINATION     # Usar minúsculas
```

---

## 📋 Ejemplos por Categoría

### Features (Nuevas Funcionalidades)

```bash
feat/mp/cache-inteligente
feat/uam/clic-automatico-ver-mas
feat/cli/comando-scrape-all
feat/mp/persistencia-dual-html-json
feat/parser/extraccion-etiquetas
```

### Fixes (Correcciones)

```bash
fix/parser/atributo-error-elemento-none
fix/core/user-agent-contexto
fix/mp/timeout-busqueda
fix/cli/menu-seleccion-profesores
```

### Refactorización

```bash
refactor/mp/normaliza-texto-funcion
refactor/parser/simplifica-manejo-fechas
refactor/uam/elimina-codigo-duplicado
refactor/cli/mejora-legibilidad-menu
```

### Documentación

```bash
docs/readme/seccion-cache
docs/technical/arquitectura-bd
docs/contributing/guia-commits
docs/api/propuesta-endpoints
```

### Pruebas

```bash
test/mp/casos-find-and-scrape
test/parser/validacion-html-sin-resenas
test/uam/extraccion-nombres-vacia
```

### Rendimiento

```bash
perf/mp/reduce-delays-scraping
perf/parser/optimiza-selectores-css
perf/core/ajusta-timeouts
```

### Mantenimiento

```bash
chore/deps/actualiza-playwright-1.46
chore/gitignore/agrega-outputs
chore/requirements/limpia-dependencias
```

### CI/CD

```bash
ci/github/workflow-tests-automaticos
ci/pre-commit/hooks-linting
ci/docker/configura-imagen
```

---

## 🔄 Ciclo de Vida de una Rama

### 1. Creación

```bash
# Desde dev actualizado
git checkout dev
git pull origin dev

# Crear nueva rama
git checkout -b feat/mp/cache-inteligente
```

### 2. Desarrollo

```bash
# Trabajar en la rama
git add .
git commit -m "feat(mp): implementa función de caché"

# Push regularmente
git push origin feat/mp/cache-inteligente
```

### 3. Pull Request

- Crear PR hacia `dev`
- Título del PR similar al nombre de la rama
- Descripción detallada con checklist

### 4. Merge y Limpieza

```bash
# Después del merge en GitHub
git checkout dev
git pull origin dev

# Eliminar rama local
git branch -d feat/mp/cache-inteligente

# Eliminar rama remota (si no se borró en GitHub)
git push origin --delete feat/mp/cache-inteligente
```

---

## 🌳 Estructura de Ramas del Proyecto

```
main (protegida)
  ↑
  └── dev (integración)
       ↑
       ├── feat/mp/cache-inteligente
       ├── feat/uam/clic-automatico
       ├── fix/parser/atributo-error
       ├── docs/readme/actualizacion
       └── refactor/cli/mejora-menu
```

### Ramas Permanentes

- **`main`**: Código en producción, siempre estable
- **`dev`**: Integración continua, base para nuevas ramas

### Ramas Temporales

- Todas las ramas de trabajo (feat, fix, etc.)
- Se eliminan después del merge

---

## 🚫 Anti-patrones

### ❌ Evitar

```bash
# Nombres genéricos
fix/bug
feat/new-feature
update/code

# Sin alcance
feat/cache
fix/parser

# Demasiado largo
feat/mp/implementa-sistema-completo-de-cache-con-deteccion-automatica

# Mezcla de idiomas
feat/mp/smart-cache

# Snake_case o camelCase
feat/mp/smart_cache
feat/mp/smartCache

# Nombres ambiguos
feat/mp/mejoras
fix/mp/ajustes
```

### ✅ Hacer

```bash
# Específico y claro
feat/mp/cache-inteligente
fix/parser/extraccion-fechas
refactor/uam/normaliza-nombres

# Conciso pero descriptivo
feat/mp/persistencia-dual
fix/core/timeout-navegacion
docs/workflow/guia-ramas
```

---

## 🎯 Casos Especiales

### Múltiples Alcances

Si el trabajo afecta múltiples módulos, usa el alcance más relevante o más general:

```bash
# Afecta mp y parser → usar 'mp' (más alto nivel)
feat/mp/mejora-extraccion-completa

# Afecta toda la app → usar alcance general
refactor/core/estructura-proyecto
```

### Hotfixes Urgentes

Para correcciones críticas en producción:

```bash
hotfix/mp/corrige-crash-scraping
hotfix/core/soluciona-memory-leak
```

Estas ramas pueden crearse desde `main` y mergearse tanto a `main` como a `dev`.

### Ramas de Experimento

Para pruebas de concepto o experimentos:

```bash
experiment/bert/prueba-modelo-sentimiento
experiment/api/test-fastapi
spike/db/evaluacion-postgresql
```

Estas pueden no seguir estrictamente la convención y pueden descartarse.

---

## 📊 Estadísticas Recomendadas

### Vida de la Rama

- **Máximo**: 1-2 semanas de desarrollo activo
- **Commits**: 3-10 commits típicamente
- **Tamaño**: Cambios enfocados en una funcionalidad/corrección

### Cuándo Dividir una Rama

Si tu rama está creciendo mucho, considera dividirla:

```bash
# En lugar de:
feat/mp/sistema-completo-scraping

# Divide en:
feat/mp/busqueda-profesores
feat/mp/paginacion-resenas
feat/mp/cache-inteligente
```

---

## 🛠️ Herramientas

### Git Aliases Útiles

```bash
# Agregar a ~/.gitconfig
[alias]
  # Crear rama siguiendo convención
  new-feat = "!f() { git checkout -b feat/$1/$2; }; f"
  new-fix = "!f() { git checkout -b fix/$1/$2; }; f"
  new-docs = "!f() { git checkout -b docs/$1/$2; }; f"
  
  # Limpiar ramas merged
  clean-branches = "!git branch --merged | grep -v '\\*\\|main\\|dev' | xargs -n 1 git branch -d"
```

### Uso

```bash
git new-feat mp cache-inteligente
# Crea: feat/mp/cache-inteligente

git new-fix parser fechas-nulas
# Crea: fix/parser/fechas-nulas
```

---

## 📚 Referencias

- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Trunk Based Development](https://trunkbaseddevelopment.com/)

---

**Última actualización**: Noviembre 2025  
**Mantenido por**: Equipo SentimentInsightUAM
