#!/usr/bin/env python3
"""
Script de Limpieza de Bases de Datos - SentimentInsightUAM

Este script limpia completamente las bases de datos PostgreSQL y MongoDB,
eliminando todos los datos pero manteniendo las estructuras (esquemas, índices, etc.).

Uso:
    python scripts/clean_databases.py [--postgres] [--mongo] [--all]
    
    Sin argumentos: modo interactivo
    --postgres: limpia solo PostgreSQL
    --mongo: limpia solo MongoDB
    --all: limpia ambas bases de datos sin confirmación
    
Ejemplos:
    python scripts/clean_databases.py                # Modo interactivo
    python scripts/clean_databases.py --all          # Limpia todo
    python scripts/clean_databases.py --postgres     # Solo PostgreSQL
    python scripts/clean_databases.py --mongo        # Solo MongoDB
    
Autor: SentimentInsightUAM Team
Fecha: 2024-11-09
Versión: 1.0.0
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Agregar src al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.db import get_db_session, get_mongo_db
    from src.db.models import Base
    from sqlalchemy import text
except ImportError as e:
    print(f"❌ Error importando módulos de base de datos: {e}")
    print("\nAsegúrate de:")
    print("1. Tener instaladas las dependencias: pip install -r requirements.txt")
    print("2. Tener los contenedores Docker corriendo: make docker-up")
    sys.exit(1)


# Colores para terminal
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


async def limpiar_postgresql(verbose: bool = True) -> bool:
    """
    Limpia todas las tablas de PostgreSQL manteniendo el esquema.
    
    Args:
        verbose: Si True, imprime mensajes detallados
        
    Returns:
        bool: True si la limpieza fue exitosa, False en caso de error
    """
    if verbose:
        print(f"\n{Colors.BLUE}{'='*70}{Colors.NC}")
        print(f"{Colors.BLUE}Limpiando PostgreSQL...{Colors.NC}")
        print(f"{Colors.BLUE}{'='*70}{Colors.NC}\n")
    
    try:
        async with get_db_session() as session:
            # Orden de eliminación respetando foreign keys
            tablas_ordenadas = [
                'resenia_etiquetas',
                'perfil_etiquetas',
                'resenias_metadata',
                'historial_scraping',
                'perfiles',
                'etiquetas',
                'cursos',
                'profesores'
            ]
            
            total_eliminados = 0
            
            for tabla in tablas_ordenadas:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {tabla}"))
                count = result.scalar()
                
                if count > 0:
                    await session.execute(text(f"DELETE FROM {tabla}"))
                    if verbose:
                        print(f"  {Colors.GREEN}✅{Colors.NC} {tabla:25} - {count:5} registros eliminados")
                    total_eliminados += count
                else:
                    if verbose:
                        print(f"  {Colors.CYAN}ℹ️{Colors.NC}  {tabla:25} - (vacía)")
            
            # Reset de secuencias (auto-increment IDs)
            secuencias = [
                'profesores_id_seq',
                'perfiles_id_seq',
                'etiquetas_id_seq',
                'cursos_id_seq',
                'resenias_metadata_id_seq',
                'historial_scraping_id_seq'
            ]
            
            if verbose:
                print(f"\n{Colors.YELLOW}Reiniciando secuencias...{Colors.NC}")
            
            for secuencia in secuencias:
                try:
                    await session.execute(text(f"ALTER SEQUENCE {secuencia} RESTART WITH 1"))
                    if verbose:
                        print(f"  {Colors.GREEN}✅{Colors.NC} {secuencia}")
                except Exception as e:
                    if verbose:
                        print(f"  {Colors.YELLOW}⚠️{Colors.NC}  {secuencia} - {str(e)}")
            
            await session.commit()
            
            if verbose:
                print(f"\n{Colors.GREEN}{'='*70}{Colors.NC}")
                print(f"{Colors.GREEN}✅ PostgreSQL limpiada exitosamente{Colors.NC}")
                print(f"{Colors.GREEN}   Total de registros eliminados: {total_eliminados}{Colors.NC}")
                print(f"{Colors.GREEN}{'='*70}{Colors.NC}")
            
            return True
            
    except Exception as e:
        if verbose:
            print(f"\n{Colors.RED}{'='*70}{Colors.NC}")
            print(f"{Colors.RED}❌ Error limpiando PostgreSQL: {str(e)}{Colors.NC}")
            print(f"{Colors.RED}{'='*70}{Colors.NC}")
        return False


async def limpiar_mongodb(verbose: bool = True) -> bool:
    """
    Limpia todas las colecciones de MongoDB manteniendo índices.
    
    Args:
        verbose: Si True, imprime mensajes detallados
        
    Returns:
        bool: True si la limpieza fue exitosa, False en caso de error
    """
    if verbose:
        print(f"\n{Colors.BLUE}{'='*70}{Colors.NC}")
        print(f"{Colors.BLUE}Limpiando MongoDB...{Colors.NC}")
        print(f"{Colors.BLUE}{'='*70}{Colors.NC}\n")
    
    try:
        db = get_mongo_db()
        
        # Colecciones a limpiar
        colecciones = ['opiniones']
        
        total_eliminados = 0
        
        for coleccion_nombre in colecciones:
            coleccion = db[coleccion_nombre]
            
            # Contar documentos antes de eliminar
            count = await coleccion.count_documents({})
            
            if count > 0:
                # Eliminar todos los documentos
                result = await coleccion.delete_many({})
                if verbose:
                    print(f"  {Colors.GREEN}✅{Colors.NC} {coleccion_nombre:25} - {result.deleted_count:5} documentos eliminados")
                total_eliminados += result.deleted_count
            else:
                if verbose:
                    print(f"  {Colors.CYAN}ℹ️{Colors.NC}  {coleccion_nombre:25} - (vacía)")
        
        if verbose:
            print(f"\n{Colors.GREEN}{'='*70}{Colors.NC}")
            print(f"{Colors.GREEN}✅ MongoDB limpiada exitosamente{Colors.NC}")
            print(f"{Colors.GREEN}   Total de documentos eliminados: {total_eliminados}{Colors.NC}")
            print(f"{Colors.GREEN}{'='*70}{Colors.NC}")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"\n{Colors.RED}{'='*70}{Colors.NC}")
            print(f"{Colors.RED}❌ Error limpiando MongoDB: {str(e)}{Colors.NC}")
            print(f"{Colors.RED}{'='*70}{Colors.NC}")
        return False


async def verificar_limpieza(verbose: bool = True) -> dict:
    """
    Verifica que las bases de datos estén vacías.
    
    Args:
        verbose: Si True, imprime mensajes detallados
        
    Returns:
        dict: Diccionario con conteos de registros por tabla/colección
    """
    if verbose:
        print(f"\n{Colors.CYAN}{'='*70}{Colors.NC}")
        print(f"{Colors.CYAN}Verificando limpieza...{Colors.NC}")
        print(f"{Colors.CYAN}{'='*70}{Colors.NC}\n")
    
    resultados = {
        'postgresql': {},
        'mongodb': {},
        'limpio': True
    }
    
    # Verificar PostgreSQL
    try:
        async with get_db_session() as session:
            tablas = ['profesores', 'perfiles', 'etiquetas', 'cursos', 
                     'resenias_metadata', 'historial_scraping',
                     'perfil_etiquetas', 'resenia_etiquetas']
            
            if verbose:
                print(f"{Colors.BLUE}PostgreSQL:{Colors.NC}")
            
            for tabla in tablas:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {tabla}"))
                count = result.scalar()
                resultados['postgresql'][tabla] = count
                
                if count > 0:
                    resultados['limpio'] = False
                    if verbose:
                        print(f"  {Colors.YELLOW}⚠️{Colors.NC}  {tabla:25} - {count} registros")
                else:
                    if verbose:
                        print(f"  {Colors.GREEN}✅{Colors.NC} {tabla:25} - vacía")
    
    except Exception as e:
        if verbose:
            print(f"  {Colors.RED}❌ Error verificando PostgreSQL: {str(e)}{Colors.NC}")
        resultados['limpio'] = False
    
    # Verificar MongoDB
    try:
        db = get_mongo_db()
        colecciones = ['opiniones']
        
        if verbose:
            print(f"\n{Colors.BLUE}MongoDB:{Colors.NC}")
        
        for coleccion_nombre in colecciones:
            coleccion = db[coleccion_nombre]
            count = await coleccion.count_documents({})
            resultados['mongodb'][coleccion_nombre] = count
            
            if count > 0:
                resultados['limpio'] = False
                if verbose:
                    print(f"  {Colors.YELLOW}⚠️{Colors.NC}  {coleccion_nombre:25} - {count} documentos")
            else:
                if verbose:
                    print(f"  {Colors.GREEN}✅{Colors.NC} {coleccion_nombre:25} - vacía")
    
    except Exception as e:
        if verbose:
            print(f"  {Colors.RED}❌ Error verificando MongoDB: {str(e)}{Colors.NC}")
        resultados['limpio'] = False
    
    if verbose:
        print(f"\n{Colors.CYAN}{'='*70}{Colors.NC}")
        if resultados['limpio']:
            print(f"{Colors.GREEN}✅ Todas las bases de datos están limpias{Colors.NC}")
        else:
            print(f"{Colors.YELLOW}⚠️  Algunas tablas/colecciones aún contienen datos{Colors.NC}")
        print(f"{Colors.CYAN}{'='*70}{Colors.NC}")
    
    return resultados


def confirmar_accion(mensaje: str) -> bool:
    """
    Solicita confirmación del usuario.
    
    Args:
        mensaje: Mensaje a mostrar
        
    Returns:
        bool: True si el usuario confirma, False en caso contrario
    """
    while True:
        respuesta = input(f"\n{Colors.YELLOW}{mensaje} (s/n): {Colors.NC}").lower().strip()
        if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
            return True
        elif respuesta in ['n', 'no']:
            return False
        else:
            print(f"{Colors.RED}Por favor responde 's' o 'n'{Colors.NC}")


async def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description='Limpia las bases de datos de SentimentInsightUAM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python scripts/clean_databases.py              # Modo interactivo
  python scripts/clean_databases.py --all        # Limpia todo sin confirmación
  python scripts/clean_databases.py --postgres   # Solo PostgreSQL
  python scripts/clean_databases.py --mongo      # Solo MongoDB
  python scripts/clean_databases.py --verify     # Solo verifica estado
        """
    )
    
    parser.add_argument('--postgres', action='store_true',
                       help='Limpiar solo PostgreSQL')
    parser.add_argument('--mongo', action='store_true',
                       help='Limpiar solo MongoDB')
    parser.add_argument('--all', action='store_true',
                       help='Limpiar ambas bases de datos sin confirmación')
    parser.add_argument('--verify', action='store_true',
                       help='Solo verificar el estado de las bases de datos')
    parser.add_argument('--quiet', action='store_true',
                       help='Modo silencioso (solo errores)')
    
    args = parser.parse_args()
    verbose = not args.quiet
    
    # Banner
    if verbose:
        print(f"\n{Colors.CYAN}{'='*70}{Colors.NC}")
        print(f"{Colors.CYAN}Script de Limpieza de Bases de Datos - SentimentInsightUAM{Colors.NC}")
        print(f"{Colors.CYAN}Versión 1.0.0 - 2024-11-09{Colors.NC}")
        print(f"{Colors.CYAN}{'='*70}{Colors.NC}")
    
    # Modo solo verificación
    if args.verify:
        await verificar_limpieza(verbose=verbose)
        return
    
    # Determinar qué limpiar
    limpiar_pg = args.postgres or args.all
    limpiar_mg = args.mongo or args.all
    
    # Si no se especificó nada, modo interactivo
    if not (args.postgres or args.mongo or args.all):
        if verbose:
            print(f"\n{Colors.YELLOW}Modo interactivo{Colors.NC}")
            print("\nEste script eliminará TODOS los datos de las bases de datos.")
            print("Los esquemas, índices y estructuras se mantendrán intactos.")
        
        limpiar_pg = confirmar_accion("¿Deseas limpiar PostgreSQL?")
        limpiar_mg = confirmar_accion("¿Deseas limpiar MongoDB?")
        
        if not (limpiar_pg or limpiar_mg):
            print(f"\n{Colors.YELLOW}Operación cancelada.{Colors.NC}\n")
            return
    
    # Confirmación final en modo --all
    if args.all and verbose:
        print(f"\n{Colors.RED}{'='*70}{Colors.NC}")
        print(f"{Colors.RED}⚠️  ADVERTENCIA: Esta operación eliminará TODOS los datos{Colors.NC}")
        print(f"{Colors.RED}{'='*70}{Colors.NC}")
    
    # Ejecutar limpieza
    exito_total = True
    
    if limpiar_pg:
        exito_pg = await limpiar_postgresql(verbose=verbose)
        exito_total = exito_total and exito_pg
    
    if limpiar_mg:
        exito_mg = await limpiar_mongodb(verbose=verbose)
        exito_total = exito_total and exito_mg
    
    # Verificación final
    if exito_total:
        await verificar_limpieza(verbose=verbose)
    
    # Resultado final
    if verbose:
        print()
        if exito_total:
            print(f"{Colors.GREEN}✅ Limpieza completada exitosamente{Colors.NC}\n")
            sys.exit(0)
        else:
            print(f"{Colors.RED}❌ Hubo errores durante la limpieza{Colors.NC}\n")
            sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Operación cancelada por el usuario.{Colors.NC}\n")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Error fatal: {str(e)}{Colors.NC}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
