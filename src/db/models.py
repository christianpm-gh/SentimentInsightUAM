"""
Modelos SQLAlchemy para PostgreSQL - SentimentInsightUAM

Define la estructura ORM de las tablas de la base de datos.
"""
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Integer, String, Boolean, DECIMAL, Date, DateTime, Text,
    ForeignKey, UniqueConstraint, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from . import Base


# ============================================================================
# MODELO: Profesor
# ============================================================================

class Profesor(Base):
    """Catálogo maestro de profesores de la UAM Azcapotzalco."""
    
    __tablename__ = 'profesores'
    
    # Campos
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_completo: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_limpio: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    url_directorio_uam: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url_misprofesores: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    departamento: Mapped[str] = mapped_column(String(100), default='Sistemas')
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )
    
    # Relaciones
    perfiles: Mapped[list["Perfil"]] = relationship(
        "Perfil", 
        back_populates="profesor",
        cascade="all, delete-orphan"
    )
    resenias: Mapped[list["ReseniaMetadata"]] = relationship(
        "ReseniaMetadata",
        back_populates="profesor",
        cascade="all, delete-orphan"
    )
    historial: Mapped[list["HistorialScraping"]] = relationship(
        "HistorialScraping",
        back_populates="profesor"
    )
    
    def __repr__(self):
        return f"<Profesor(id={self.id}, nombre='{self.nombre_limpio}')>"


# ============================================================================
# MODELO: Perfil
# ============================================================================

class Perfil(Base):
    """Snapshot temporal de métricas de cada profesor."""
    
    __tablename__ = 'perfiles'
    
    # Campos
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profesor_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('profesores.id', ondelete='CASCADE'),
        nullable=False
    )
    calidad_general: Mapped[Optional[float]] = mapped_column(DECIMAL(4, 2), nullable=True)
    dificultad: Mapped[Optional[float]] = mapped_column(DECIMAL(4, 2), nullable=True)
    porcentaje_recomendacion: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2), nullable=True)
    total_resenias_encontradas: Mapped[int] = mapped_column(Integer, default=0)
    scraping_exitoso: Mapped[bool] = mapped_column(Boolean, default=True)
    fuente: Mapped[str] = mapped_column(String(50), default='misprofesores.com')
    fecha_extraccion: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    
    # Relaciones
    profesor: Mapped["Profesor"] = relationship("Profesor", back_populates="perfiles")
    etiquetas_perfil: Mapped[list["PerfilEtiqueta"]] = relationship(
        "PerfilEtiqueta",
        back_populates="perfil",
        cascade="all, delete-orphan"
    )
    resenias: Mapped[list["ReseniaMetadata"]] = relationship(
        "ReseniaMetadata",
        back_populates="perfil"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint('calidad_general >= 0 AND calidad_general <= 10', name='check_calidad_general'),
        CheckConstraint('dificultad >= 0 AND dificultad <= 10', name='check_dificultad'),
        CheckConstraint('porcentaje_recomendacion >= 0 AND porcentaje_recomendacion <= 100', name='check_recomendacion'),
    )
    
    def __repr__(self):
        return f"<Perfil(id={self.id}, profesor_id={self.profesor_id}, calidad={self.calidad_general})>"


# ============================================================================
# MODELO: Etiqueta
# ============================================================================

class Etiqueta(Base):
    """Catálogo unificado de etiquetas (tags) del sistema."""
    
    __tablename__ = 'etiquetas'
    
    # Campos
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    etiqueta: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    etiqueta_normalizada: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    categoria: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    uso_total: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    
    # Relaciones
    perfiles: Mapped[list["PerfilEtiqueta"]] = relationship(
        "PerfilEtiqueta",
        back_populates="etiqueta"
    )
    resenias: Mapped[list["ReseniaEtiqueta"]] = relationship(
        "ReseniaEtiqueta",
        back_populates="etiqueta"
    )
    
    def __repr__(self):
        return f"<Etiqueta(id={self.id}, etiqueta='{self.etiqueta}')>"


# ============================================================================
# MODELO: PerfilEtiqueta (Relación Many-to-Many)
# ============================================================================

class PerfilEtiqueta(Base):
    """Relación many-to-many entre perfiles y etiquetas con contadores."""
    
    __tablename__ = 'perfil_etiquetas'
    
    # Campos
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    perfil_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('perfiles.id', ondelete='CASCADE'),
        nullable=False
    )
    etiqueta_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('etiquetas.id', ondelete='CASCADE'),
        nullable=False
    )
    contador: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relaciones
    perfil: Mapped["Perfil"] = relationship("Perfil", back_populates="etiquetas_perfil")
    etiqueta: Mapped["Etiqueta"] = relationship("Etiqueta", back_populates="perfiles")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('perfil_id', 'etiqueta_id', name='uq_perfil_etiqueta'),
    )
    
    def __repr__(self):
        return f"<PerfilEtiqueta(perfil_id={self.perfil_id}, etiqueta_id={self.etiqueta_id}, contador={self.contador})>"


