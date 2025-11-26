# Guía de Configuración de Bases de Datos

**SentimentInsightUAM v1.2.1**

Esta guía detalla cómo configurar PostgreSQL y MongoDB para el sistema de persistencia de SentimentInsightUAM.

---

## 🐳 Configuración Rápida con Docker (Recomendado)

Si prefieres usar Docker, puedes **omitir toda esta guía de configuración manual** y seguir estos pasos:

### Instalación con Docker

1. **Requisitos**:
   - Docker >= 20.10
   - Docker Compose >= 2.0

2. **Configurar e iniciar servicios**:
   ```bash
   # Copiar variables de entorno
   cp .env.docker .env

   # Iniciar contenedores (opción fácil)
   make docker-up

   # O manualmente con Docker Compose
   docker-compose up -d
   ```

3. **Verificar**:
   ```bash
   # PostgreSQL
   make db-psql
   # o: docker exec sentiment_postgres psql -U sentiment_admin -d sentiment_uam_db -c "\dt"

   # MongoDB
   make db-mongo
   # o: docker exec sentiment_mongo mongosh -u sentiment_admin -p dev_password_2024 \
   #      --authenticationDatabase sentiment_uam_nlp sentiment_uam_nlp --eval "db.getCollectionNames()"
   ```

**Ventajas de Docker**:
- ✅ Setup en 2 minutos vs 30-45 minutos manual
- ✅ Mismo entorno en todos los sistemas operativos
- ✅ Scripts de inicialización ejecutados automáticamente
- ✅ Fácil reset de datos (`make db-reset`)
- ✅ Aislamiento total del sistema host
- ✅ No requiere instalación de PostgreSQL/MongoDB en tu sistema

**Documentación completa de Docker**: Ver [DOCKER_SETUP.md](./DOCKER_SETUP.md)

---

## 📘 Guía de Instalación Manual

**Continúa con esta guía si prefieres instalación nativa o necesitas configuración para producción.**

