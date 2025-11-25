"""
Módulo de normalización de nombres de materias utilizando Fuzzy Matching.
"""
import os
from pathlib import Path
from typing import List, Optional, Tuple
from rapidfuzz import process, fuzz

class CourseNormalizer:
    _instance = None
    _materias_oficiales: List[str] = []
    _cache: dict = {}
    
    # Umbral de similitud para considerar un match válido (0-100)
    # 85 es un buen punto de partida: permite "Proba y Estadistica" -> "Probabilidad y Estadística"
    # pero evita falsos positivos agresivos.
    THRESHOLD = 85

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CourseNormalizer, cls).__new__(cls)
            cls._instance._load_materias()
        return cls._instance

    def _load_materias(self):
        """Carga la lista oficial de materias desde el archivo de texto."""
        # Asumiendo que el archivo está en data/inputs/materias.txt relativo a la raíz del proyecto
        # Ajustar ruta según la estructura del proyecto
        base_path = Path(__file__).parent.parent.parent
        file_path = base_path / "data" / "inputs" / "materias.txt"
        
        if not file_path.exists():
            print(f"⚠️ Advertencia: No se encontró el archivo de materias en {file_path}")
            self._materias_oficiales = []
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Leer líneas, limpiar espacios y filtrar vacías
                self._materias_oficiales = [line.strip() for line in f if line.strip()]
            print(f"✅ CourseNormalizer cargado con {len(self._materias_oficiales)} materias oficiales.")
        except Exception as e:
            print(f"❌ Error cargando materias.txt: {e}")
            self._materias_oficiales = []

    def normalize(self, input_name: str) -> Tuple[str, float, bool]:
        """
        Normaliza un nombre de materia buscando la mejor coincidencia en la lista oficial.
        
        Args:
            input_name: Nombre de la materia a normalizar (ej. "Proba")
            
        Returns:
            Tuple[str, float, bool]: 
                - Nombre normalizado (o el original si no hubo match)
                - Score de similitud (0-100)
                - Bool indicando si fue un match exitoso (score >= THRESHOLD)
        """
        if not input_name or not isinstance(input_name, str):
            return input_name, 0.0, False
            
        input_name = input_name.strip()
        if not input_name:
            return input_name, 0.0, False

        # Verificar caché
        if input_name in self._cache:
            return self._cache[input_name]

        if not self._materias_oficiales:
            return input_name, 0.0, False

        # Fuzzy matching
        # extractOne retorna (match, score, index)
        result = process.extractOne(
            input_name, 
            self._materias_oficiales, 
            scorer=fuzz.WRatio
        )
        
        if result:
            match_name, score, _ = result
            is_match = score >= self.THRESHOLD
            
            final_name = match_name if is_match else input_name
            
            # Guardar en caché
            self._cache[input_name] = (final_name, score, is_match)
            
            return final_name, score, is_match
            
        return input_name, 0.0, False

    def get_stats(self):
        return {
            "total_oficiales": len(self._materias_oficiales),
            "cache_size": len(self._cache)
        }
