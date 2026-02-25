"""
Módulo para extracción y validación de datos
"""

from datetime import datetime
from typing import List, Tuple, Dict, Any

class DataExtractor:
    """Extrae y valida datos de movimientos"""
    
    @staticmethod
    def validate_movement(movement: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Valida que un movimiento tiene todos los campos requeridos
        
        Args:
            movement: Dict con datos del movimiento
            
        Returns:
            tuple: (es_válido, mensaje_error)
        """
        required_fields = ['fecha', 'descripcion', 'monto', 'tipo']
        
        # Verificar campos requeridos
        for field in required_fields:
            if field not in movement or movement[field] is None:
                return False, f"Campo faltante: {field}"
        
        # Validar tipo
        if movement['tipo'] not in ['ingreso', 'gasto']:
            return False, f"Tipo inválido: {movement['tipo']}. Debe ser 'ingreso' o 'gasto'"
        
        # Validar monto
        try:
            float(movement['monto'])
        except (ValueError, TypeError):
            return False, f"Monto no es un número válido: {movement['monto']}"
        
        return True, "OK"
    
    @staticmethod
    def normalize_date(date_str: str) -> str:
        """
        Normaliza fechas a formato YYYY-MM-DD
        
        Soporta múltiples formatos:
        - YYYY-MM-DD
        - DD-MM-YYYY
        - DD/MM/YYYY
        - YYYY/MM/DD
        - DD.MM.YYYY
        
        Args:
            date_str: String de fecha en diversos formatos
            
        Returns:
            str: Fecha normalizada en formato YYYY-MM-DD
        """
        formats = [
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%d.%m.%Y',
            '%d %m %Y',
            '%Y %m %d',
        ]
        
        date_str = str(date_str).strip()
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Si no se puede parsear, retorna tal cual
        print(f"⚠️  Advertencia: No se pudo normalizar fecha: {date_str}")
        return date_str
    
    @staticmethod
    def remove_duplicates(movements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Elimina movimientos duplicados
        
        Dos movimientos se consideran duplicados si tienen:
        - Misma fecha
        - Misma descripción
        - Mismo monto
        
        Args:
            movements: Lista de movimientos
            
        Returns:
            list: Movimientos sin duplicados (mantiene el primero)
        """
        seen = set()
        unique = []
        duplicates = 0
        
        for mov in movements:
            # Clave única: fecha + descripción + monto
            key = (
                str(mov.get('fecha', '')).strip(),
                str(mov.get('descripcion', '')).strip().lower(),
                float(mov.get('monto', 0))
            )
            
            if key not in seen:
                seen.add(key)
                unique.append(mov)
            else:
                duplicates += 1
        
        if duplicates > 0:
            print(f"ℹ️  Se eliminaron {duplicates} movimientos duplicados")
        
        return unique
    
    @staticmethod
    def clean_description(description: str) -> str:
        """
        Limpia la descripción de espacios y caracteres especiales
        
        Args:
            description: Descripción original
            
        Returns:
            str: Descripción limpia
        """
        # Eliminar espacios múltiples
        description = ' '.join(description.split())
        
        # Eliminar caracteres especiales problemáticos
        description = description.strip()
        
        return description
    
    @staticmethod
    def classify_transaction_type(monto: float) -> str:
        """
        Clasifica el tipo de transacción basado en el monto
        
        Args:
            monto: Monto del movimiento (puede ser positivo o negativo)
            
        Returns:
            str: 'ingreso' si es positivo, 'gasto' si es negativo
        """
        monto_float = float(monto)
        return 'ingreso' if monto_float > 0 else 'gasto'