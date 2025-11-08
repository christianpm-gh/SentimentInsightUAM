# Guía de Contribución - SentimentInsightUAM

## 🔀 Flujo de Trabajo con Git

### Configuración Inicial

Antes de comenzar a trabajar, configura tu identidad de Git:

```bash
git config user.name "tu-usuario-github"
git config user.email "tu-email@example.com"
```

### Estructura de Ramas

Este proyecto utiliza las siguientes ramas:

- **`main`**: Rama principal (estable y protegida)
- **`dev`**: Rama de integración para desarrollo
- **`tipo/alcance/descripcion`**: Ramas de trabajo temporal

#### Tipos de Rama

Los tipos válidos para ramas son:

- `feat`: Nueva funcionalidad
- `fix`: Corrección de bugs
- `refactor`: Refactorización de código
- `perf`: Mejoras de rendimiento
- `chore`: Tareas de mantenimiento
- `build`: Cambios en el sistema de build
- `ci`: Cambios en CI/CD
- `docs`: Documentación
- `test`: Pruebas
- `style`: Formato de código
- `revert`: Reversión de cambios

#### Alcances Sugeridos

- `core`: Funcionalidades centrales del sistema
- `mp`: Módulo de MisProfesores
- `uam`: Módulo del directorio UAM
- `cli`: Interfaz de línea de comandos
- `data`: Manejo de datos y persistencia
- `api`: API REST (futuro)
- `db`: Base de datos (futuro)

### Ejemplos de Nombres de Ramas

```bash
feat/mp/paginacion-resenas
fix/core/backoff-timeouts
refactor/uam/normaliza-nombres
docs/workflow/guia-contribucion
```

## 📝 Conventional Commits

### Formato

```
<tipo>(<alcance>): <resumen en imperativo en español>

[Sin cuerpo, la explicacion debe ir en la descripcion del PR]
```

### Reglas

1. **Resumen**: Máximo 72 caracteres
2. **Tiempo verbal**: Imperativo ("agrega", "corrige", no "agregado" o "agregando")
3. **Idioma**: Español para mensajes de commit
4. **Cuerpo**: Opcional, explica el contexto y razonamiento
5. **Referencias**: Incluye enlaces a tareas de Asana si aplica

### Ejemplos de Commits

#### Ejemplos de Commits

```bash
# Feature
git commit -m "feat(mp): agrega parseo de métricas de perfil"

# Fix
git commit -m "fix(core): corrige user-agent en contexto de navegador"

# Refactor
git commit -m "refactor(uam): simplifica extracción de nombres del directorio"

# Documentación
git commit -m "docs(cli): documenta flags de la línea de comandos"
```

## 🔄 Flujo de Trabajo Completo

### 1. Crear Rama de Trabajo

```bash
# Asegúrate de estar en dev actualizado
git checkout dev
git pull origin dev

# Crea tu rama de trabajo
git checkout -b tipo/alcance/descripcion-breve
```

### 2. Realizar Cambios

- Haz commits pequeños y atómicos
- Cada commit debe representar una unidad lógica de cambio
- Usa mensajes descriptivos siguiendo Conventional Commits

```bash
# Ejemplo de commits incrementales
git add src/mp/parser.py
git commit -m "feat(mp): agrega función auxiliar para normalizar fechas"

git add tests/test_parser.py
git commit -m "test(mp): agrega pruebas para normalización de fechas"

git add README.md
git commit -m "docs(mp): documenta formato de fechas esperado"
```

### 3. Push a Remoto

```bash
git push origin tipo/alcance/descripcion-breve
```

### 4. Crear Pull Request

1. Ve a GitHub y crea un Pull Request hacia `dev`
2. **Título del PR**: Usa el mensaje del primer commit (o un resumen general)
3. **Descripción**: Incluye:
   - Qué cambios se hicieron
   - Por qué se hicieron
   - Checklist de pruebas locales
   - Referencias a issues o tareas

#### Plantilla de PR

```markdown
## Descripción

Breve descripción de los cambios realizados.

## Tipo de Cambio

- [ ] 🐛 Bug fix
- [ ] ✨ Nueva funcionalidad
- [ ] 📝 Documentación
- [ ] 🔧 Refactorización
- [ ] ⚡ Mejora de rendimiento

## Checklist de Pruebas

- [ ] Las pruebas existentes pasan
- [ ] Se agregaron nuevas pruebas (si aplica)
- [ ] El código sigue las convenciones del proyecto
- [ ] La documentación fue actualizada (si aplica)
- [ ] Se probó localmente en WSL/Ubuntu

## Referencias

- Asana: [enlace a la tarea]
- Relacionado con: #123
```

### 5. Revisión y Merge

1. Espera revisión del equipo
2. Realiza cambios solicitados si es necesario
3. Considera hacer rebase interactivo si hay muchos commits
4. **Merge squash** a `dev` una vez aprobado

### 6. Limpieza

```bash
# Después del merge, elimina tu rama local
git checkout dev
git pull origin dev
git branch -d tipo/alcance/descripcion-breve
```

## 🏷️ Versionado (SemVer)

Cuando se promueva código de `dev` a `main`, se creará un tag siguiendo **Semantic Versioning**:

```
vMAJOR.MINOR.PATCH
```

- **MAJOR**: Cambios incompatibles en la API
- **MINOR**: Nueva funcionalidad compatible
- **PATCH**: Correcciones de bugs

### Ejemplo

```bash
git tag -a v1.2.3 -m "Release version 1.2.3: Agrega análisis de sentimiento con BERT"
git push origin v1.2.3
```

## 🚫 Qué NO Hacer

- ❌ No hacer commit directo a `main` o `dev`
- ❌ No usar mensajes genéricos como "fix", "update", "changes"
- ❌ No mezclar múltiples tipos de cambios en un commit
- ❌ No hacer commits enormes con docenas de archivos
- ❌ No hacer push con código que no funciona
- ❌ No ignorar las pruebas antes de hacer PR

## 🤝 Trabajo con Agentes de Código IA

Al trabajar con agentes de código (como GitHub Copilot):

### Instrucciones para el Agente

1. **Siempre** seguir Conventional Commits
2. **Crear ramas** con nombres descriptivos siguiendo la convención
3. **Commits atómicos**: Un cambio lógico por commit
4. **Documentar**: Actualizar README y docs cuando sea relevante
5. **Pruebas**: Asegurar que el código funciona antes de commit

### Ejemplo de Prompt para Agente

```
Crea una rama feat/mp/cache-inteligente e implementa un sistema de caché
para detectar si un profesor ya fue scrapeado. Usa commits atómicos
siguiendo Conventional Commits. Actualiza la documentación relevante.
```

## 📚 Recursos

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Writing Good Commit Messages](https://chris.beams.io/posts/git-commit/)

---

**¿Preguntas?** Abre un issue en GitHub o contacta al equipo en Asana.
