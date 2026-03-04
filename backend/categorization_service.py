import pandas as pd
from typing import Tuple, Dict

class CategorizationService:
    """Servicio de categorización de movimientos"""

    def __init__(self, csv_path: str = "categories.csv"):
        """Carga categorías desde CSV y precalcula índices de búsqueda."""
        self.categories_df = pd.read_csv(csv_path, sep=';')
        self.patterns = self._build_patterns()
        self.learned_mappings: Dict[str, Tuple[str, str]] = {}
        # Inverted index: keyword → (category, confidence)
        self._inverted_index: Dict[str, Tuple[str, float]] = self._build_inverted_index()
        # Cache of parsed results keyed by description
        self._categorize_cache: Dict[str, Tuple[str, str]] = {}
        # Cached subcategory lookup
        self._default_subcat_cache: Dict[str, str] = {}

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

    def _build_inverted_index(self) -> Dict[str, Tuple[str, float]]:
        """Construye índice invertido keyword→(categoría, confianza) para búsqueda O(1)."""
        index: Dict[str, Tuple[str, float]] = {}
        for categoria, keywords in self.patterns.items():
            for keyword in keywords:
                confidence = min(0.95, 0.5 + (len(keyword) / 50))
                existing = index.get(keyword)
                if existing is None or confidence > existing[1]:
                    index[keyword] = (categoria, confidence)
        return index

    def categorize(self, descripcion: str) -> Tuple[str, str]:
        """
        Categoriza un movimiento.
        Retorna: (categoria, subcategoria)
        """
        if not descripcion:
            return "Sin Categoría", "Sin Subcategoría"

        desc_lower = descripcion.lower()

        # Return from description cache if available
        cached = self._categorize_cache.get(desc_lower)
        if cached is not None:
            return cached

        # Transferencias internas SIEMPRE van aquí
        transfer_keywords = [
            'pago tarjeta', 'pago tdc', 'pago cmr',
            'transferencia a tarjeta', 'transferencia a t.',
            'monto cancelado', 'pago de cuenta',
            'abono tarjeta', 'nota de credito',
            'transferencia a cuenta', 'pago cuenta'
        ]

        if any(keyword in desc_lower for keyword in transfer_keywords):
            result: Tuple[str, str] = ("Transferencia Interna", "Interna")
            self._categorize_cache[desc_lower] = result
            return result

        # Buscar en mapeos aprendidos PRIMERO
        for pattern, (cat, subcat) in self.learned_mappings.items():
            if pattern in desc_lower:
                result = (cat, subcat)
                self._categorize_cache[desc_lower] = result
                return result

        # Búsqueda rápida via índice invertido
        best_match: str | None = None
        best_confianza = 0.0

        for keyword, (categoria, confidence) in self._inverted_index.items():
            if keyword in desc_lower and confidence > best_confianza:
                best_confianza = confidence
                best_match = categoria

        if best_match:
            subcat = self._get_default_subcategory(best_match)
            result = (best_match, subcat)
            self._categorize_cache[desc_lower] = result
            return result

        result = ("Sin Categoría", "Sin Subcategoría")
        self._categorize_cache[desc_lower] = result
        return result

    def _get_default_subcategory(self, categoria: str) -> str:
        """Retorna la primera subcategoría de una categoría (con caché)."""
        cached_subcat = self._default_subcat_cache.get(categoria)
        if cached_subcat is not None:
            return cached_subcat

        matching = self.categories_df[self.categories_df['Categoría'] == categoria]
        subcat = matching.iloc[0]['Subcategoría'] if len(matching) > 0 else "Sin Subcategoría"
        self._default_subcat_cache[categoria] = subcat
        return subcat

    def learn_mapping(self, descripcion: str, categoria: str, subcategoria: str) -> None:
        """Aprende un nuevo mapeo del usuario e invalida caché relacionado."""
        pattern = descripcion.lower().split()[0]  # Primera palabra
        self.learned_mappings[pattern] = (categoria, subcategoria)
        # Invalidate description cache entries that contain this pattern
        keys_to_delete = [k for k in self._categorize_cache if pattern in k]
        for key in keys_to_delete:
            del self._categorize_cache[key]

    def get_all_categories(self) -> list:
        """Retorna lista de todas las categorías"""
        return sorted(self.categories_df['Categoría'].unique().tolist())

    def get_subcategories(self, categoria: str) -> list:
        """Retorna subcategorías de una categoría"""
        matching = self.categories_df[self.categories_df['Categoría'] == categoria]
        return matching['Subcategoría'].tolist()
