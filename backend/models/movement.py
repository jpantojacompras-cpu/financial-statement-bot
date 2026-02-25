"""
Modelo para representar un movimiento bancario
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Movement:
    """
    Representa un movimiento bancario (transacción)
    
    Attributes:
        id: Identificador único del movimiento
        fecha: Fecha en formato YYYY-MM-DD
        descripcion: Descripción del movimiento
        monto: Cantidad de dinero (positivo=ingreso, negativo=gasto)
        tipo: 'ingreso' o 'gasto'
        categoria: Categoría principal del movimiento
        subcategoria: Subcategoría del movimiento
        archivo_referencia: Nombre del archivo de origen
        banco: Nombre del banco de origen
    """
    
    id: int
    fecha: str
    descripcion: str
    monto: float
    tipo: str  # 'ingreso' o 'gasto'
    categoria: Optional[str] = "Sin Categoría"
    subcategoria: Optional[str] = "Sin Subcategoría"
    archivo_referencia: Optional[str] = None
    banco: Optional[str] = None
    
    def to_dict(self):
        """Convierte el movimiento a diccionario"""
        return {
            'id': self.id,
            'fecha': self.fecha,
            'descripcion': self.descripcion,
            'monto': self.monto,
            'tipo': self.tipo,
            'categoria': self.categoria,
            'subcategoria': self.subcategoria,
            'archivo_referencia': self.archivo_referencia,
            'banco': self.banco
        }
    
    def __str__(self):
        """Representación en string del movimiento"""
        return f"{self.fecha} | {self.descripcion} | ${self.monto} | {self.tipo}"