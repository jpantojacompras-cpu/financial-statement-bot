"""
Módulo universal para leer archivos Excel y PDF
Detecta automáticamente: Banco, Tipo de Producto
Soporta: BICE CC, CMR TC, Santander CC, Santander TC
"""

import pandas as pd
import pdfplumber
from pathlib import Path
from typing import List, Dict, Any, Tuple
import re
from datetime import datetime

class FileReader:
    """Lee archivos XLSX y PDF detectando automáticamente banco y tipo de producto"""

    def __init__(self):
        self.supported_formats = ['.xlsx', '.pdf']

    def read_xlsx(self, file_path):
        """Lee un archivo Excel"""
        try:
            filename = Path(file_path).name.lower()
            print(f"\n📄 Procesando XLSX: {filename}")

            df = pd.read_excel(file_path)
            
            # Detectar banco y tipo desde contenido
            detection = self._detect_from_dataframe(df)
            print(f"   Banco: {detection['bank']} | Tipo: {detection['product_type']}")

            movements = self._extract_from_dataframe(df, file_path, detection)
            
            if not movements:
                print(f"   Intentando saltar filas...")
                for skip_rows in range(1, 15):
                    try:
                        df = pd.read_excel(file_path, skiprows=skip_rows)
                        movements = self._extract_from_dataframe(df, file_path, detection)
                        if movements:
                            print(f"   Datos encontrados saltando {skip_rows} fila(s)")
                            break
                    except:
                        continue

            print(f"   Total movimientos: {len(movements)}")
            return movements

        except Exception as e:
            print(f"Error leyendo XLSX: {e}")
            return []

    def read_pdf(self, file_path):
        """Lee un archivo PDF detectando automáticamente el contenido"""
        try:
            filename = Path(file_path).name.lower()
            print(f"\n📄 Procesando PDF: {filename}")

            movements = []

            with pdfplumber.open(file_path) as pdf:
                print(f"   Total de páginas: {len(pdf.pages)}")

                # Detectar banco y tipo desde primeras páginas
                detection = self._detect_from_pdf(pdf)
                print(f"   Banco: {detection['bank']} | Tipo: {detection['product_type']}")

                # Procesar todas las páginas con el parser correcto
                for page_num, page in enumerate(pdf.pages, 1):
                    print(f"   Procesando página {page_num}...")
                    
                    text = page.extract_text()
                    if not text:
                        continue

                    page_movements = self._extract_movements_from_text(
                        text, 
                        file_path, 
                        detection['bank'],
                        detection['product_type'],
                        page=page
                    )
                    
                    if page_movements:
                        movements.extend(page_movements)
                        print(f"      → {len(page_movements)} movimientos")

            print(f"   Total movimientos extraídos: {len(movements)}")
            return movements

        except ImportError:
            print(f"Error: pdfplumber no instalado")
            return []
        except Exception as e:
            print(f"Error leyendo PDF: {e}")
            return []

    def _detect_from_pdf(self, pdf) -> Dict[str, str]:
        """Detecta banco y tipo de producto desde el PDF"""
        full_text = ""
        
        # Leer primeras 5 páginas
        for page in pdf.pages[:5]:
            text = page.extract_text()
            if text:
                full_text += text.lower() + " "
        
        return self._analyze_content(full_text)

    def _detect_from_dataframe(self, df) -> Dict[str, str]:
        """Detecta banco y tipo desde DataFrame"""
        text = ' '.join(df.astype(str).values.flatten()).lower()
        return self._analyze_content(text)

    def _analyze_content(self, text: str) -> Dict[str, str]:
        """Analiza contenido para detectar banco y tipo de producto"""
        
        text_lower = text.lower()
        
        # Detectar banco
        bank = self._detect_bank(text_lower)
        
        # Detectar tipo de producto
        product_type = self._detect_product_type(text_lower, bank)
        
        return {
            'bank': bank,
            'product_type': product_type
        }

    def _detect_bank(self, text: str) -> str:
        """Detecta el banco desde el texto"""
        
        # Palabras clave por banco (bice antes de santander y cmr para evitar
        # falsos positivos cuando transacciones mencionan otros bancos)
        patterns = {
            'bice': ['banco bice', 'bice'],
            'santander': ['santander', 'banco santander', 's a n t a n d e r'],
            'cmr': ['cmr', 'falabella', 'tarjeta cmr'],
            'itau': ['itau', 'itaú', 'banco itau'],
            'bbva': ['bbva', 'banco bbva'],
            'scotiabank': ['scotia', 'scotiabank'],
        }
        
        for bank, keywords in patterns.items():
            for keyword in keywords:
                if keyword in text:
                    return bank.upper()
        
        return 'DESCONOCIDO'

    def _detect_product_type(self, text: str, bank: str) -> str:
        """Detecta tipo de producto (Cuenta Corriente o Tarjeta Crédito)"""
        
        # CMR es SIEMPRE tarjeta de crédito
        if bank == 'CMR':
            return 'TARJETA_CREDITO'
        
        # Palabras clave para tarjeta de crédito
        credit_card_keywords = [
            'tarjeta de credito', 'tarjeta crédito', 'tdc',
            'compras nacionales', 'comercios', 'limite de credito',
            'pago minimo', 'fecha vencimiento', 'movimientos tarjeta',
            'extracto tarjeta', 'estado tarjeta'
        ]
        
        # Palabras clave para cuenta corriente
        checking_keywords = [
            'cuenta corriente', 'cuenta en pesos', 'movimientos cuenta',
            'saldo inicial', 'saldo final', 'transferencia', 'deposito',
            'giro', 'cheque', 'sobregiro', 'disponible'
        ]
        
        cc_count = sum(text.count(keyword) for keyword in credit_card_keywords)
        checking_count = sum(text.count(keyword) for keyword in checking_keywords)
        
        if cc_count > checking_count:
            return 'TARJETA_CREDITO'
        else:
            return 'CUENTA_CORRIENTE'

    def _extract_movements_from_text(self, text: str, file_path: str, bank: str, product_type: str, page=None) -> List[Dict]:
        """Extrae movimientos según banco y tipo de producto"""
        
        if bank == 'CMR':
            return self._parse_cmr_cc(text, file_path)
        elif bank == 'SANTANDER' and product_type == 'TARJETA_CREDITO':
            return self._parse_santander_cc(text, file_path)
        elif bank == 'SANTANDER' and product_type == 'CUENTA_CORRIENTE':
            return self._parse_santander_checking(text, file_path, page=page)
        elif bank == 'BICE' and product_type == 'CUENTA_CORRIENTE':
            return self._parse_bice_checking(text, file_path)
        else:
            # Parser genérico
            return self._parse_generic(text, file_path)

    def _parse_cmr_cc(self, text: str, file_path: str) -> List[Dict]:
        """Parser CMR Tarjeta de Crédito"""
        movements = []
        lines = text.split('\n')

        fecha_pattern = r'(\d{1,2}/\d{1,2}/\d{4})'

        for line in lines:
            line = line.strip()
            
            if not line or len(line) < 15:
                continue
            
            if any(word in line.lower() for word in ['compras nacionales', 'sin movimientos', 'cargos', 'resumen', 'total', 'página']):
                continue

            fecha_match = re.search(fecha_pattern, line)
            if not fecha_match:
                continue

            try:
                fecha_str = fecha_match.group(1)
                fecha = self._parse_date(fecha_str, '%d/%m/%Y')
                if not fecha:
                    continue

                # Extraer descripción y monto
                fecha_end = fecha_match.end()
                resto = line[fecha_end:].strip()

                # Buscar montos
                montos = re.findall(r'\$\s*(\d+(?:\.\d{3})*(?:,\d{2})?)', resto)
                if not montos:
                    continue

                monto_str = montos[-1]
                monto = self._parse_amount(monto_str)

                if not monto or monto <= 0 or monto > 100000000:
                    continue

                # Descripción
                monto_idx = resto.rfind(f"${monto_str}")
                if monto_idx < 0:
                    monto_idx = resto.rfind(monto_str)
                
                descripcion_raw = resto[:monto_idx].strip() if monto_idx > 0 else resto
                descripcion = self._clean_description(descripcion_raw)

                if not descripcion or len(descripcion) < 3:
                    continue

                movement = {
                    "id": len(movements),
                    "fecha": fecha,
                    "descripcion": descripcion,
                    "monto": abs(monto),
                    "tipo": "gasto",
                    "archivo_referencia": Path(file_path).name,
                    "categoria": "Sin Categoria",
                    "subcategoria": "Sin Subcategoria"
                }
                movements.append(movement)

            except Exception as e:
                continue

        return movements

    def _parse_santander_cc(self, text: str, file_path: str) -> List[Dict]:
        """Parser Santander Tarjeta de Crédito"""
        movements = []
        lines = text.split('\n')

        fecha_pattern = r'(\d{1,2}/\d{1,2}/\d{4})'

        for line in lines:
            line = line.strip()
            
            if not line or len(line) < 20:
                continue
            
            if any(word in line.lower() for word in ['estado de cuenta', 'periodo', 'total operaciones', 'resumen', 'página']):
                continue

            fecha_match = re.search(fecha_pattern, line)
            if not fecha_match:
                continue

            try:
                fecha_str = fecha_match.group(1)
                fecha = self._parse_date(fecha_str, '%d/%m/%Y')
                if not fecha:
                    continue

                fecha_end = fecha_match.end()
                resto = line[fecha_end:].strip()

                # Buscar montos
                montos = re.findall(r'\$\s*(\d+(?:\.\d{3})*(?:,\d{2})?)', resto)
                if not montos:
                    continue

                monto_str = montos[-1]
                monto = self._parse_amount(monto_str)

                if not monto or monto <= 0 or monto > 100000000:
                    continue

                # Descripción
                monto_idx = resto.rfind(f"${monto_str}")
                if monto_idx < 0:
                    monto_idx = resto.rfind(monto_str)
                
                descripcion_raw = resto[:monto_idx].strip() if monto_idx > 0 else resto
                descripcion = self._clean_description(descripcion_raw)

                if not descripcion or len(descripcion) < 3:
                    continue

                movement = {
                    "id": len(movements),
                    "fecha": fecha,
                    "descripcion": descripcion,
                    "monto": abs(monto),
                    "tipo": "gasto",
                    "archivo_referencia": Path(file_path).name,
                    "categoria": "Sin Categoria",
                    "subcategoria": "Sin Subcategoria"
                }
                movements.append(movement)

            except Exception as e:
                continue

        return movements

    def _parse_santander_checking(self, text: str, file_path: str, page=None) -> List[Dict]:
        """Parser Santander Cuenta Corriente"""
        from collections import deque
        movements = []
        lines = text.split('\n')

        # Get column x-positions and amount word positions from page if available
        cargo_x = None
        abono_x = None
        amount_x_queues = {}  # amount_str -> deque of x-center positions (page order)

        if page is not None:
            words = page.extract_words()
            # Find first CARGOS and ABONOS header x-centers from the main table
            for w in words:
                if w['text'].upper() == 'CARGOS' and cargo_x is None:
                    cargo_x = (w['x0'] + w['x1']) / 2
                elif w['text'].upper() == 'ABONOS' and abono_x is None:
                    abono_x = (w['x0'] + w['x1']) / 2

            # Build lookup: amount_str -> deque of x-center positions (in page order)
            # Require at least one .DDD group to match Chilean thousand-separator format
            # and to avoid matching reference/document numbers (e.g. "800020", "0159524825")
            amount_word_re = re.compile(r'^\d+(?:\.\d{3})+$')
            for w in words:
                if amount_word_re.match(w['text']):
                    key = w['text']
                    if key not in amount_x_queues:
                        amount_x_queues[key] = deque()
                    amount_x_queues[key].append((w['x0'] + w['x1']) / 2)

        # Extract year from text (from CARTOLA DESDE/HASTA full dates like "30/10/2025")
        year_match = re.search(r'\d{1,2}/\d{1,2}/(\d{4})', text)
        year = year_match.group(1) if year_match else str(datetime.now().year)

        # Amount pattern: Chilean thousand-separator format (dot-grouped, no $ required)
        # Requiring at least one .DDD group avoids matching bare document/reference numbers
        amount_re = re.compile(r'\b(\d+(?:\.\d{3})+)\b')

        for line in lines:
            line = line.strip()

            if not line or len(line) < 10:
                continue

            if any(word in line.lower() for word in ['estado de cuenta', 'saldo', 'periodo', 'total', 'resumen', 'página']):
                continue

            # Lines must start with DD/MM date (e.g. "05/11Agustinas ...")
            fecha_match = re.match(r'^(\d{1,2}/\d{1,2})', line)
            if not fecha_match:
                continue

            try:
                fecha_dm = fecha_match.group(1)
                parts = fecha_dm.split('/')
                dia = int(parts[0])
                mes = int(parts[1])
                if dia < 1 or dia > 31 or mes < 1 or mes > 12:
                    continue
                fecha = f"{year}-{mes:02d}-{dia:02d}"

                fecha_end = fecha_match.end()
                resto = line[fecha_end:].strip()

                if not resto or len(resto) < 5:
                    continue

                # Find all amounts (numbers with thousand-separator dots)
                montos = amount_re.findall(resto)
                if not montos:
                    continue

                # Determine monto and tipo using column x-positions if available
                monto_str = None
                tipo = "gasto"  # default

                if cargo_x is not None and abono_x is not None:
                    # SALDO column sits further right than ABONOS; use one column-width
                    # beyond ABONOS as the cutoff to exclude running-balance amounts
                    saldo_threshold = abono_x + (abono_x - cargo_x)
                    for m in montos:
                        if m in amount_x_queues and amount_x_queues[m]:
                            x = amount_x_queues[m].popleft()
                            if x <= saldo_threshold:
                                # Amount is in CARGOS or ABONOS column
                                monto_str = m
                                if abs(x - abono_x) < abs(x - cargo_x):
                                    tipo = "ingreso"
                                break
                            # else: x is in SALDO column, consume and continue

                if monto_str is None:
                    monto_str = montos[0]  # fallback: use first amount found

                monto = self._parse_amount(monto_str)

                if not monto or monto <= 0 or monto > 100000000:
                    continue

                # Description: text before the transaction amount
                # Use rfind to handle edge cases where the amount string appears
                # elsewhere in the description text
                monto_idx = resto.rfind(monto_str)
                descripcion_raw = resto[:monto_idx].strip() if monto_idx > 0 else resto
                descripcion = self._clean_description(descripcion_raw)

                if not descripcion or len(descripcion) < 3:
                    continue

                movement = {
                    "id": len(movements),
                    "fecha": fecha,
                    "descripcion": descripcion,
                    "monto": abs(monto),
                    "tipo": tipo,
                    "archivo_referencia": Path(file_path).name,
                    "categoria": "Sin Categoria",
                    "subcategoria": "Sin Subcategoria"
                }
                movements.append(movement)

            except Exception as e:
                continue

        return movements

    def _parse_bice_checking(self, text: str, file_path: str) -> List[Dict]:
        """Parser BICE Cuenta Corriente - Mejorado"""
        movements = []
        lines = text.split('\n')

        # Patrones de BICE: "2 jun 2025" o "30 may 2025"
        fecha_pattern = r'(\d{1,2})\s+([a-z]{3})\s+(\d{4})'
        
        month_map = {
            'ene': 1, 'enero': 1, 'jan': 1,
            'feb': 2, 'febrero': 2,
            'mar': 3, 'marzo': 3,
            'apr': 4, 'abr': 4, 'abril': 4,
            'may': 5, 'mayo': 5,
            'jun': 6, 'junio': 6,
            'jul': 7, 'julio': 7,
            'ago': 8, 'agos': 8, 'agosto': 8, 'aug': 8,
            'sep': 9, 'sept': 9, 'septiembre': 9,
            'oct': 10, 'octubre': 10,
            'nov': 11, 'noviembre': 11,
            'dic': 12, 'diciembre': 12, 'dec': 12
        }

        palabras_descartables = ['saldo', 'resumen', 'periodo', 'total', 'cartola', 'página', 'derechos', 'abonos y cargos']

        for line_idx, line in enumerate(lines):
            line = line.strip()
            
            if not line or len(line) < 20:
                continue
            
            if any(palabra in line.lower() for palabra in palabras_descartables):
                continue

            # Buscar fecha
            fecha_match = re.search(fecha_pattern, line, re.IGNORECASE)
            if not fecha_match:
                continue

            try:
                dia_str, mes_str, ano_str = fecha_match.groups()
                dia = int(dia_str)
                ano = int(ano_str)
                mes = month_map.get(mes_str.lower())

                if not mes or mes < 1 or mes > 12 or dia < 1 or dia > 31:
                    continue

                fecha = f"{ano}-{mes:02d}-{dia:02d}"

                # Extraer resto después de la fecha
                fecha_end = fecha_match.end()
                resto = line[fecha_end:].strip()

                if not resto or len(resto) < 10:
                    continue

                # Buscar montos (formato: $xxx.xxx o $xxx)
                monto_pattern = r'\$\s*(\d+(?:\.\d{3})*(?:,\d{2})?)'
                montos = re.findall(monto_pattern, resto)

                if not montos:
                    continue

                # El último monto es el principal
                monto_str = montos[-1]
                monto = self._parse_amount(monto_str)

                if not monto or monto <= 0 or monto > 500000000:
                    continue

                # Extraer descripción (todo antes del monto)
                monto_idx = resto.rfind(f"${monto_str}")
                if monto_idx < 0:
                    monto_idx = resto.rfind(monto_str)

                if monto_idx > 0:
                    descripcion_raw = resto[:monto_idx].strip()
                else:
                    descripcion_raw = resto

                # Limpiar descripciones muy largas (multi-línea)
                descripcion_raw = re.sub(r'\s+', ' ', descripcion_raw)
                descripcion = self._clean_description(descripcion_raw)

                if not descripcion or len(descripcion) < 3:
                    continue

                # Detectar tipo por palabras clave
                tipo = "ingreso"
                if any(word in descripcion.lower() for word in ['abono', 'deposito', 'liquidacion', 'ingreso']):
                    tipo = "ingreso"
                elif any(word in descripcion.lower() for word in ['cargo', 'transferencia', 'dividendo', 'apertura']):
                    tipo = "gasto"

                movement = {
                    "id": len(movements),
                    "fecha": fecha,
                    "descripcion": descripcion,
                    "monto": abs(monto),
                    "tipo": tipo,
                    "archivo_referencia": Path(file_path).name,
                    "categoria": "Sin Categoria",
                    "subcategoria": "Sin Subcategoria"
                }
                movements.append(movement)

            except Exception as e:
                continue

        return movements

    def _parse_generic(self, text: str, file_path: str) -> List[Dict]:
        """Parser genérico para bancos no identificados"""
        movements = []
        lines = text.split('\n')

        fecha_pattern = r'(\d{1,2}/\d{1,2}/\d{4})'

        for line in lines:
            line = line.strip()
            
            if not line or len(line) < 20:
                continue

            fecha_match = re.search(fecha_pattern, line)
            if not fecha_match:
                continue

            try:
                fecha_str = fecha_match.group(1)
                fecha = self._parse_date(fecha_str, '%d/%m/%Y')
                if not fecha:
                    continue

                fecha_end = fecha_match.end()
                resto = line[fecha_end:].strip()

                # Buscar montos
                montos = re.findall(r'\$\s*(\d+(?:\.\d{3})*(?:,\d{2})?)', resto)
                if not montos:
                    continue

                monto_str = montos[-1]
                monto = self._parse_amount(monto_str)

                if not monto or monto <= 0 or monto > 100000000:
                    continue

                # Descripción
                monto_idx = resto.rfind(f"${monto_str}")
                if monto_idx < 0:
                    monto_idx = resto.rfind(monto_str)
                
                descripcion_raw = resto[:monto_idx].strip() if monto_idx > 0 else resto
                descripcion = self._clean_description(descripcion_raw)

                if not descripcion or len(descripcion) < 3:
                    continue

                movement = {
                    "id": len(movements),
                    "fecha": fecha,
                    "descripcion": descripcion,
                    "monto": abs(monto),
                    "tipo": "gasto",
                    "archivo_referencia": Path(file_path).name,
                    "categoria": "Sin Categoria",
                    "subcategoria": "Sin Subcategoria"
                }
                movements.append(movement)

            except Exception as e:
                continue

        return movements

    def _extract_from_dataframe(self, df, file_path: str, detection: Dict) -> List[Dict]:
        """Extrae movimientos desde DataFrame"""
        if df.empty:
            return []

        movements = []
        df.columns = [str(col).strip() for col in df.columns]
        df.columns = [str(col).lower().strip() for col in df.columns]

        date_col = self._find_column(df, ['fecha', 'date'])
        desc_col = self._find_column(df, ['descripcion', 'description', 'concepto'])
        amount_col = self._find_column(df, ['monto', 'amount', 'valor'])

        if not date_col or not desc_col or not amount_col:
            return []

        for idx, row in df.iterrows():
            try:
                fecha_val = row[date_col]
                desc_val = row[desc_col]
                monto_val = row[amount_col]

                if pd.isna(fecha_val) or pd.isna(desc_val) or pd.isna(monto_val):
                    continue

                fecha = self._parse_date(str(fecha_val))
                if not fecha:
                    continue

                descripcion = self._clean_description(str(desc_val))
                if not descripcion or len(descripcion) < 2:
                    continue

                monto = self._parse_amount(str(monto_val))
                if monto is None or monto <= 0:
                    continue

                movement = {
                    "id": len(movements),
                    "fecha": fecha,
                    "descripcion": descripcion,
                    "monto": abs(monto),
                    "tipo": detection['product_type'],
                    "archivo_referencia": Path(file_path).name,
                    "categoria": "Sin Categoria",
                    "subcategoria": "Sin Subcategoria"
                }
                movements.append(movement)

            except Exception as e:
                continue

        return movements

    def _parse_date(self, date_str: str, date_format: str = None) -> str:
        """Parsea fecha con múltiples formatos"""
        if not date_str or date_str.lower() == 'nan':
            return None

        date_str = str(date_str).strip()

        formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y', '%Y-%m-%d',
            '%d %b %Y', '%d %B %Y', '%d %m %Y', '%Y/%m/%d'
        ]

        if date_format:
            formats.insert(0, date_format)

        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue

        return None

    def _parse_amount(self, amount_str: str) -> float:
        """Parsea monto en diferentes formatos"""
        if not amount_str or amount_str.lower() == 'nan':
            return None

        amount_str = str(amount_str).strip().replace(' ', '')

        if not amount_str:
            return None

        is_negative = amount_str.startswith('-')
        if is_negative:
            amount_str = amount_str[1:]

        # Manejo de miles con punto y decimales con coma (1.234,56)
        if amount_str.count('.') >= 2:
            amount_str = amount_str.replace('.', '').replace(',', '.')
        elif ',' in amount_str and '.' in amount_str:
            if amount_str.rfind(',') > amount_str.rfind('.'):
                amount_str = amount_str.replace('.', '').replace(',', '.')
            else:
                amount_str = amount_str.replace(',', '')
        elif '.' in amount_str:
            parts = amount_str.split('.')
            if len(parts[-1]) == 3:
                amount_str = amount_str.replace('.', '')
        elif ',' in amount_str:
            amount_str = amount_str.replace(',', '.')

        try:
            result = float(amount_str)
            if is_negative:
                result = -result
            return result
        except ValueError:
            return None

    def _clean_description(self, desc: str) -> str:
        """Limpia descripción"""
        desc = str(desc).strip()

        # Remover patrones no deseados
        desc = re.sub(r'\d{1,2}/\d{1,2}\s+\w+-\d{4}', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'\s*RUT\s+[\d\-\.]+.*', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'\s+\d{7,}\s*', ' ', desc)
        desc = re.sub(r'\b\d{1,2}/\d{1,2}/\s*$', '', desc)
        desc = re.sub(r'\b\d{1,2}/\d{1,2}[\s|]*$', '', desc)
        desc = re.sub(r'\s+', ' ', desc).strip()

        if len(desc) > 100:
            desc = desc[:97] + "..."

        return desc.strip()

    def _find_column(self, df, possible_names):
        """Busca columna en DataFrame"""
        df_cols = {str(col).lower().strip(): col for col in df.columns}

        for name in possible_names:
            normalized = name.lower().strip()
            if normalized in df_cols:
                return df_cols[normalized]

        for name in possible_names:
            normalized = name.lower().strip()
            for col_normalized, col_original in df_cols.items():
                if normalized in col_normalized:
                    return col_original

        return None