---

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Instalación de PostgreSQL](#instalación-de-postgresql)
3. [Instalación de MongoDB](#instalación-de-mongodb)
4. [Configuración de PostgreSQL](#configuración-de-postgresql)
5. [Configuración de MongoDB](#configuración-de-mongodb)
6. [Creación de Usuario y Permisos](#creación-de-usuario-y-permisos)
7. [Ejecución de Scripts de Inicialización](#ejecución-de-scripts-de-inicialización)
8. [Verificación](#verificación)
9. [Variables de Entorno](#variables-de-entorno)
10. [Troubleshooting](#troubleshooting)

---

## 🔧 Requisitos Previos

### Software Necesario

- **PostgreSQL** >= 15.0
- **MongoDB** >= 7.0
- **Python** >= 3.11
- **psql** (cliente PostgreSQL)
- **mongosh** (MongoDB Shell)

### Verificar Instalaciones

```bash
# PostgreSQL
psql --version
# Salida esperada: psql (PostgreSQL) 15.x

# MongoDB
mongosh --version
# Salida esperada: 2.x.x

# Python
python3 --version
# Salida esperada: Python 3.11.x o superior
```

---

## 🐘 Instalación de PostgreSQL

### Ubuntu/Debian

```bash
# Actualizar paquetes
sudo apt update

# Instalar PostgreSQL
sudo apt install postgresql postgresql-contrib

# Iniciar servicio
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verificar estado
sudo systemctl status postgresql
```

### macOS (Homebrew)

```bash
# Instalar PostgreSQL
brew install postgresql@15

# Iniciar servicio
brew services start postgresql@15

# Verificar
psql postgres -c "SELECT version();"
```

### Fedora/RHEL/CentOS

```bash
# Instalar PostgreSQL
sudo dnf install postgresql-server postgresql-contrib

# Inicializar base de datos
sudo postgresql-setup --initdb

# Iniciar servicio
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

---

## 🍃 Instalación de MongoDB

### Ubuntu/Debian

```bash
# Importar clave pública GPG
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
   --dearmor

# Crear archivo de lista de fuentes
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
   sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Actualizar paquetes
sudo apt update

# Instalar MongoDB
sudo apt install -y mongodb-org

# Iniciar servicio
sudo systemctl start mongod
sudo systemctl enable mongod

# Verificar
sudo systemctl status mongod
```

### macOS (Homebrew)

```bash
# Agregar tap de MongoDB
brew tap mongodb/brew

# Instalar MongoDB Community Edition
brew install mongodb-community@7.0

# Iniciar servicio
brew services start mongodb-community@7.0

# Verificar
mongosh --eval "db.adminCommand('ping')"
```

### Fedora/RHEL/CentOS

```bash
# Crear archivo de repositorio
sudo cat <<EOF > /etc/yum.repos.d/mongodb-org-7.0.repo
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-7.0.asc
EOF

# Instalar MongoDB
sudo dnf install -y mongodb-org

# Iniciar servicio
sudo systemctl start mongod
sudo systemctl enable mongod
```

---

## ⚙️ Configuración de PostgreSQL

### 1. Acceder como Usuario Postgres

```bash
sudo -u postgres psql
```

### 2. Crear Usuario de Administración

```sql
-- Crear usuario con contraseña
CREATE USER sentiment_admin WITH PASSWORD 'tu_contraseña_segura';

-- Otorgar privilegios de creación de BD
ALTER USER sentiment_admin CREATEDB;

-- Salir
\q
```

### 3. Configurar Autenticación

Editar archivo de configuración `pg_hba.conf`:

```bash
# Ubicación típica (Ubuntu/Debian)
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Ubicación típica (Fedora/RHEL)
sudo nano /var/lib/pgsql/data/pg_hba.conf
```

Agregar/modificar la siguiente línea:

```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             sentiment_admin                         md5
host    all             sentiment_admin 127.0.0.1/32            md5
host    all             sentiment_admin ::1/128                 md5
```

### 4. Reiniciar PostgreSQL

```bash
# Ubuntu/Debian
sudo systemctl restart postgresql

# Fedora/RHEL
sudo systemctl restart postgresql
```

---

## ⚙️ Configuración de MongoDB

### 1. Habilitar Autenticación

Editar archivo de configuración:

```bash
sudo nano /etc/mongod.conf
```

Agregar/descomentar las siguientes líneas:

```yaml
security:
  authorization: enabled
```

### 2. Crear Usuario Administrador

```bash
# Conectar sin autenticación (primera vez)
mongosh

# En el shell de MongoDB:
use admin

db.createUser({
  user: "admin",
  pwd: "tu_contraseña_admin_segura",
  roles: [ { role: "userAdminAnyDatabase", db: "admin" }, "readWriteAnyDatabase" ]
})

exit
```

### 3. Crear Usuario para SentimentInsightUAM

```bash
# Conectar con usuario admin
mongosh -u admin -p --authenticationDatabase admin

# Crear usuario de aplicación
use sentiment_uam_nlp

db.createUser({
  user: "sentiment_admin",
  pwd: "tu_contraseña_segura",
  roles: [
    { role: "readWrite", db: "sentiment_uam_nlp" },
    { role: "dbAdmin", db: "sentiment_uam_nlp" }
  ]
})

exit
```

### 4. Reiniciar MongoDB

```bash
sudo systemctl restart mongod
```

---

## 🔐 Creación de Usuario y Permisos

### PostgreSQL: Permisos Detallados

```bash
# Conectar como sentiment_admin
psql -U sentiment_admin -d postgres

# Crear la base de datos
CREATE DATABASE sentiment_uam_db OWNER sentiment_admin;

# Conectar a la nueva BD
\c sentiment_uam_db

# Otorgar permisos completos
GRANT ALL PRIVILEGES ON DATABASE sentiment_uam_db TO sentiment_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sentiment_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sentiment_admin;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO sentiment_admin;

# Configurar permisos predeterminados para objetos futuros
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO sentiment_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO sentiment_admin;

\q
```

### MongoDB: Verificar Permisos

```bash
mongosh -u sentiment_admin -p --authenticationDatabase sentiment_uam_nlp

use sentiment_uam_nlp

# Verificar permisos
db.runCommand({ usersInfo: "sentiment_admin", showPrivileges: true })

exit
```

---

## 🚀 Ejecución de Scripts de Inicialización

### PostgreSQL

```bash
# Navegar al directorio del proyecto
cd /home/mr_ciem/dev/python-dev/SentimentInsightUAM

# Ejecutar script de inicialización
psql -U sentiment_admin -d postgres -f scripts/init_postgres.sql

# Verificar creación de tablas
psql -U sentiment_admin -d sentiment_uam_db -c "\dt"
```

**Salida esperada**:
```
                 List of relations
 Schema |         Name          | Type  |      Owner
--------+-----------------------+-------+-----------------
 public | cursos                | table | sentiment_admin
 public | etiquetas             | table | sentiment_admin
 public | historial_scraping    | table | sentiment_admin
 public | perfil_etiquetas      | table | sentiment_admin
 public | perfiles              | table | sentiment_admin
 public | profesores            | table | sentiment_admin
 public | resenia_etiquetas     | table | sentiment_admin
 public | resenias_metadata     | table | sentiment_admin
(8 rows)
```

### MongoDB

```bash
# Ejecutar script de inicialización
mongosh -u sentiment_admin -p --authenticationDatabase sentiment_uam_nlp sentiment_uam_nlp scripts/init_mongo.js

# Verificar colecciones
mongosh -u sentiment_admin -p --authenticationDatabase sentiment_uam_nlp sentiment_uam_nlp --eval "db.getCollectionNames()"
```

**Salida esperada**:
```
[ 'opiniones', 'sentimiento_cache', 'system.js' ]
```

---

## ✅ Verificación

### Verificar PostgreSQL

```bash
# Conectar a la base de datos
psql -U sentiment_admin -d sentiment_uam_db

# Listar tablas
\dt

# Listar vistas
\dv

# Listar vistas materializadas
\dm

# Listar funciones
\df

# Verificar extensiones
\dx

# Contar etiquetas iniciales (debe ser 21)
SELECT COUNT(*) FROM etiquetas;

# Verificar estructura de una tabla
\d profesores

# Salir
\q
```

### Verificar MongoDB

```bash
# Conectar
mongosh -u sentiment_admin -p --authenticationDatabase sentiment_uam_nlp

use sentiment_uam_nlp

# Listar colecciones
show collections

# Verificar índices de opiniones
db.opiniones.getIndexes()

# Verificar validación de esquema
db.getCollectionInfos({ name: "opiniones" })[0].options.validator

# Probar inserción de documento de prueba
db.opiniones.insertOne({
    profesor_id: 1,
    profesor_nombre: "Test Profesor",
    profesor_slug: "test-profesor",
    fecha_opinion: new Date(),
    comentario: "Test de validación",
    idioma: "es",
    sentimiento: { analizado: false },
    fecha_extraccion: new Date(),
    fuente: "test",
    version_scraper: "1.1.0"
})

# Verificar documento
db.opiniones.findOne({ profesor_id: 1 })

# Eliminar documento de prueba
db.opiniones.deleteOne({ profesor_id: 1 })

exit
```

---

## 🔑 Variables de Entorno

### Crear archivo `.env`

```bash
# En el directorio raíz del proyecto
cd /home/mr_ciem/dev/python-dev/SentimentInsightUAM

# Crear archivo .env
nano .env
```

### Contenido del archivo `.env`

```env
# ============================================================================
# Configuración de Bases de Datos - SentimentInsightUAM
# ============================================================================

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sentiment_uam_db
POSTGRES_USER=sentiment_admin
POSTGRES_PASSWORD=tu_contraseña_segura

# MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB=sentiment_uam_nlp
MONGO_USER=sentiment_admin
MONGO_PASSWORD=tu_contraseña_segura

# URLs de Conexión (construidas automáticamente)
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
MONGO_URL=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@${MONGO_HOST}:${MONGO_PORT}/${MONGO_DB}?authSource=${MONGO_DB}

# Configuración del Scraper
HEADLESS=true
USER_AGENT=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36

# Configuración de Logging
LOG_LEVEL=INFO
LOG_FILE=logs/sentimentuam.log
```

### Proteger archivo `.env`

```bash
# Establecer permisos restrictivos
chmod 600 .env

# Verificar que .env esté en .gitignore
echo ".env" >> .gitignore
```

---

## 🔍 Troubleshooting

### Error: "psql: FATAL: Peer authentication failed"

**Solución**:
```bash
# Editar pg_hba.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Cambiar de 'peer' a 'md5' en líneas locales
# Antes:
# local   all             all                                     peer

# Después:
# local   all             all                                     md5

# Reiniciar
sudo systemctl restart postgresql
```

### Error: "MongoDB connection refused"

**Solución**:
```bash
# Verificar que el servicio esté activo
sudo systemctl status mongod

# Iniciar si está detenido
sudo systemctl start mongod

# Verificar puerto
sudo netstat -tuln | grep 27017

# Revisar logs
sudo tail -f /var/log/mongodb/mongod.log
```

### Error: "Authentication failed" en MongoDB

**Solución**:
```bash
# Verificar que la autenticación esté habilitada
grep "authorization" /etc/mongod.conf

# Si no está habilitada, agregarla:
sudo nano /etc/mongod.conf

# Agregar:
security:
  authorization: enabled

# Reiniciar
sudo systemctl restart mongod

# Recrear usuario si es necesario
mongosh
use admin
db.auth("admin", "password_admin")
use sentiment_uam_nlp
db.dropUser("sentiment_admin")
db.createUser({
  user: "sentiment_admin",
  pwd: "nueva_contraseña",
  roles: [ { role: "readWrite", db: "sentiment_uam_nlp" } ]
})
```

### Error: "relation does not exist" en PostgreSQL

**Solución**:
```bash
# Verificar que estás en la base de datos correcta
psql -U sentiment_admin -d sentiment_uam_db -c "\c"

# Listar tablas
psql -U sentiment_admin -d sentiment_uam_db -c "\dt"

# Si no hay tablas, ejecutar script de inicialización
psql -U sentiment_admin -d sentiment_uam_db -f scripts/init_postgres.sql
```

### Error: "Could not connect to server" (PostgreSQL)

**Solución**:
```bash
# Verificar servicio
sudo systemctl status postgresql

# Verificar puerto
sudo netstat -tuln | grep 5432

# Revisar logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Iniciar servicio si está detenido
sudo systemctl start postgresql
```

---

## 📊 Consultas de Validación

### PostgreSQL: Validar Estructura

```sql
-- Conectar
psql -U sentiment_admin -d sentiment_uam_db

-- 1. Contar tablas (debe ser 8)
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

-- 2. Verificar índices (debe ser > 20)
SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';

-- 3. Verificar funciones (debe ser >= 4)
SELECT COUNT(*) FROM pg_proc WHERE pronamespace = 'public'::regnamespace;

-- 4. Verificar etiquetas seed (debe ser 21)
SELECT COUNT(*) FROM etiquetas;

-- 5. Listar etiquetas por categoría
SELECT categoria, COUNT(*) 
FROM etiquetas 
GROUP BY categoria 
ORDER BY COUNT(*) DESC;

-- 6. Verificar constraints
SELECT 
    conname AS constraint_name,
    conrelid::regclass AS table_name
FROM pg_constraint
WHERE contype = 'c'  -- CHECK constraints
ORDER BY conrelid::regclass::text;
```

### MongoDB: Validar Estructura

```javascript
// Conectar
mongosh -u sentiment_admin -p --authenticationDatabase sentiment_uam_nlp

use sentiment_uam_nlp

// 1. Verificar colecciones
db.getCollectionNames()

// 2. Contar índices en opiniones (debe ser >= 8)
db.opiniones.getIndexes().length

// 3. Verificar validación de esquema
db.getCollectionInfos({ name: "opiniones" })[0].options.validator

// 4. Listar índices con detalles
db.opiniones.getIndexes()

// 5. Estadísticas de la base de datos
db.stats()

// 6. Verificar funciones auxiliares
db.system.js.find()
```

---

## 🎯 Próximos Pasos

Una vez configuradas las bases de datos:

1. **Instalar dependencias Python**:
   ```bash
   pip install sqlalchemy[asyncio] asyncpg motor pymongo
   ```

2. **Crear módulos de persistencia**:
   - `src/db/postgres.py` - Conexión y modelos SQLAlchemy
   - `src/db/mongodb.py` - Conexión Motor (async)
   - `src/db/sync.py` - Lógica de sincronización

3. **Integrar con scraper**:
   - Modificar `src/mp/scrape_prof.py`
   - Agregar llamada a función de persistencia

4. **Ejecutar pruebas**:
   - Scrapear 3-5 profesores
   - Verificar inserción en ambas BD
   - Validar vínculos entre PostgreSQL y MongoDB

---

## 📚 Recursos Adicionales

- [Documentación PostgreSQL 15](https://www.postgresql.org/docs/15/)
- [Documentación MongoDB 7.0](https://www.mongodb.com/docs/v7.0/)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/en/20/)
- [Motor (Async MongoDB)](https://motor.readthedocs.io/)
- [AsyncPG](https://magicstack.github.io/asyncpg/)

---

**Versión**: 1.2.1  
**Última actualización**: 2025-11-26  
**Mantenedores**: Equipo SentimentInsightUAM
