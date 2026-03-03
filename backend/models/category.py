"""
Modelo para representar una categoría
"""

from dataclasses import dataclass
from typing import List

@dataclass
class Category:
    """
    Representa una categoría de movimiento
    
    Attributes:
        categoria: Nombre de la categoría principal
        subcategoria: Nombre de la subcategoría
        keywords: Lista de palabras clave para identificar automáticamente
    """
    
    categoria: str
    subcategoria: str
    keywords: List[str]
    
    def to_dict(self):
        """Convierte la categoría a diccionario"""
        return {
            'categoria': self.categoria,
            'subcategoria': self.subcategoria,
            'keywords': self.keywords
        }
    
    def matches(self, text: str) -> bool:
        """
        Verifica si el texto contiene alguna de las palabras clave
        
        Args:
            text: Texto a verificar
            
        Returns:
            True si encuentra coincidencia, False en caso contrario
        """
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in self.keywords)
    
    def __str__(self):
        """Representación en string de la categoría"""
        return f"{self.categoria} > {self.subcategoria}"