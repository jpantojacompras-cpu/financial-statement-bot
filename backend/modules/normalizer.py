"""
Módulo para normalización y consolidación de datos
"""

import pandas as pd
from typing import List, Dict, Any

class DataNormalizer:
    """Normaliza y consolida movimientos de múltiples fuentes"""
    
    @staticmethod
    def consolidate(all_movements: List[List[Dict[str, Any]]]) -> pd.DataFrame:
        """
        Consolida todos los movimientos en un único DataFrame
        
        Args:
            all_movements: Lista de listas de movimientos (de múltiples archivos)
            
        Returns:
            pd.DataFrame: Datos consolidados y normalizados
        """
        # Aplanar lista de listas en una única lista
        flat_movements = []
        for movements_list in all_movements:
            if isinstance(movements_list, list):
                flat_movements.extend(movements_list)
            else:
                flat_movements.append(movements_list)
        
        if not flat_movements:
            print("⚠️  No hay movimientos para consolidar")
            return pd.DataFrame()
        
        # Convertir a DataFrame
        df = pd.DataFrame(flat_movements)
        
        # Normalizar tipos de datos
        df = DataNormalizer._normalize_types(df)
        
        # Ordenar por fecha
        if 'fecha' in df.columns:
            df = df.sort_values('fecha').reset_index(drop=True)
        
        print(f"✅ Se consolidaron {len(df)} movimientos")
        
        return df
    
    @staticmethod
    def _normalize_types(df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza tipos de datos del DataFrame
        
        Args:
            df: DataFrame a normalizar
            
        Returns:
            pd.DataFrame: DataFrame con tipos normalizados
        """
        if 'fecha' in df.columns:
            try:
                df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce').dt.strftime('%Y-%m-%d')
            except Exception as e:
                print(f"❌ Error normalizando fechas: {e}")
        
        if 'monto' in df.columns:
            try:
                df['monto'] = pd.to_numeric(df['monto'], errors='coerce')
            except Exception as e:
                print(f"❌ Error normalizando montos: {e}")
        
        # Asegurar que las columnas texto sean strings
        for col in ['descripcion', 'categoria', 'subcategoria', 'archivo_referencia', 'banco']:
            if col in df.columns:
                df[col] = df[col].astype(str)
        
        return df
    
    @staticmethod
    def save_to_csv(df: pd.DataFrame, output_path: str) -> bool:
        """
        Guarda el DataFrame consolidado a CSV
        
        Args:
            df: DataFrame a guardar
            output_path: Ruta del archivo de salida
            
        Returns:
            bool: True si se guardó exitosamente, False en caso contrario
        """
        try:
            df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"✅ Archivo guardado en: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Error guardando CSV: {e}")
            return False
    
    @staticmethod
    def load_from_csv(csv_path: str) -> pd.DataFrame:
        """
        Carga un archivo maestro desde CSV
        
        Args:
            csv_path: Ruta del archivo CSV
            
        Returns:
            pd.DataFrame: Datos cargados
        """
        try:
            df = pd.read_csv(csv_path)
            print(f"✅ Archivo cargado desde: {csv_path}")
            return df
        except Exception as e:
            print(f"❌ Error cargando CSV: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Obtiene estadísticas resumidas del DataFrame
        
        Args:
            df: DataFrame con movimientos
            
        Returns:
            dict: Estadísticas (total ingresos, gastos, etc.)
        """
        if df.empty:
            return {
                'total_movimientos': 0,
                'total_ingresos': 0,
                'total_gastos': 0,
                'saldo': 0
            }
        
        ingresos = df[df['tipo'] == 'ingreso']['monto'].sum() if 'tipo' in df.columns else 0
        gastos = df[df['tipo'] == 'gasto']['monto'].sum() if 'tipo' in df.columns else 0
        
        return {
            'total_movimientos': len(df),
            'total_ingresos': float(ingresos),
            'total_gastos': float(abs(gastos)),
            'saldo': float(ingresos + gastos)
        }