# Git Workflow

Este repositorio usa Conventional Commits y ramas semánticas.

## Ramas
- `main`: estable y protegida.
- `dev`: integración.
- Feature/fix/refactor: `tipo/alcance/slug-kebab`.

**Tipos**: feat, fix, refactor, perf, chore, build, ci, docs, test, style, revert.

**Alcances sugeridos**: core, mp, uam, cli, data.

### Ejemplos de ramas
- `feat/mp/paginacion-resenas`
- `fix/core/backoff-timeouts`
- `refactor/uam/normaliza-nombres`

## Commits (Conventional Commits)

**Formato**:
```
<tipo>(<alcance>): <resumen en imperativo en español>
```

**Reglas**:
- 72 chars aprox. en el resumen.
- Cuerpo opcional con Por qué y Cómo.
- Referencias de tarea: `Asana: https://app.asana.com/...` o `Refs: ASANA-123`.

### Ejemplos
```
feat(mp): agrega parseo de métricas de perfil
fix(core): corrige user-agent aleatorio en contexto de navegador
refactor(uam): simplifica extracción de nombres del directorio
docs(cli): documenta flags de la línea de comandos
```

## Flujo de trabajo
1. Crea rama desde `dev`: `tipo/alcance/slug`.
2. Commits pequeños y atómicos.
3. PR hacia `dev` con título = primer commit. Incluye checklist de pruebas locales.
4. Rebase interactivo antes de merge si es necesario.
5. Merge squash a `dev`. Promociona a `main` cuando pase QA.

**Convenciones de tags**: `vX.Y.Z` siguiendo SemVer cuando aplique.

