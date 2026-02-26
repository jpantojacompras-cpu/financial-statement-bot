"""
Módulo para detectar automáticamente:
- Institución (Banco, empresa financiera)
- Tipo de producto (Cuenta Corriente, Tarjeta de Crédito)
- Formato del archivo
"""

import pandas as pd
import re
from typing import Dict, Tuple, Any
from pathlib import Path

class FileDetector:
    """Detecta tipo de institución y producto financiero"""
    
    def __init__(self):
        self.institutions = {
            'santander': ['santander', 'bsan'],
            'bice': ['bice', 'banco bice'],
            'cmr': ['cmr', 'falabella'],
            'itau': ['itau', 'itaú'],
            'bbva': ['bbva', 'banco bbva'],
            'scotiabank': ['scotia', 'scotiabank'],
            'corfo': ['corfo', 'banco estado'],
            'chile': ['banco de chile', 'banco chile'],
            'ripley': ['ripley'],
            'paris': ['paris'],
        }
        
        self.product_types = {
            'cuenta_corriente': [
                'cuenta corriente', 'movimientos cuenta', 'saldo inicial',
                'débito', 'crédito', 'saldo final', 'disponible',
                'transferencia', 'depósito', 'giro', 'cheque'
            ],
            'tarjeta_credito': [
                'tarjeta de crédito', 'tarjeta crédito', 'cmr',
                'pago mínimo', 'cuota', 'comercio', 'fecha de vencimiento',
                'transacción', 'límite de crédito', 'saldo disponible',
                'tasa de interés', 'resumen de compras', 'compra',
                'extracto tarjeta', 'estado de cuenta tarjeta'
            ],
            'linea_credito': [
                'línea de crédito', 'giro', 'sobregiro', 'línea'
            ]
        }
    
    def detect_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analiza un archivo y detecta institución y tipo de producto
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            dict: {
                'institution': 'santander',
                'product_type': 'cuenta_corriente',
                'confidence': 0.95,
                'details': {...}
            }
        """
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            return self._detect_from_pdf(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            return self._detect_from_excel(file_path)
        else:
            return {
                'institution': 'unknown',
                'product_type': 'unknown',
                'confidence': 0.0,
                'details': {}
            }
    
    def _detect_from_excel(self, file_path: str) -> Dict[str, Any]:
        """Detecta desde archivo Excel"""
        try:
            # Leer primeras filas del Excel
            df = pd.read_excel(file_path, nrows=50, header=None)
            text_content = ' '.join(df.astype(str).values.flatten()).lower()
            
            return self._analyze_text(text_content, file_path)
            
        except Exception as e:
            print(f"Error detectando desde Excel: {e}")
            return {
                'institution': 'unknown',
                'product_type': 'unknown',
                'confidence': 0.0,
                'details': {'error': str(e)}
            }
    
    def _detect_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """Detecta desde archivo PDF"""
        try:
            import pdfplumber
            
            text_content = ""
            with pdfplumber.open(file_path) as pdf:
                # Leer primeras 3 páginas
                for page in pdf.pages[:3]:
                    text = page.extract_text()
                    if text:
                        text_content += text.lower() + " "
            
            return self._analyze_text(text_content, file_path)
            
        except ImportError:
            print("pdfplumber no instalado")
            return {
                'institution': 'unknown',
                'product_type': 'unknown',
                'confidence': 0.0,
                'details': {'error': 'pdfplumber not installed'}
            }
        except Exception as e:
            print(f"Error detectando desde PDF: {e}")
            return {
                'institution': 'unknown',
                'product_type': 'unknown',
                'confidence': 0.0,
                'details': {'error': str(e)}
            }
    
    def _analyze_text(self, text: str, file_path: str) -> Dict[str, Any]:
        """
        Analiza el contenido de texto para detectar institución y tipo
        
        Args:
            text: Contenido de texto extraído
            file_path: Ruta del archivo (para analizar nombre también)
            
        Returns:
            dict: Resultados de detección
        """
        
        # Detectar institución
        institution = self._detect_institution(text, file_path)
        
        # Detectar tipo de producto
        product_type = self._detect_product_type(text, institution['name'])
        
        # Calcular confianza
        confidence = self._calculate_confidence(text, institution, product_type)
        
        return {
            'institution': institution['name'],
            'institution_code': institution['code'],
            'product_type': product_type['type'],
            'confidence': confidence,
            'details': {
                'institution_matches': institution['matches'],
                'product_matches': product_type['matches'],
                'raw_text_sample': text[:200]
            }
        }
    
    def _detect_institution(self, text: str, file_path: str) -> Dict[str, Any]:
        """Detecta la institución financiera"""
        
        matches = {}
        
        # Buscar palabras clave de instituciones
        for institution, keywords in self.institutions.items():
            count = sum(text.count(keyword) for keyword in keywords)
            if count > 0:
                matches[institution] = count
        
        # También revisar nombre del archivo
        filename = Path(file_path).name.lower()
        for institution, keywords in self.institutions.items():
            if any(keyword in filename for keyword in keywords):
                matches[institution] = matches.get(institution, 0) + 5  # Mayor peso
        
        if not matches:
            return {
                'name': 'unknown',
                'code': None,
                'matches': matches
            }
        
        # Retornar institución con más coincidencias
        best_match = max(matches.items(), key=lambda x: x[1])
        
        return {
            'name': best_match[0],
            'code': best_match[0].upper(),
            'matches': matches
        }
    
    def _detect_product_type(self, text: str, institution: str) -> Dict[str, Any]:
        """Detecta el tipo de producto financiero"""
        
        matches = {}
        
        # Contar coincidencias por tipo
        for product_type, keywords in self.product_types.items():
            count = sum(text.count(keyword) for keyword in keywords)
            if count > 0:
                matches[product_type] = count
        
        # LÓGICA ESPECIAL PARA CMR
        # CMR es SIEMPRE tarjeta de crédito
        if 'cmr' in text and institution == 'cmr':
            return {
                'type': 'tarjeta_credito',
                'matches': matches,
                'reason': 'CMR es siempre tarjeta de crédito'
            }
        
        if not matches:
            return {
                'type': 'unknown',
                'matches': matches
            }
        
        # Retornar tipo con más coincidencias
        best_match = max(matches.items(), key=lambda x: x[1])
        
        return {
            'type': best_match[0],
            'matches': matches
        }
    
    def _calculate_confidence(self, text: str, institution: Dict, product_type: Dict) -> float:
        """
        Calcula confianza de la detección (0.0 a 1.0)
        """
        confidence = 0.0
        
        # Confianza por institución
        if institution['matches']:
            institution_score = list(institution['matches'].values())
            confidence += min(0.5, len(list(institution['matches'].values())) * 0.15)
        
        # Confianza por tipo de producto
        if product_type['matches']:
            product_score = list(product_type['matches'].values())
            confidence += min(0.5, len(list(product_type['matches'].values())) * 0.15)
        
        # Bonus si hay coincidencias fuertes
        if institution['matches']:
            max_inst_count = max(institution['matches'].values())
            if max_inst_count >= 3:
                confidence = min(1.0, confidence + 0.3)
        
        if product_type['matches']:
            max_prod_count = max(product_type['matches'].values())
            if max_prod_count >= 3:
                confidence = min(1.0, confidence + 0.3)
        
        return round(confidence, 2)