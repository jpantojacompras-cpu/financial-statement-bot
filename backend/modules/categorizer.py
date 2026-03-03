"""
Módulo para categorización automática de movimientos
"""

import pandas as pd
from typing import List, Dict, Any, Tuple

class SimpleCategorizer:
    """Categoriza movimientos usando lookup table simple"""
    
    def __init__(self, categories_csv_path=None):
        """
        Inicializa el categorizador
        
        Args:
            categories_csv_path: Ruta al archivo de categorías (opcional)
        """
        self.categories_df = None
        if categories_csv_path:
            self.load_categories(categories_csv_path)
    
    def load_categories(self, csv_path: str) -> bool:
        """
        Carga el archivo de categorías
        
        Args:
            csv_path: Ruta al CSV de categorías
            
        Returns:
            bool: True si se cargó exitosamente
        """
        try:
            self.categories_df = pd.read_csv(csv_path)
            print(f"✅ Categorías cargadas desde: {csv_path}")
            return True
        except Exception as e:
            print(f"⚠️  Error cargando categorías: {e}")
            self.categories_df = pd.DataFrame()
            return False
    
    def categorize(self, description: str) -> Tuple[str, str]:
        """
        Categoriza una descripción
        
        Args:
            description: Descripción del movimiento
            
        Returns:
            tuple: (categoría, subcategoría)
        """
        if self.categories_df is None or self.categories_df.empty:
            return "Sin Categoría", "Sin Subcategoría"
        
        description_lower = str(description).lower()
        
        try:
            for _, row in self.categories_df.iterrows():
                keywords = str(row.get('keywords', '')).lower().split(',')
                
                for keyword in keywords:
                    keyword_clean = keyword.strip()
                    if keyword_clean and keyword_clean in description_lower:
                        return (
                            str(row.get('categoria', 'Sin Categoría')),
                            str(row.get('subcategoria', 'Sin Subcategoría'))
                        )
        except Exception as e:
            print(f"⚠️  Error categorizando: {e}")
        
        return "Sin Categoría", "Sin Subcategoría"
    
    def categorize_batch(self, movements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Categoriza un lote de movimientos
        
        Args:
            movements: Lista de movimientos
            
        Returns:
            list: Movimientos categorizados
        """
        categorized = []
        
        for movement in movements:
            try:
                cat, subcat = self.categorize(movement.get('descripcion', ''))
                movement['categoria'] = cat
                movement['subcategoria'] = subcat
                categorized.append(movement)
            except Exception as e:
                print(f"⚠️  Error categorizando movimiento: {e}")
                movement['categoria'] = "Sin Categoría"
                movement['subcategoria'] = "Sin Subcategoría"
                categorized.append(movement)
        
        return categorized