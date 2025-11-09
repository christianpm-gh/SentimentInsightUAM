# ============================================================================
# Makefile para SentimentInsightUAM
# ============================================================================
# Comandos útiles para gestión de contenedores Docker y bases de datos
#
# Uso:
#   make help           - Mostrar ayuda
#   make docker-up      - Iniciar contenedores
#   make docker-down    - Detener contenedores
#   make db-status      - Verificar estado de bases de datos
# ============================================================================

.PHONY: help docker-up docker-down docker-restart docker-logs docker-clean \
        db-setup db-status db-psql db-mongo db-reset install test

# Colores para output
RESET=\033[0m
BOLD=\033[1m
GREEN=\033[32m
YELLOW=\033[33m
RED=\033[31m
BLUE=\033[34m

# Cargar variables de entorno desde .env si existe
ifneq (,$(wildcard .env))
    include .env
    export
endif

# ============================================================================
# Ayuda
# ============================================================================

help:
	@echo "$(BOLD)$(BLUE)SentimentInsightUAM - Comandos Disponibles$(RESET)"
	@echo ""
	@echo "$(BOLD)Docker:$(RESET)"
	@echo "  $(GREEN)make docker-up$(RESET)       - Iniciar contenedores (PostgreSQL + MongoDB)"
	@echo "  $(GREEN)make docker-down$(RESET)     - Detener contenedores"
	@echo "  $(GREEN)make docker-restart$(RESET)  - Reiniciar contenedores"
	@echo "  $(GREEN)make docker-logs$(RESET)     - Ver logs de contenedores"
	@echo "  $(GREEN)make docker-clean$(RESET)    - Eliminar contenedores y volúmenes $(RED)(DESTRUYE DATOS)$(RESET)"
	@echo ""
	@echo "$(BOLD)Bases de Datos:$(RESET)"
	@echo "  $(GREEN)make db-setup$(RESET)        - Configurar bases de datos"
	@echo "  $(GREEN)make db-status$(RESET)       - Verificar estado de bases de datos"
	@echo "  $(GREEN)make db-psql$(RESET)         - Conectar a PostgreSQL (shell interactivo)"
	@echo "  $(GREEN)make db-mongo$(RESET)        - Conectar a MongoDB (mongosh)"
	@echo "  $(GREEN)make db-reset$(RESET)        - Reiniciar bases de datos $(RED)(DESTRUYE DATOS)$(RESET)"
	@echo ""
	@echo "$(BOLD)Desarrollo:$(RESET)"
	@echo "  $(GREEN)make install$(RESET)         - Instalar dependencias Python"
	@echo "  $(GREEN)make test$(RESET)            - Ejecutar tests (cuando estén disponibles)"
	@echo ""

# ============================================================================
# Comandos Docker
# ============================================================================

docker-up:
	@echo "$(BOLD)$(BLUE)🚀 Iniciando contenedores...$(RESET)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)⚠️  Archivo .env no encontrado$(RESET)"; \
		echo "$(YELLOW)📋 Copiando .env.docker a .env...$(RESET)"; \
		cp .env.docker .env; \
		echo "$(GREEN)✅ Archivo .env creado$(RESET)"; \
		echo "$(YELLOW)⚠️  Recuerda cambiar las contraseñas para producción$(RESET)"; \
	fi
	@docker-compose up -d
	@echo "$(YELLOW)⏳ Esperando inicialización de bases de datos...$(RESET)"
	@sleep 12
	@$(MAKE) db-status

docker-down:
	@echo "$(BOLD)$(BLUE)🛑 Deteniendo contenedores...$(RESET)"
	@docker-compose down
	@echo "$(GREEN)✅ Contenedores detenidos$(RESET)"

docker-restart:
	@echo "$(BOLD)$(BLUE)🔄 Reiniciando contenedores...$(RESET)"
	@$(MAKE) docker-down
	@$(MAKE) docker-up

docker-logs:
	@echo "$(BOLD)$(BLUE)📋 Mostrando logs de contenedores...$(RESET)"
	@echo "$(YELLOW)Presiona Ctrl+C para salir$(RESET)"
	@docker-compose logs -f

docker-clean:
	@echo "$(BOLD)$(RED)⚠️  ADVERTENCIA: Esto eliminará todos los datos de las bases de datos!$(RESET)"
	@read -p "¿Estás seguro? Escribe 'SI' para confirmar: " confirm; \
	if [ "$$confirm" = "SI" ]; then \
		echo "$(BLUE)🗑️  Eliminando contenedores y volúmenes...$(RESET)"; \
		docker-compose down -v; \
		echo "$(GREEN)✅ Contenedores y volúmenes eliminados$(RESET)"; \
	else \
		echo "$(YELLOW)❌ Operación cancelada$(RESET)"; \
	fi

# ============================================================================
# Comandos de Bases de Datos
# ============================================================================

db-setup:
	@echo "$(BOLD)$(BLUE)📊 Configurando bases de datos...$(RESET)"
	@echo "$(GREEN)✅ PostgreSQL configurado automáticamente por init_postgres.sql$(RESET)"
	@echo "$(GREEN)✅ MongoDB configurado automáticamente por init_mongo.js$(RESET)"
	@$(MAKE) db-status

db-status:
	@echo ""
	@echo "$(BOLD)$(BLUE)📊 Estado de PostgreSQL:$(RESET)"
	@docker exec sentiment_postgres psql -U sentiment_admin -d sentiment_uam_db -c "\dt" 2>/dev/null && \
		echo "$(GREEN)✅ PostgreSQL operativo$(RESET)" || \
		echo "$(RED)❌ PostgreSQL no disponible$(RESET)"
	@echo ""
	@echo "$(BOLD)$(BLUE)📊 Estado de MongoDB:$(RESET)"
	@docker exec sentiment_mongo mongosh -u sentiment_admin -p $${MONGO_PASSWORD:-dev_password_2024} \
		--authenticationDatabase sentiment_uam_nlp \
		--eval "db.getCollectionNames()" sentiment_uam_nlp 2>/dev/null && \
		echo "$(GREEN)✅ MongoDB operativo$(RESET)" || \
		echo "$(RED)❌ MongoDB no disponible$(RESET)"
	@echo ""

db-psql:
	@echo "$(BOLD)$(BLUE)🐘 Conectando a PostgreSQL...$(RESET)"
	@echo "$(YELLOW)Usa \q para salir$(RESET)"
	@docker exec -it sentiment_postgres psql -U sentiment_admin -d sentiment_uam_db

db-mongo:
	@echo "$(BOLD)$(BLUE)🍃 Conectando a MongoDB...$(RESET)"
	@echo "$(YELLOW)Usa exit para salir$(RESET)"
	@docker exec -it sentiment_mongo mongosh -u sentiment_admin -p $${MONGO_PASSWORD:-dev_password_2024} \
		--authenticationDatabase sentiment_uam_nlp sentiment_uam_nlp

db-reset:
	@echo "$(BOLD)$(RED)⚠️  ADVERTENCIA: Esto eliminará TODOS los datos de las bases de datos!$(RESET)"
	@read -p "¿Estás seguro? Escribe 'RESET' para confirmar: " confirm; \
	if [ "$$confirm" = "RESET" ]; then \
		echo "$(BLUE)🔄 Reiniciando bases de datos...$(RESET)"; \
		$(MAKE) docker-clean; \
		$(MAKE) docker-up; \
		echo "$(GREEN)✅ Bases de datos reiniciadas$(RESET)"; \
	else \
		echo "$(YELLOW)❌ Operación cancelada$(RESET)"; \
	fi

# ============================================================================
# Comandos de Desarrollo
# ============================================================================

install:
	@echo "$(BOLD)$(BLUE)📦 Instalando dependencias Python...$(RESET)"
	@pip install -r requirements.txt
	@echo "$(BLUE)🎭 Instalando Playwright...$(RESET)"
	@python -m playwright install chromium
	@echo "$(GREEN)✅ Dependencias instaladas correctamente$(RESET)"

test:
	@echo "$(BOLD)$(BLUE)🧪 Ejecutando tests...$(RESET)"
	@echo "$(YELLOW)⚠️  Tests no implementados aún$(RESET)"
	@echo "$(YELLOW)TODO: Implementar tests en versión futura$(RESET)"

# ============================================================================
# Default
# ============================================================================

.DEFAULT_GOAL := help
