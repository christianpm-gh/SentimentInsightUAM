#!/bin/bash
# ============================================================================
# Script de Verificación - Implementación Docker v1.1.1
# ============================================================================
# Este script verifica que la implementación de Docker esté completa
# y funcionando correctamente.
#
# Uso: bash scripts/verify_docker_setup.sh
# ============================================================================

set -e

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "============================================================================"
echo -e "${BLUE}Verificación de Implementación Docker - SentimentInsightUAM v1.1.1${NC}"
echo "============================================================================"
echo ""

# Función para verificar archivo
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} Archivo encontrado: $1"
        return 0
    else
        echo -e "${RED}❌${NC} Archivo faltante: $1"
        return 1
    fi
}

# Función para verificar comando
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✅${NC} Comando disponible: $1"
        return 0
    else
        echo -e "${YELLOW}⚠️${NC}  Comando no encontrado: $1"
        return 1
    fi
}

# ============================================================================
# Paso 1: Verificar archivos creados
# ============================================================================

echo -e "${BLUE}Paso 1: Verificando archivos creados...${NC}"
echo ""

check_file "docker-compose.yml"
check_file ".env.docker"
check_file "Makefile"
check_file ".dockerignore"
check_file "scripts/init_mongo.js"
check_file "docs/DOCKER_SETUP.md"
check_file "docs/RESUMEN_V1.1.1.md"

echo ""

# ============================================================================
# Paso 2: Verificar archivos actualizados
# ============================================================================

echo -e "${BLUE}Paso 2: Verificando archivos actualizados...${NC}"
echo ""

check_file "README.md"
check_file "docs/DATABASE_SETUP.md"
check_file "CHANGELOG.md"
check_file ".gitignore"

echo ""

# ============================================================================
# Paso 3: Verificar permisos de script
# ============================================================================

echo -e "${BLUE}Paso 3: Verificando permisos de scripts...${NC}"
echo ""

if [ -f "scripts/init_mongo.js" ]; then
    echo -e "${GREEN}✅${NC} Script de inicialización Mongo encontrado: scripts/init_mongo.js"
else
    echo -e "${RED}❌${NC} Script de inicialización Mongo faltante: scripts/init_mongo.js"
fi

echo ""

# ============================================================================
# Paso 4: Verificar comandos necesarios
# ============================================================================

echo -e "${BLUE}Paso 4: Verificando comandos necesarios...${NC}"
echo ""

check_command "docker"
check_command "docker-compose"
check_command "make"

echo ""

# ============================================================================
# Paso 5: Verificar versiones
# ============================================================================

echo -e "${BLUE}Paso 5: Verificando versiones...${NC}"
echo ""

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d ' ' -f3 | cut -d ',' -f1)
    echo -e "${GREEN}✅${NC} Docker version: $DOCKER_VERSION"
else
    echo -e "${RED}❌${NC} Docker no instalado"
fi

if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | cut -d ' ' -f4 | cut -d ',' -f1)
    echo -e "${GREEN}✅${NC} Docker Compose version: $COMPOSE_VERSION"
else
    echo -e "${RED}❌${NC} Docker Compose no instalado"
fi

echo ""

# ============================================================================
# Paso 6: Verificar archivo .env
# ============================================================================

echo -e "${BLUE}Paso 6: Verificando configuración...${NC}"
echo ""

if [ -f ".env" ]; then
    echo -e "${GREEN}✅${NC} Archivo .env existe"
else
    echo -e "${YELLOW}⚠️${NC}  Archivo .env no encontrado"
    echo -e "   Ejecutar: cp .env.docker .env"
fi

echo ""

# ============================================================================
# Paso 7: Verificar Makefile targets
# ============================================================================

echo -e "${BLUE}Paso 7: Verificando targets de Makefile...${NC}"
echo ""

EXPECTED_TARGETS=("docker-up" "docker-down" "docker-restart" "docker-logs" "docker-clean" "db-status" "db-psql" "db-mongo" "db-reset" "install" "help")

for target in "${EXPECTED_TARGETS[@]}"; do
    if grep -q "^${target}:" Makefile; then
        echo -e "${GREEN}✅${NC} Target encontrado: make $target"
    else
        echo -e "${RED}❌${NC} Target faltante: make $target"
    fi
done

echo ""

# ============================================================================
# Paso 8: Verificar contenedores (si Docker está corriendo)
# ============================================================================

echo -e "${BLUE}Paso 8: Verificando estado de contenedores (opcional)...${NC}"
echo ""

if docker ps &> /dev/null; then
    POSTGRES_RUNNING=$(docker ps --filter "name=sentiment_postgres" --format "{{.Names}}" 2>/dev/null || echo "")
    MONGO_RUNNING=$(docker ps --filter "name=sentiment_mongo" --format "{{.Names}}" 2>/dev/null || echo "")
    
    if [ -n "$POSTGRES_RUNNING" ]; then
        echo -e "${GREEN}✅${NC} Contenedor PostgreSQL corriendo: $POSTGRES_RUNNING"
    else
        echo -e "${YELLOW}ℹ️${NC}  Contenedor PostgreSQL no corriendo (ejecutar: make docker-up)"
    fi
    
    if [ -n "$MONGO_RUNNING" ]; then
        echo -e "${GREEN}✅${NC} Contenedor MongoDB corriendo: $MONGO_RUNNING"
    else
        echo -e "${YELLOW}ℹ️${NC}  Contenedor MongoDB no corriendo (ejecutar: make docker-up)"
    fi
else
    echo -e "${YELLOW}ℹ️${NC}  Docker daemon no accesible (¿está iniciado?)"
fi

echo ""

# ============================================================================
# Paso 9: Verificar volúmenes (si Docker está corriendo)
# ============================================================================

echo -e "${BLUE}Paso 9: Verificando volúmenes de Docker (opcional)...${NC}"
echo ""

if docker volume ls &> /dev/null; then
    VOLUMES=$(docker volume ls --filter "name=sentiment_" --format "{{.Name}}" 2>/dev/null || echo "")
    
    if [ -n "$VOLUMES" ]; then
        echo -e "${GREEN}✅${NC} Volúmenes encontrados:"
        for vol in $VOLUMES; do
            echo -e "   - $vol"
        done
    else
        echo -e "${YELLOW}ℹ️${NC}  No hay volúmenes creados aún (ejecutar: make docker-up)"
    fi
else
    echo -e "${YELLOW}ℹ️${NC}  No se pueden verificar volúmenes (Docker no accesible)"
fi

echo ""

# ============================================================================
# Resumen
# ============================================================================

echo "============================================================================"
echo -e "${BLUE}Resumen de Verificación${NC}"
echo "============================================================================"
echo ""

if [ -f "docker-compose.yml" ] && [ -f ".env.docker" ] && [ -f "Makefile" ]; then
    echo -e "${GREEN}✅ Implementación completada correctamente${NC}"
    echo ""
    echo "Próximos pasos:"
    echo "1. Configurar entorno: cp .env.docker .env"
    echo "2. Iniciar servicios: make docker-up"
    echo "3. Verificar estado: make db-status"
    echo "4. Conectar a PostgreSQL: make db-psql"
    echo "5. Conectar a MongoDB: make db-mongo"
    echo ""
    echo "Documentación completa: docs/DOCKER_SETUP.md"
else
    echo -e "${RED}❌ Implementación incompleta${NC}"
    echo ""
    echo "Archivos faltantes. Revisar output anterior."
fi

echo "============================================================================"