# ============================================================================
# MODELO: Curso
# ============================================================================

class Curso(Base):
    """Catálogo de materias/cursos impartidos."""
    
    __tablename__ = 'cursos'
    
    # Campos
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_normalizado: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    codigo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    departamento: Mapped[str] = mapped_column(String(100), default='Sistemas')
    nivel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    total_resenias: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    
    # Relaciones
    resenias: Mapped[list["ReseniaMetadata"]] = relationship(
        "ReseniaMetadata",
        back_populates="curso"
    )
    
    def __repr__(self):
        return f"<Curso(id={self.id}, nombre='{self.nombre}')>"


# ============================================================================
# MODELO: ReseniaMetadata
# ============================================================================

class ReseniaMetadata(Base):
    """Datos estructurados de cada reseña (sin comentario textual)."""
    
    __tablename__ = 'resenias_metadata'
    
    # Campos
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profesor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('profesores.id', ondelete='CASCADE'),
        nullable=False
    )
    curso_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('cursos.id', ondelete='SET NULL'),
        nullable=True
    )
    perfil_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('perfiles.id', ondelete='SET NULL'),
        nullable=True
    )
    fecha_resenia: Mapped[date] = mapped_column(Date, nullable=False)
    calidad_general: Mapped[Optional[float]] = mapped_column(DECIMAL(4, 2), nullable=True)
    facilidad: Mapped[Optional[float]] = mapped_column(DECIMAL(4, 2), nullable=True)
    asistencia: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    calificacion_recibida: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    nivel_interes: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mongo_opinion_id: Mapped[Optional[str]] = mapped_column(String(24), unique=True, nullable=True)
    tiene_comentario: Mapped[bool] = mapped_column(Boolean, default=False)
    longitud_comentario: Mapped[int] = mapped_column(Integer, default=0)
    fecha_extraccion: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    fuente: Mapped[str] = mapped_column(String(50), default='misprofesores.com')
    
    # Relaciones
    profesor: Mapped["Profesor"] = relationship("Profesor", back_populates="resenias")
    curso: Mapped[Optional["Curso"]] = relationship("Curso", back_populates="resenias")
    perfil: Mapped[Optional["Perfil"]] = relationship("Perfil", back_populates="resenias")
    etiquetas_resenia: Mapped[list["ReseniaEtiqueta"]] = relationship(
        "ReseniaEtiqueta",
        back_populates="resenia",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint('calidad_general >= 0 AND calidad_general <= 10', name='check_resenia_calidad'),
        CheckConstraint('facilidad >= 0 AND facilidad <= 10', name='check_resenia_facilidad'),
    )
    
    def __repr__(self):
        return f"<ReseniaMetadata(id={self.id}, profesor_id={self.profesor_id}, calidad={self.calidad_general})>"


# ============================================================================
# MODELO: ReseniaEtiqueta (Relación Many-to-Many)
# ============================================================================

class ReseniaEtiqueta(Base):
    """Relación many-to-many entre reseñas y etiquetas."""
    
    __tablename__ = 'resenia_etiquetas'
    
    # Campos
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resenia_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('resenias_metadata.id', ondelete='CASCADE'),
        nullable=False
    )
    etiqueta_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('etiquetas.id', ondelete='CASCADE'),
        nullable=False
    )
    
    # Relaciones
    resenia: Mapped["ReseniaMetadata"] = relationship("ReseniaMetadata", back_populates="etiquetas_resenia")
    etiqueta: Mapped["Etiqueta"] = relationship("Etiqueta", back_populates="resenias")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('resenia_id', 'etiqueta_id', name='uq_resenia_etiqueta'),
    )
    
    def __repr__(self):
        return f"<ReseniaEtiqueta(resenia_id={self.resenia_id}, etiqueta_id={self.etiqueta_id})>"


# ============================================================================
# MODELO: HistorialScraping
# ============================================================================

class HistorialScraping(Base):
    """Auditoría completa de ejecuciones del scraper."""
    
    __tablename__ = 'historial_scraping'
    
    # Campos
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profesor_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('profesores.id', ondelete='SET NULL'),
        nullable=True
    )
    estado: Mapped[str] = mapped_column(String(50), nullable=False)
    resenias_encontradas: Mapped[int] = mapped_column(Integer, default=0)
    resenias_nuevas: Mapped[int] = mapped_column(Integer, default=0)
    resenias_actualizadas: Mapped[int] = mapped_column(Integer, default=0)
    mensaje_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duracion_segundos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    url_procesada: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cache_utilizado: Mapped[bool] = mapped_column(Boolean, default=False)
    razon_rescraping: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_origen: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    
    # Relaciones
    profesor: Mapped[Optional["Profesor"]] = relationship("Profesor", back_populates="historial")
    
    def __repr__(self):
        return f"<HistorialScraping(id={self.id}, profesor_id={self.profesor_id}, estado='{self.estado}')>"
