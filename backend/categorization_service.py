import pandas as pd
from typing import Tuple, Optional, Dict

class CategorizationService:
    """Servicio de categorización de movimientos"""
    
    def __init__(self, csv_path: str = "categories.csv"):
        """Carga categorías desde CSV"""
        self.categories_df = pd.read_csv(csv_path, sep=';')
        self.patterns = self._build_patterns()
        self.learned_mappings = {}  # Mapeos aprendidos del usuario
    
    def _build_patterns(self) -> Dict[str, list]:
        """Crea patrones de palabras clave para cada categoría"""
        patterns = {
            'Movilización': [
                'bencina', 'gasolina', 'combustible', 'uber', 'taxi', 'transantiago',
                'metro', 'autopista', 'peaje', 'parking', 'estacionamiento',
                'revisión técnica', 'seguro auto', 'seguro vehicular', 'bip',
                'patente', 'lavado'
            ],
            'Salud': [
                'farmacia', 'dr.', 'médico', 'doctor', 'clínica', 'hospital',
                'examen', 'procedimiento', 'dental', 'dentista', 'oftalmología',
                'psicólogo', 'isapre', 'afp', 'seguros de salud', 'lab'
            ],
            'Mascotas': [
                'veterinario', 'vet', 'pet shop', 'mascota', 'perro', 'gato',
                'comida mascotas', 'alimento mascotas'
            ],
            'Cuentas básicas': [
                'luz', 'agua', 'gas', 'internet', 'celular', 'teléfono',
                'mantenimiento', 'comisión', 'mantención', 'cuenta',
                'servicio técnico', 'donación'
            ],
            'Deudas': [
                'hipotecario', 'hipoteca', 'cuota', 'deuda', 'crédito', 'préstamo'
            ],
            'Inversiones': [
                'exness', 'trading', 'bolsa', 'acciones', 'dap', 'fondo mutuo',
                'criptomoneda', 'bitcoin', 'inversión'
            ],
            'Plataformas / Suscripciones': [
                'netflix', 'spotify', 'chatgpt', 'crunchyroll', 'suscripción',
                'adobe', 'microsoft', 'apple', 'amazon prime'
            ],
            'Entretención / Deporte': [
                'muni las condes', 'gym', 'gimnasio', 'cine', 'teatro',
                'concierto', 'deporte', 'entretención', 'cancha'
            ],
            'Alimentación': [
                'supermercado', 'jumbo', 'líder', 'santa isabel', 'walmart',
                'uber eats', 'restaurante', 'café', 'pizza', 'comida',
                'almuerzo', 'desayuno', 'cena', 'delivery'
            ],
            'Compras': [
                'aliexpress', 'shein', 'amazon', 'tienda', 'shop', 'peluquería',
                'barbería', 'ropa', 'zapatos', 'tecnología', 'electrónica',
                'casa', 'muebles', 'decoración'
            ]
        }
        return patterns
    
    def categorize(self, descripcion: str) -> Tuple[str, str]:
        """
        Categoriza un movimiento
        Retorna: (categoria, subcategoria)
        """
        if not descripcion:
            return "Sin Categoría", "Sin Subcategoría"
        
        # Transferencias internas SIEMPRE van aquí
        transfer_keywords = [
            'pago tarjeta', 'pago tdc', 'pago cmr',
            'transferencia a tarjeta', 'transferencia a t.',
            'monto cancelado', 'pago de cuenta',
            'abono tarjeta', 'nota de credito',
            'transferencia a cuenta', 'pago cuenta'
        ]
        
        desc_lower = descripcion.lower()
        if any(keyword in desc_lower for keyword in transfer_keywords):
            return "Transferencia Interna", "Interna"
        
        # Buscar en mapeos aprendidos PRIMERO
        for pattern, (cat, subcat) in self.learned_mappings.items():
            if pattern in desc_lower:
                return cat, subcat
        
        # Buscar coincidencias en patrones
        best_match = None
        best_confianza = 0.0
        
        for categoria, keywords in self.patterns.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    confianza = min(0.95, 0.5 + (len(keyword) / 50))
                    if confianza > best_confianza:
                        best_confianza = confianza
                        best_match = categoria
        
        if best_match:
            subcat = self._get_default_subcategory(best_match)
            return best_match, subcat
        
        return "Sin Categoría", "Sin Subcategoría"
    
    def _get_default_subcategory(self, categoria: str) -> str:
        """Retorna la primera subcategoría de una categoría"""
        matching = self.categories_df[
            self.categories_df['Categoría'] == categoria
        ]
        if len(matching) > 0:
            return matching.iloc[0]['Subcategoría']
        return "Sin Subcategoría"
    
    def learn_mapping(self, descripcion: str, categoria: str, subcategoria: str):
        """Aprende un nuevo mapeo del usuario"""
        pattern = descripcion.lower().split()[0]  # Primera palabra
        self.learned_mappings[pattern] = (categoria, subcategoria)
    
    def get_all_categories(self) -> list:
        """Retorna lista de todas las categorías"""
        return sorted(self.categories_df['Categoría'].unique().tolist())
    
    def get_subcategories(self, categoria: str) -> list:
        """Retorna subcategorías de una categoría"""
        matching = self.categories_df[
            self.categories_df['Categoría'] == categoria
        ]
        return matching['Subcategoría'].tolist()