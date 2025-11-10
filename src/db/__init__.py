"""
Módulo de persistencia de datos para SentimentInsightUAM

Proporciona conexiones y utilidades para PostgreSQL y MongoDB.
"""
import os
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Base declarativa para modelos SQLAlchemy
Base = declarative_base()

# ============================================================================
# CONFIGURACIÓN DE POSTGRESQL
# ============================================================================

# URL de conexión PostgreSQL (asyncpg)
POSTGRES_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+asyncpg://{os.getenv('POSTGRES_USER', 'sentiment_admin')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'dev_password_2024')}@"
    f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB', 'sentiment_uam_db')}"
)

# Engine asíncrono de SQLAlchemy
pg_engine = create_async_engine(
    POSTGRES_URL,
    echo=False,  # Cambiar a True para debug SQL
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True  # Verifica conexiones antes de usarlas
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    pg_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager para obtener sesión de base de datos PostgreSQL.
    
    Uso:
        async with get_db_session() as session:
            result = await session.execute(query)
            await session.commit()
    
    Yields:
        AsyncSession: Sesión de SQLAlchemy
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================================================
# CONFIGURACIÓN DE MONGODB
# ============================================================================

# URL de conexión MongoDB
MONGO_URL = os.getenv(
    "MONGO_URL",
    f"mongodb://{os.getenv('MONGO_USER', 'sentiment_admin')}:"
    f"{os.getenv('MONGO_PASSWORD', 'dev_password_2024')}@"
    f"{os.getenv('MONGO_HOST', 'localhost')}:"
    f"{os.getenv('MONGO_PORT', '27017')}/"
    f"{os.getenv('MONGO_DB', 'sentiment_uam_nlp')}?"
    f"authSource={os.getenv('MONGO_DB', 'sentiment_uam_nlp')}"
)

# Cliente MongoDB (singleton)
_mongo_client = None


def get_mongo_client() -> AsyncIOMotorClient:
    """
    Obtiene cliente MongoDB (singleton).
    
    Returns:
        AsyncIOMotorClient: Cliente de MongoDB
    """
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(
            MONGO_URL,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000
        )
    return _mongo_client


def get_mongo_db():
    """
    Obtiene instancia de base de datos MongoDB.
    
    Returns:
        Database: Base de datos sentiment_uam_nlp
    """
    client = get_mongo_client()
    return client[os.getenv('MONGO_DB', 'sentiment_uam_nlp')]


async def close_mongo_connection():
    """Cierra conexión de MongoDB."""
    global _mongo_client
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None


# ============================================================================
# UTILIDADES
# ============================================================================

async def init_db():
    """
    Inicializa conexiones a bases de datos.
    Verifica que las tablas existan.
    """
    # Verificar PostgreSQL
    async with pg_engine.begin() as conn:
        # Importar modelos para registrarlos
        from . import models  # noqa
        # No crear tablas aquí, ya existen por init_postgres.sql
        pass
    
    # Verificar MongoDB
    mongo_db = get_mongo_db()
    await mongo_db.command('ping')
    
    print("✓ Conexiones a bases de datos inicializadas")


async def close_db():
    """Cierra todas las conexiones de bases de datos."""
    await pg_engine.dispose()
    await close_mongo_connection()
    print("✓ Conexiones cerradas")


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'Base',
    'pg_engine',
    'AsyncSessionLocal',
    'get_db_session',
    'get_mongo_client',
    'get_mongo_db',
    'init_db',
    'close_db',
]
