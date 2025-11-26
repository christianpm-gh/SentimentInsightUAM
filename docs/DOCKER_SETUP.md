# Guía de Configuración con Docker

**SentimentInsightUAM v1.2.1**

Esta guía te ayudará a configurar rápidamente las bases de datos PostgreSQL y MongoDB usando Docker y Docker Compose.

---

## 📋 Tabla de Contenidos

1. [¿Por qué Docker?](#por-qué-docker)
2. [Requisitos Previos](#requisitos-previos)
3. [Instalación de Docker](#instalación-de-docker)
4. [Configuración Rápida](#configuración-rápida)
5. [Comandos Útiles](#comandos-útiles)
6. [Arquitectura de Contenedores](#arquitectura-de-contenedores)
7. [Verificación](#verificación)
8. [Gestión de Datos](#gestión-de-datos)
9. [Troubleshooting](#troubleshooting)
10. [Comparativa: Docker vs Manual](#comparativa-docker-vs-manual)

---

## 🐳 ¿Por qué Docker?

### Ventajas

- ✅ **Setup en 2 minutos** vs 30-45 minutos de instalación manual
- ✅ **Mismo entorno** en Windows, macOS y Linux
- ✅ **Scripts de inicialización** ejecutados automáticamente
- ✅ **Aislamiento total** del sistema host
- ✅ **Fácil reset** de datos con un solo comando
- ✅ **No requiere** instalación de PostgreSQL/MongoDB en el sistema
- ✅ **Ideal para desarrollo** y testing

### Cuándo NO usar Docker

- ⚠️ Servidores de producción (mejor usar servicios gestionados como AWS RDS, MongoDB Atlas)
- ⚠️ Entornos con restricciones de rendimiento extremas (penalización ~5-10%)
- ⚠️ Sistemas sin soporte para virtualización

---

## 🔧 Requisitos Previos

### Software Necesario

- **Docker** >= 20.10
- **Docker Compose** >= 2.0 (incluido en Docker Desktop)
- **Make** (opcional, para usar Makefile)

### Espacio en Disco

- ~500 MB para imágenes Docker
- ~1-5 GB para datos de bases de datos (dependiendo del scraping)

---

## 📥 Instalación de Docker

### Ubuntu/Debian

```bash
# Actualizar paquetes
sudo apt update

# Instalar dependencias
sudo apt install ca-certificates curl gnupg

# Agregar clave GPG oficial de Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Agregar repositorio de Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Agregar usuario al grupo docker (opcional, para no usar sudo)
sudo usermod -aG docker $USER
newgrp docker
```

### macOS

```bash
# Opción 1: Homebrew
brew install --cask docker

# Opción 2: Descarga manual
# Descargar desde https://www.docker.com/products/docker-desktop/
```

### Fedora/RHEL/CentOS

```bash
# Instalar Docker
sudo dnf install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Iniciar servicio
sudo systemctl start docker
sudo systemctl enable docker

# Agregar usuario al grupo docker
sudo usermod -aG docker $USER
newgrp docker
```

### Windows

1. Descargar **Docker Desktop** desde [docker.com](https://www.docker.com/products/docker-desktop/)
2. Instalar y reiniciar
3. Habilitar WSL 2 si se solicita
4. Abrir terminal (PowerShell o WSL2)

### Verificar Instalación

```bash
# Verificar Docker
docker --version
# Salida esperada: Docker version 24.x.x

# Verificar Docker Compose
docker-compose --version
# Salida esperada: Docker Compose version v2.x.x

# Probar Docker
docker run hello-world
```

---

## 🚀 Configuración Rápida

### 1. Configurar Variables de Entorno

```bash
# Navegar al directorio del proyecto
cd /ruta/a/SentimentInsightUAM

# Copiar archivo de configuración
cp .env.docker .env

# (Opcional) Editar contraseñas para producción
nano .env
```

### 2. Iniciar Contenedores

**Opción A: Con Makefile (Recomendado)**

```bash
# Ver comandos disponibles
make help

# Iniciar bases de datos
make docker-up
```

**Opción B: Docker Compose directo**

```bash
# Iniciar contenedores en segundo plano
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### 3. Verificar Estado

```bash
# Con Makefile
make db-status

# O manualmente
docker ps
```

**Salida esperada:**

```
CONTAINER ID   IMAGE                 STATUS         PORTS                    NAMES
abc123def456   postgres:15-alpine    Up 30 seconds  0.0.0.0:5432->5432/tcp   sentiment_postgres
xyz789uvw012   mongo:7.0             Up 30 seconds  0.0.0.0:27017->27017/tcp sentiment_mongo
```

---

## 💻 Comandos Útiles

### Gestión de Contenedores

```bash
# Iniciar contenedores
make docker-up
# o: docker-compose up -d

# Detener contenedores
make docker-down
# o: docker-compose down

# Reiniciar contenedores
make docker-restart

# Ver logs en tiempo real
make docker-logs
# o: docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f postgres
docker-compose logs -f mongodb
```

### Gestión de Bases de Datos

```bash
# Verificar estado
make db-status

# Conectar a PostgreSQL (shell interactivo)
make db-psql
# o: docker exec -it sentiment_postgres psql -U sentiment_admin -d sentiment_uam_db

# Conectar a MongoDB (mongosh)
make db-mongo
# o: docker exec -it sentiment_mongo mongosh -u sentiment_admin -p dev_password_2024 --authenticationDatabase sentiment_uam_nlp sentiment_uam_nlp

# Reiniciar bases de datos (DESTRUYE DATOS)
make db-reset
```

### Consultas de Verificación

**PostgreSQL:**

```bash
# Listar tablas
docker exec sentiment_postgres psql -U sentiment_admin -d sentiment_uam_db -c "\dt"

# Contar etiquetas iniciales (debe ser 21)
docker exec sentiment_postgres psql -U sentiment_admin -d sentiment_uam_db -c "SELECT COUNT(*) FROM etiquetas;"

# Ver estructura de tabla
docker exec sentiment_postgres psql -U sentiment_admin -d sentiment_uam_db -c "\d profesores"
```

**MongoDB:**

```bash
# Listar colecciones
docker exec sentiment_mongo mongosh -u sentiment_admin -p dev_password_2024 \
  --authenticationDatabase sentiment_uam_nlp \
  --eval "db.getCollectionNames()" sentiment_uam_nlp

# Verificar índices
docker exec sentiment_mongo mongosh -u sentiment_admin -p dev_password_2024 \
  --authenticationDatabase sentiment_uam_nlp \
  --eval "db.opiniones.getIndexes()" sentiment_uam_nlp
```

---

## 🏗️ Arquitectura de Contenedores

### Servicios

```
┌─────────────────────────────────────────────────────────┐
│              SentimentInsightUAM Docker                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────┐         ┌──────────────────┐    │
│  │   PostgreSQL     │         │     MongoDB      │    │
│  │   15-alpine      │         │      7.0         │    │
│  ├──────────────────┤         ├──────────────────┤    │
│  │ Puerto: 5432     │         │ Puerto: 27017    │    │
│  │ Usuario: sent... │         │ Usuario: sent... │    │
│  │ DB: sentiment... │         │ DB: sentiment... │    │
│  └────────┬─────────┘         └─────────┬────────┘    │
│           │                             │             │
│           │   sentiment_network (bridge)│             │
│           └─────────────────────────────┘             │
│                                                         │
│  ┌──────────────────┐         ┌──────────────────┐    │
│  │ Volumen:         │         │ Volumen:         │    │
│  │ postgres_data    │         │ mongo_data       │    │
│  │ (Persistente)    │         │ (Persistente)    │    │
│  └──────────────────┘         └──────────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘
         ▲                               ▲
         │                               │
         └───── Aplicación Python ───────┘
              (src/db/postgres.py)
              (src/db/mongodb.py)
```

### Volúmenes Persistentes

Los datos se almacenan en **volúmenes de Docker** que persisten aunque se detengan los contenedores:

- `sentiment_postgres_data` - Datos de PostgreSQL
- `sentiment_mongo_data` - Datos de MongoDB
- `sentiment_mongo_config` - Configuración de MongoDB

### Scripts de Inicialización

Al primer arranque, se ejecutan automáticamente:

1. **PostgreSQL**: `scripts/init_postgres.sql`
   - Crea base de datos `sentiment_uam_db`
   - Instala extensiones (`unaccent`, `pg_trgm`)
   - Crea 8 tablas
   - Crea 2 vistas (1 materializada)
   - Inserta 21 etiquetas iniciales

2. **MongoDB**: `scripts/init_mongo.js` + `scripts/setup_mongo_user.sh`
   - Crea base de datos `sentiment_uam_nlp`
   - Crea colección `opiniones` con validación JSON Schema
   - Crea 8 índices especializados
   - Crea usuario `sentiment_admin` con permisos

---

## ✅ Verificación

### 1. Verificar Contenedores en Ejecución

```bash
docker ps
```

**Esperado**: 2 contenedores (`sentiment_postgres`, `sentiment_mongo`) con estado `Up`

### 2. Verificar Health Checks

```bash
docker inspect sentiment_postgres | grep -A 5 Health
docker inspect sentiment_mongo | grep -A 5 Health
```

**Esperado**: `"Status": "healthy"`

### 3. Verificar PostgreSQL

```bash
# Listar tablas
make db-psql
# Dentro del shell:
\dt
\q
```

**Esperado**: 8 tablas listadas

### 4. Verificar MongoDB

```bash
# Listar colecciones
make db-mongo
# Dentro del shell:
db.getCollectionNames()
exit
```

**Esperado**: `['opiniones', 'sentimiento_cache', 'system.js']`

### 5. Probar Conexión desde Python

```python
# test_connection.py
import asyncio
import asyncpg
from motor.motor_asyncio import AsyncIOMotorClient

async def test_postgres():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='sentiment_admin',
        password='dev_password_2024',
        database='sentiment_uam_db'
    )
    tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname='public'")
    print(f"✅ PostgreSQL conectado. Tablas: {len(tables)}")
    await conn.close()

async def test_mongo():
    client = AsyncIOMotorClient('mongodb://sentiment_admin:dev_password_2024@localhost:27017/sentiment_uam_nlp?authSource=sentiment_uam_nlp')
    db = client['sentiment_uam_nlp']
    collections = await db.list_collection_names()
    print(f"✅ MongoDB conectado. Colecciones: {collections}")
    client.close()

asyncio.run(test_postgres())
asyncio.run(test_mongo())
```

```bash
# Ejecutar
python test_connection.py
```

---

## 💾 Gestión de Datos

### Backup de Datos

**PostgreSQL:**

```bash
# Backup completo
docker exec sentiment_postgres pg_dump -U sentiment_admin sentiment_uam_db > backup_postgres_$(date +%Y%m%d).sql

# Restaurar backup
docker exec -i sentiment_postgres psql -U sentiment_admin sentiment_uam_db < backup_postgres_20250109.sql
```

**MongoDB:**

```bash
# Backup completo
docker exec sentiment_mongo mongodump \
  --username sentiment_admin \
  --password dev_password_2024 \
  --authenticationDatabase sentiment_uam_nlp \
  --db sentiment_uam_nlp \
  --out /tmp/backup

# Copiar backup al host
docker cp sentiment_mongo:/tmp/backup ./backup_mongo_$(date +%Y%m%d)

# Restaurar backup
docker exec sentiment_mongo mongorestore \
  --username sentiment_admin \
  --password dev_password_2024 \
  --authenticationDatabase sentiment_uam_nlp \
  --db sentiment_uam_nlp \
  /tmp/backup/sentiment_uam_nlp
```

### Limpiar Datos

```bash
# Opción 1: Eliminar todos los datos y reiniciar
make db-reset

# Opción 2: Eliminar contenedores y volúmenes manualmente
docker-compose down -v

# Opción 3: Truncar tablas específicas (PostgreSQL)
docker exec sentiment_postgres psql -U sentiment_admin -d sentiment_uam_db -c "TRUNCATE TABLE profesores CASCADE;"
```

### Exportar Datos

**PostgreSQL a CSV:**

```bash
docker exec sentiment_postgres psql -U sentiment_admin -d sentiment_uam_db \
  -c "\COPY (SELECT * FROM profesores) TO '/tmp/profesores.csv' CSV HEADER"

docker cp sentiment_postgres:/tmp/profesores.csv ./profesores_export.csv
```

**MongoDB a JSON:**

```bash
docker exec sentiment_mongo mongoexport \
  --username sentiment_admin \
  --password dev_password_2024 \
  --authenticationDatabase sentiment_uam_nlp \
  --db sentiment_uam_nlp \
  --collection opiniones \
  --out /tmp/opiniones.json

docker cp sentiment_mongo:/tmp/opiniones.json ./opiniones_export.json
```

---

## 🐛 Troubleshooting

### Error: "Cannot connect to Docker daemon"

**Causa**: Docker no está iniciado o no tienes permisos

**Solución**:

```bash
# Iniciar Docker (Linux)
sudo systemctl start docker

# Agregar usuario al grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Reiniciar Docker Desktop (macOS/Windows)
```

### Error: "port is already allocated"

**Causa**: Puerto 5432 o 27017 ya en uso

**Solución**:

```bash
# Verificar qué usa el puerto
sudo lsof -i :5432
sudo lsof -i :27017

# Opción 1: Detener servicio conflictivo
sudo systemctl stop postgresql
sudo systemctl stop mongod

# Opción 2: Cambiar puerto en .env
# Editar .env y cambiar POSTGRES_PORT=5433 o MONGO_PORT=27018
```

### Error: "health check failed"

**Causa**: Contenedor no inició correctamente

**Solución**:

```bash
# Ver logs detallados
docker-compose logs postgres
docker-compose logs mongodb

# Reiniciar contenedores
make docker-restart

# Si persiste, limpiar y reiniciar
make docker-clean
make docker-up
```

### Error: "authentication failed" (PostgreSQL)

**Causa**: Contraseña incorrecta o usuario no creado

**Solución**:

```bash
# Verificar variables de entorno
cat .env | grep POSTGRES

# Reiniciar contenedor con variables correctas
docker-compose down
docker-compose up -d

# Verificar logs de inicialización
docker-compose logs postgres | grep "database system is ready"
```

### Error: "user not found" (MongoDB)

**Causa**: Usuario no creado o script de setup no ejecutado

**Solución**:

```bash
# Verificar si el script de setup se ejecutó
docker-compose logs mongodb | grep "sentiment_admin creado"

# Si no se ejecutó, recrear contenedor
docker-compose down -v
docker-compose up -d

# Crear usuario manualmente si es necesario
docker exec -it sentiment_mongo mongosh -u admin -p admin_password_2024 --authenticationDatabase admin

# En mongosh:
use sentiment_uam_nlp
db.createUser({
  user: "sentiment_admin",
  pwd: "dev_password_2024",
  roles: [
    { role: "readWrite", db: "sentiment_uam_nlp" },
    { role: "dbAdmin", db: "sentiment_uam_nlp" }
  ]
})
exit
```

### Contenedores se detienen inmediatamente

**Causa**: Error en scripts de inicialización o variables de entorno

**Solución**:

```bash
# Ver logs completos
docker-compose logs

# Ejecutar en modo interactivo para ver errores
docker-compose up

# Verificar sintaxis de scripts
cat scripts/init_postgres.sql | head -20
cat scripts/init_mongo.js | head -20
```

### Problemas de rendimiento

**Causa**: Recursos limitados de Docker

**Solución**:

```bash
# Aumentar recursos en Docker Desktop (macOS/Windows)
# Settings > Resources > Memory: 4GB+, CPUs: 2+

# Verificar uso de recursos
docker stats

# Limpiar imágenes no usadas
docker system prune -a
```

---

## 📊 Comparativa: Docker vs Manual

| Aspecto | Docker | Instalación Manual |
|---------|--------|-------------------|
| **Tiempo de setup** | 2-3 minutos | 30-45 minutos |
| **Compatibilidad OS** | Universal (1 comando) | 3 guías separadas |
| **Reproducibilidad** | 100% idéntico | Variable según sistema |
| **Aislamiento** | Total (contenedor) | Global (sistema) |
| **Reset de datos** | `docker-compose down -v` | Drop database manualmente |
| **Recursos** | Solo cuando se usa | Permanente en sistema |
| **Curva de aprendizaje** | Media (requiere Docker) | Baja |
| **Ideal para** | Desarrollo, testing | Producción, servidores |
| **Rendimiento** | ~95% (penalización 5-10%) | 100% nativo |

---

## 🎯 Recomendaciones

### Para Desarrollo

✅ **Usar Docker** - Simplifica setup y garantiza consistencia

### Para Testing

✅ **Usar Docker** - Fácil limpiar datos entre tests

### Para Producción

⚠️ **Usar servicios gestionados**:
- AWS RDS (PostgreSQL)
- MongoDB Atlas (MongoDB)
- O instalación manual optimizada

### Para Aprender

✅ **Probar ambos** - Docker para entender contenedores, manual para entender bases de datos

---

## 📚 Recursos Adicionales

- [Docker Docs](https://docs.docker.com/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [MongoDB Docker Hub](https://hub.docker.com/_/mongo)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [Guía de instalación manual](./DATABASE_SETUP.md)

---

**Última actualización:** 2025-11-26  
**Versión del proyecto:** 1.2.1  
**Mantenedores:** Equipo SentimentInsightUAM - UAM Azcapotzalco
