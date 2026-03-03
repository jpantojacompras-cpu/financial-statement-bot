import pandas as pd
from typing import Tuple, Optional, Dict
from pathlib import Path
import json

class CategorizationService:
    """Servicio de categorización de movimientos con aprendizaje"""
    
    def __init__(self, csv_path: str = "categories.csv", mappings_path: str = "processed_files/movimento_categorizations.json"):
        """Carga categorías desde CSV y mapeos aprendidos"""
        self.csv_path = csv_path
        self.mappings_path = Path(mappings_path)
        self.categories_df = pd.read_csv(csv_path, sep=';')
        self.patterns = self._build_patterns()
        self.learned_mappings = self._load_learned_mappings()
    
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
    
    def _load_learned_mappings(self) -> Dict[str, Dict]:
        """Carga mapeos aprendidos del JSON"""
        if self.mappings_path.exists():
            try:
                with open(self.mappings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Error cargando mapeos: {e}")
                return {}
        return {}
    
    def _save_learned_mappings(self):
        """Guarda mapeos aprendidos al JSON"""
        try:
            self.mappings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.mappings_path, 'w', encoding='utf-8') as f:
                json.dump(self.learned_mappings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ Error guardando mapeos: {e}")
    
    def categorize(self, descripcion: str) -> Tuple[str, str]:
        """
        Categoriza un movimiento
        Retorna: (categoria, subcategoria)
        
        Orden de prioridad:
        1. Transferencias internas
        2. Mapeos aprendidos del usuario
        3. Patrones predefinidos
        4. Sin Categoría
        """
        if not descripcion:
            return "Sin Categoría", "Sin Subcategoría"
        
        desc_lower = descripcion.lower()
        
        # 1️⃣ TRANSFERENCIAS INTERNAS - Máxima prioridad
        transfer_keywords = [
            'pago tarjeta', 'pago tdc', 'pago cmr',
            'transferencia a tarjeta', 'transferencia a t.',
            'monto cancelado', 'pago de cuenta',
            'abono tarjeta', 'nota de credito',
            'transferencia a cuenta', 'pago cuenta'
        ]
        
        if any(keyword in desc_lower for keyword in transfer_keywords):
            return "Transferencia Interna", "Interna"
        
        # 2️⃣ MAPEOS APRENDIDOS - Segunda prioridad (lo que el usuario aprendió)
        for pattern, mapping in self.learned_mappings.items():
            if pattern.lower() in desc_lower:
                return mapping['categoria'], mapping['subcategoria']
        
        # 3️⃣ PATRONES PREDEFINIDOS - Tercera prioridad
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
        
        # 4️⃣ SIN CATEGORÍA
        return "Sin Categoría", "Sin Subcategoría"
    
    def _get_default_subcategory(self, categoria: str) -> str:
        """Retorna la primera subcategoría de una categoría"""
        matching = self.categories_df[
            self.categories_df['Categoría'] == categoria
        ]
        if len(matching) > 0:
            return matching.iloc[0]['Subcategoría']
        return "Sin Subcategoría"
    
    def learn_mapping(self, pattern: str, categoria: str, subcategoria: str) -> Dict:
        """
        Aprende un nuevo mapeo del usuario
        
        Args:
            pattern: Palabra clave a buscar (ej: "exness")
            categoria: Categoría asignada
            subcategoria: Subcategoría asignada
        
        Returns:
            Dict con el mapeo guardado
        """
        pattern_lower = pattern.lower()
        
        self.learned_mappings[pattern_lower] = {
            'categoria': categoria,
            'subcategoria': subcategoria,
            'veces_asignada': self.learned_mappings.get(pattern_lower, {}).get('veces_asignada', 0) + 1,
            'fecha_ultima_actualizacion': pd.Timestamp.now().isoformat()
        }
        
        self._save_learned_mappings()
        
        return self.learned_mappings[pattern_lower]
    
    def unlearn_mapping(self, pattern: str) -> bool:
        """Elimina un mapeo aprendido"""
        pattern_lower = pattern.lower()
        if pattern_lower in self.learned_mappings:
            del self.learned_mappings[pattern_lower]
            self._save_learned_mappings()
            return True
        return False
    
    def get_all_categories(self) -> list:
        """Retorna lista de todas las categorías"""
        return sorted(self.categories_df['Categoría'].unique().tolist())
    
    def get_subcategories(self, categoria: str) -> list:
        """Retorna subcategorías de una categoría"""
        matching = self.categories_df[
            self.categories_df['Categoría'] == categoria
        ]
        return matching['Subcategoría'].tolist()
    
    def get_learned_mappings(self) -> Dict:
        """Retorna todos los mapeos aprendidos"""
        return self.learned_mappings