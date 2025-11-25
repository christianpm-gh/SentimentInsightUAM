import asyncio
import sys
from pathlib import Path
from sqlalchemy import select, func, desc

# Agregar root al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import get_db_session
from src.db.models import Curso, ReseniaMetadata

async def show_stats():
    print("\n📊 Estadísticas de Materias (PostgreSQL)")
    print("========================================")
    
    async with get_db_session() as session:
        # Contar reseñas por curso
        stmt = (
            select(Curso.nombre, func.count(ReseniaMetadata.id).label('total'))
            .join(ReseniaMetadata, Curso.id == ReseniaMetadata.curso_id)
            .group_by(Curso.nombre)
            .order_by(desc('total'))
        )
        
        result = await session.execute(stmt)
        rows = result.all()
        
        total_resenias = sum(row.total for row in rows)
        print(f"Total de reseñas con materia asignada: {total_resenias}\n")
        
        print(f"{'MATERIA':<60} | {'RESEÑAS'}")
        print("-" * 72)
        
        for nombre, total in rows:
            # Truncar nombre si es muy largo para visualización
            nombre_display = (nombre[:57] + '...') if len(nombre) > 57 else nombre
            print(f"{nombre_display:<60} | {total}")

if __name__ == "__main__":
    asyncio.run(show_stats())
