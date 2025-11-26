# Guía de Desarrollo - SentimentInsightUAM

**Versión**: 1.2.1  
**Última actualización**: 2025-11-26

Esta guía proporciona instrucciones para desarrolladores que deseen contribuir o modificar el proyecto SentimentInsightUAM.

---

## 📋 Tabla de Contenidos

1. [Requisitos del Sistema](#requisitos-del-sistema)
2. [Configuración del Entorno](#configuración-del-entorno)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Flujo de Desarrollo](#flujo-de-desarrollo)
5. [Ejecutar el Proyecto](#ejecutar-el-proyecto)
6. [Debugging](#debugging)
7. [Tests](#tests)
8. [Convenciones de Código](#convenciones-de-código)
9. [Troubleshooting](#troubleshooting)

---

## 🔧 Requisitos del Sistema

### Software Requerido
- **Python** 3.11 o superior
- **Docker** >= 20.10 (para bases de datos)
- **Docker Compose** >= 2.0
- **Git** para control de versiones

### Verificar Instalaciones
```bash
# Python
python3 --version
# Salida esperada: Python 3.11.x o superior

# Docker
docker --version
# Salida esperada: Docker version 24.x.x

# Docker Compose
docker-compose --version
# Salida esperada: Docker Compose version v2.x.x

# Git
git --version
# Salida esperada: git version 2.x.x
```

---

## ⚙️ Configuración del Entorno

### 1. Clonar el Repositorio
```bash
git clone https://github.com/christianpm-gh/SentimentInsightUAM.git
cd SentimentInsightUAM
```

### 2. Crear Entorno Virtual
```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# Linux/macOS:
source venv/bin/activate

# Windows:
.\venv\Scripts\activate

# Verificar activación
which python
# Debe mostrar: .../SentimentInsightUAM/venv/bin/python
```

### 3. Instalar Dependencias
```bash
# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Instalar Playwright
python -m playwright install chromium
```

### 4. Configurar Variables de Entorno
```bash
# Copiar template de configuración
cp .env.example .env

# O si usas Docker, copiar configuración Docker
cp .env.docker .env

# Editar si es necesario
nano .env
```

### 5. Iniciar Bases de Datos (Docker)
```bash
# Opción 1: Usando Makefile (recomendado)
make docker-up

# Opción 2: Docker Compose directo
docker-compose up -d

# Verificar estado
make db-status
```

---

## 📁 Estructura del Proyecto

```
SentimentInsightUAM/
├── src/                    # Código fuente
│   ├── cli.py              # CLI principal
│   ├── core/               # Funcionalidades core
│   │   └── browser.py      # Context manager Playwright
│   ├── db/                 # Módulos de BD
│   │   ├── __init__.py     # Conexiones async
│   │   ├── models.py       # Modelos ORM
│   │   └── repository.py   # Persistencia dual
│   ├── mp/                 # Módulo MisProfesores
│   │   ├── parser.py       # Parser HTML
│   │   └── scrape_prof.py  # Scraper con caché
│   └── uam/                # Módulo UAM
│       └── nombres_uam.py  # Scraper directorio
├── data/                   # Datos
│   ├── inputs/             # Entradas
│   └── outputs/            # Salidas (HTML, JSON)
├── scripts/                # Scripts utilidad
├── tests/                  # Tests
├── docs/                   # Documentación
└── requirements.txt        # Dependencias
```

---

## 🔄 Flujo de Desarrollo

### Crear Nueva Rama
```bash
# Desde main/dev actualizado
git checkout main
git pull origin main

# Crear rama siguiendo convención
git checkout -b feat/mp/nueva-caracteristica
# Formato: tipo/alcance/descripcion
```

### Tipos de Rama Válidos
| Tipo | Uso |
|------|-----|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bugs |
| `refactor` | Refactorización |
| `docs` | Documentación |
| `test` | Tests |
| `chore` | Mantenimiento |

### Hacer Commits
```bash
# Formato: tipo(alcance): descripción
git commit -m "feat(mp): agrega soporte para nueva etiqueta"
git commit -m "fix(parser): corrige extracción de fechas"
git commit -m "docs(readme): actualiza instrucciones de instalación"
```

Ver [COMMIT_CONVENTION.md](/.github/COMMIT_CONVENTION.md) para más detalles.

---

## 🚀 Ejecutar el Proyecto

### Comandos CLI Principales

```bash
# Asegurar venv activo
source venv/bin/activate

# Extraer lista de profesores UAM
python -m src.cli nombres-uam

# Scrapear profesor individual (modo interactivo)
python -m src.cli prof

# Scrapear profesor por nombre
python -m src.cli prof --name "Juan Pérez García"

# Scrapear todos los profesores
python -m src.cli scrape-all
```

### Comandos de Base de Datos

```bash
# Iniciar contenedores
make docker-up

# Ver estado de BD
make db-status

# Conectar a PostgreSQL
make db-psql
# Dentro: \dt para ver tablas, \q para salir

# Conectar a MongoDB
make db-mongo
# Dentro: db.opiniones.find().limit(5)

# Detener contenedores
make docker-down

# Limpiar datos (CUIDADO)
make docker-clean
```

### Script de Limpieza de BD
```bash
# Modo interactivo
python scripts/clean_databases.py

# Limpiar todo sin confirmación
python scripts/clean_databases.py --all

# Solo PostgreSQL
python scripts/clean_databases.py --postgres

# Solo MongoDB
python scripts/clean_databases.py --mongo

# Solo verificar estado
python scripts/clean_databases.py --verify
```

---

## 🐛 Debugging

### Modo Verbose del Navegador
```bash
# Desactivar modo headless en .env
HEADLESS=false

# Ejecutar para ver navegador
python -m src.cli prof --name "Test"
```

### Logs de Docker
```bash
# Ver logs en tiempo real
make docker-logs

# Logs de servicio específico
docker-compose logs -f postgres
docker-compose logs -f mongodb
```

### Debugging de Scraper
```python
# En src/mp/scrape_prof.py, agregar prints temporales
print(f"DEBUG: URL navegada = {page.url}")
print(f"DEBUG: HTML length = {len(html)}")
print(f"DEBUG: Páginas encontradas = {pages}")
```

### Validar Datos en BD
```sql
-- En PostgreSQL (make db-psql)
SELECT id, nombre_limpio, slug FROM profesores ORDER BY id DESC LIMIT 5;
SELECT COUNT(*) FROM resenias_metadata;
SELECT * FROM historial_scraping ORDER BY timestamp DESC LIMIT 5;
```

```javascript
// En MongoDB (make db-mongo)
db.opiniones.countDocuments({});
db.opiniones.find().sort({fecha_extraccion: -1}).limit(5);
db.opiniones.find({"sentimiento_general.analizado": false}).count();
```

---

## 🧪 Tests

### Ejecutar Tests
```bash
# Asegurar venv activo y BD corriendo
source venv/bin/activate
make docker-up

# Ejecutar test específico
python tests/test_database_integration.py

# Ejecutar test de scraping
python tests/test_scrape_josue_padilla.py
```

### Estructura de Tests
```
tests/
├── test_database_integration.py  # Prueba de conexiones y BD
└── test_scrape_josue_padilla.py  # Prueba de scraping completo
```

### Escribir Nuevos Tests
```python
# Ejemplo de estructura de test
import asyncio

async def test_nueva_funcionalidad():
    """Descripción del test."""
    # Arrange
    datos_entrada = {...}
    
    # Act
    resultado = await funcion_a_testear(datos_entrada)
    
    # Assert
    assert resultado is not None
    assert resultado['campo'] == valor_esperado

if __name__ == "__main__":
    asyncio.run(test_nueva_funcionalidad())
```

---

## 📐 Convenciones de Código

### Estilo Python
- Seguir PEP 8
- Usar type hints en funciones
- Docstrings en español, estilo Google
- Nombres descriptivos en español

```python
async def obtener_profesor_por_id(profesor_id: int) -> Optional[dict]:
    """
    Obtiene un profesor por su ID.
    
    Args:
        profesor_id: ID único del profesor
        
    Returns:
        Dict con datos del profesor o None si no existe
    """
    # Implementación
    pass
```

### Manejo de Errores
```python
# Pattern recomendado
try:
    resultado = await operacion_riesgosa()
except Exception as e:
    print(f"Error en operación: {e}")
    # Continuar o manejar gracefully
```

### Elementos Opcionales en HTML
```python
# ✅ Correcto
elem = soup.select_one(".selector")
value = elem.get_text(strip=True) if elem else None

# ❌ Incorrecto (causa AttributeError)
value = (soup.select_one(".selector") or "").get_text(strip=True)
```

### Async/Await
- Todo código de I/O debe ser asíncrono
- Usar `async with` para context managers
- Evitar `asyncio.run()` dentro de funciones async

---

## 🔍 Troubleshooting

### Error: ModuleNotFoundError
```bash
# Solución: Activar venv e instalar dependencias
source venv/bin/activate
pip install -r requirements.txt
```

### Error: Playwright no instalado
```bash
# Solución: Instalar navegador
python -m playwright install chromium
```

### Error: Conexión a BD fallida
```bash
# Verificar que Docker esté corriendo
docker ps

# Verificar estado de contenedores
make db-status

# Reiniciar contenedores
make docker-restart
```

### Error: Puerto ya en uso
```bash
# Verificar qué usa el puerto
sudo lsof -i :5432  # PostgreSQL
sudo lsof -i :27017 # MongoDB

# Detener servicio conflictivo
sudo systemctl stop postgresql
sudo systemctl stop mongod
```

### Error: Timeout en scraping
```bash
# Aumentar timeouts en .env
RATE_MIN_MS=500
RATE_MAX_MS=1500

# Verificar conectividad
curl -I https://www.misprofesores.com
```

### Limpiar y reiniciar todo
```bash
# Detener contenedores
make docker-down

# Limpiar volúmenes (CUIDADO: elimina datos)
docker-compose down -v

# Reiniciar
make docker-up

# Reinstalar dependencias
pip install -r requirements.txt
python -m playwright install chromium
```

---

## 📚 Referencias Rápidas

### Comandos Make Disponibles
```bash
make help          # Ver todos los comandos
make docker-up     # Iniciar BD
make docker-down   # Detener BD
make db-status     # Estado de BD
make db-psql       # Shell PostgreSQL
make db-mongo      # Shell MongoDB
make install       # Instalar dependencias
```

### URLs Útiles
- **MisProfesores.com**: https://www.misprofesores.com/
- **Directorio UAM**: https://sistemas.azc.uam.mx/Somos/Directorio/

### Archivos de Configuración
- `.env` - Variables de entorno
- `docker-compose.yml` - Configuración Docker
- `requirements.txt` - Dependencias Python

### Documentación Relacionada
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Arquitectura del sistema
- [TECHNICAL_DOCUMENTATION.md](./TECHNICAL_DOCUMENTATION.md) - Documentación técnica
- [CONTRIBUTING.md](/.github/CONTRIBUTING.md) - Guía de contribución
- [COMMIT_CONVENTION.md](/.github/COMMIT_CONVENTION.md) - Convención de commits

---

**Mantenedores**: Equipo SentimentInsightUAM - UAM Azcapotzalco
