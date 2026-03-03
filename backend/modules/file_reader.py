"""
Módulo universal para leer archivos Excel y PDF
Detecta automáticamente: Banco, Tipo de Producto
Soporta: BICE CC, CMR TC, Santander CC, Santander TC
"""

import pandas as pd
import pdfplumber
import camelot
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

    def read_pdf(self, file_path: str) -> List[Dict]:
        """Lee un archivo PDF detectando automáticamente el contenido"""
        try:
            filename = Path(file_path).name.lower()
            print(f"\n📄 Procesando PDF: {filename}")

            with pdfplumber.open(file_path) as pdf:
                print(f"   Total de páginas: {len(pdf.pages)}")

                 # Detectar banco y tipo desde primeras páginas
                detection = self._detect_from_pdf(pdf)
                print(f"   Banco: {detection['bank']} | Tipo: {detection['product_type']}")

                # ✅ ESPECIAL PARA BICE: Usar tabla directamente
                if detection['bank'] == 'BICE' and detection['product_type'] == 'CUENTA_CORRIENTE':
                    print(f"   Procesando página 1...")
                    movements = self._parse_bice_checking_from_pdf(file_path)
                    print(f"   Total movimientos extraídos: {len(movements)}")
                    return movements
                
                # ✅ SANTANDER CUENTA CORRIENTE: Usar Camelot
                if detection['bank'] == 'SANTANDER' and detection['product_type'] == 'CUENTA_CORRIENTE':
                    print(f"   Procesando página 1...")
                    movements = self._parse_santander_with_camelot(file_path)
                    print(f"   Total movimientos extraídos: {len(movements)}")
                    return movements
                
                # ✅ SANTANDER TARJETA DE CRÉDITO
                if detection['bank'] == 'SANTANDER' and detection['product_type'] == 'TARJETA_CREDITO':
                    print(f"   Procesando TODAS las páginas...")
                    # Extraer texto de TODAS las páginas
                    text_all_pages = ""
                    for page_num, page in enumerate(pdf.pages, 1):
                        page_text = page.extract_text()
                        if page_text:
                            text_all_pages += page_text + "\n"
                    
                    movements = self._parse_santander_tarjeta_credito(text_all_pages, file_path)
                    print(f"   Total movimientos extraídos: {len(movements)}")
                    return movements
                
                # Para otros bancos: procesamiento tradicional
                movements = []
                for page_num, page in enumerate(pdf.pages, 1):
                    print(f"   Procesando página {page_num}...")
                    
                    page_movements = []
                    
                    # OTROS BANCOS: Usar texto
                    text = page.extract_text()
                    if not text:
                        continue
                    page_movements = self._extract_movements_from_text(
                        text, 
                        file_path, 
                        detection['bank'],
                        detection['product_type'],
                        page
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
        
        print("DEBUG: Antes de _detect_bank():")
        print(f"  - 'pantoja' en texto: {'pantoja' in full_text}")
        print(f"  - 'cuenta corriente' en texto: {'cuenta corriente' in full_text}")
        print(f"  - 'cmr' en texto: {'cmr' in full_text}")
        
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
        """Detecta el banco desde el texto - BICE PRIMERO"""
        
        text_lower = text.lower()
        
        # ✅ PASO 1: BUSCAR "BANCO BICE" PRIMERO (MÁS ESPECÍFICO)
        if 'banco bice' in text_lower or 'banco = bice' in text_lower:
            print(f"🏦 Institución detectada: bice (confianza: 1.0) [por 'BANCO BICE']")
            return "BICE"
        
        # ✅ PASO 1b: Buscar número de cuenta BICE (21-XXXXX-X)
        if re.search(r'\b21-\d{5}-\d\b', text_lower):
            print(f"🏦 Institución detectada: bice (confianza: 1.0) [por número de cuenta]")
            return "BICE"
        
        # ✅ PASO 1c: Buscar "Cuenta en pesos" (BICE específico)
        if 'cuenta en pesos n°' in text_lower or 'cuenta en pesos' in text_lower:
            print(f"🏦 Institución detectada: bice (confianza: 1.0) [por 'Cuenta en pesos']")
            return "BICE"
        
        # ✅ PASO 2: CMR (número de tarjeta específico)
        if re.search(r'\b4517\s*9123\s*\d{4}\s*\d{4}\b', text_lower):
            print(f"🏦 Institución detectada: cmr (confianza: 1.0) [por número de tarjeta]")
            return "CMR"
        
        # ✅ PASO 3: SANTANDER (después de descartar BICE)
        # Si tiene "pantoja" + "cuenta corriente" + NO es BICE = SANTANDER
        if ('pantoja' in text_lower) and ('cuenta corriente' in text_lower):
            score = text_lower.count('pantoja') + text_lower.count('cuenta corriente')
            print(f"🏦 Institución detectada: santander (confianza: {min(score, 10)}/10) [por pantoja + cuenta corriente]")
            return "SANTANDER"
        
        # Si tiene "banco santander" o "santander chile"
        if 'banco santander' in text_lower or 'santander chile' in text_lower:
            score = text_lower.count('banco santander') + text_lower.count('santander chile')
            print(f"🏦 Institución detectada: santander (confianza: {min(score, 10)}/10)")
            return "SANTANDER"
        
        # ✅ PASO 4: Otros bancos
        patterns = {
            'bice': ['bice'],
            'cmr': ['cmr', 'falabella', 'tarjeta cmr'],
            'itau': ['itau', 'itaú', 'banco itau'],
            'bbva': ['bbva', 'banco bbva'],
            'scotiabank': ['scotia', 'scotiabank'],
        }
        
        bank_scores = {}
        
        for bank, keywords in patterns.items():
            count = sum(text_lower.count(keyword) for keyword in keywords)
            bank_scores[bank] = count
        
        best_bank = max(bank_scores, key=bank_scores.get)
        
        if bank_scores[best_bank] > 0:
            print(f"🏦 Institución detectada: {best_bank.lower()} (confianza: {bank_scores[best_bank]}/10)")
            return best_bank.upper()
        
        return "DESCONOCIDO"
    
    def _detect_product_type(self, text: str, bank: str) -> str:
        """Detecta tipo de producto (Cuenta Corriente o Tarjeta Crédito)"""

        # CMR es SIEMPRE tarjeta de crédito
        if bank == 'CMR':
            return 'TARJETA_CREDITO'

        # ✅ PASO 0: BUSCAR ENCABEZADO ESPECÍFICO DE TDC SANTANDER
        if 'estado de cuenta en moneda nacional de tarjeta de credito' in text.lower():
            print(f"      ✅ Detectado: TARJETA_CREDITO (por encabezado específico)")
            return 'TARJETA_CREDITO'

        # Palabras clave para tarjeta de crédito
        credit_card_keywords = [
            'tarjeta de credito', 'tarjeta crédito', 'tdc',
            'compras nacionales', 'comercios', 'limite de credito',
            'pago minimo', 'fecha vencimiento', 'movimientos tarjeta',
            'extracto tarjeta', 'estado tarjeta', 'cupo total', 'cupo utilizado'
        ]

        # Palabras clave para cuenta corriente (PRIMERO - PRIORITARIO)
        checking_keywords = [
            'cuenta corriente ml',  # ← MÁS ESPECÍFICO, PRIMERO
            'cuenta corriente',
            'cuenta en pesos',
            'movimientos cuenta',
            'saldo inicial', 'saldo final',
            'transferencia', 'deposito',
            'giro', 'cheque', 'sobregiro', 'disponible',
            'detalle de movimientos'  # ← Encabezado de tabla Santander
        ]

        # ✅ PRIMERO: Buscar palabras muy específicas de cuenta corriente
        if 'cuenta corriente ml' in text.lower():
            print(f"      ✅ Detectado: CUENTA_CORRIENTE (por 'cuenta corriente ml')")
            return 'CUENTA_CORRIENTE'
        
        if 'detalle de movimientos' in text.lower():
            print(f"      ✅ Detectado: CUENTA_CORRIENTE (por 'detalle de movimientos')")
            return 'CUENTA_CORRIENTE'

        cc_count = sum(text.count(keyword) for keyword in credit_card_keywords)
        checking_count = sum(text.count(keyword) for keyword in checking_keywords)

        print(f"      DEBUG: CC count={cc_count}, Checking count={checking_count}")

        if cc_count > checking_count:
            print(f"      ✅ Detectado: TARJETA_CREDITO")
            return 'TARJETA_CREDITO'
        else:
            print(f"      ✅ Detectado: CUENTA_CORRIENTE")
            return 'CUENTA_CORRIENTE'
        
    def _extract_movements_from_text(self, text: str, file_path: str, bank: str, product_type: str, page) -> List[Dict]:
            """Extrae movimientos del texto de PDF para bancos que no tienen tabla estructurada"""
            movements = []
            
            if not text:
                return []
            
            try:
                # Para CMR Tarjeta de Crédito
                if bank.upper() == 'CMR' and product_type == 'TARJETA_CREDITO':
                    movements = self._parse_cmr_cc(text, file_path)
                
                # Para SANTANDER Tarjeta de Crédito
                elif bank.upper() == 'SANTANDER' and product_type == 'TARJETA_CREDITO':
                    movements = self._parse_cmr_cc(text, file_path)  # Usa el mismo parser
                
                # Para otros bancos genéricos
                else:
                    movements = self._parse_generic(text, file_path)
                
                return movements
                
            except Exception as e:
                print(f"      ❌ Error extrayendo movimientos: {e}")
                return []
            
    def _parse_santander_tarjeta_credito(self, text: str, file_path: str) -> List[Dict]:
        """Parser para Santander Tarjeta de Crédito - Procesa TODAS las páginas"""
        movements = []
        
        # Extraer fecha de estado de cuenta
        fecha_estado_pattern = r'FECHA ESTADO DE CUENTA\s+(\d{2})/(\d{2})/(\d{4})'
        fecha_estado_match = re.search(fecha_estado_pattern, text)
        
        if fecha_estado_match:
            estado_day, estado_month_str, estado_year_str = fecha_estado_match.groups()
            estado_month = int(estado_month_str)
            estado_year = int(estado_year_str)
            month_name = self._get_month_name(estado_month)
            print(f"   📅 Fecha de estado: {month_name} {estado_year}")
        else:
            from datetime import datetime
            now = datetime.now()
            estado_year = now.year
            estado_month = now.month
            month_name = self._get_month_name(estado_month)
            print(f"   ⚠️ No se encontró fecha de estado, usando: {month_name} {estado_year}")
        
        # Dividir por secciones de "PERÍODO ACTUAL" (puede haber múltiples)
        # Las páginas 2+ también tienen "2.PERÍODO ACTUAL"
        
        lines = text.split('\n')
        
        # Patrón para detectar líneas de movimiento
        fecha_pattern = r'(\d{2})/(\d{2})/(\d{2})'  # DD/MM/YY
        
        exclude_keywords = [
            'total operaciones', 'movimientos tarjeta', 'productos o servicios',
            'cargos, comisiones', 'período anterior', 'período actual',
            'lugar de operación', 'fecha de operación', 'descripción operación',
            'nºcuota', 'valor cuota', 'monto origen', 'monto total',
            'operación pagar', 'cargo del mes', 'mensual', 'o cobro',
            'información general', 'detalle', 'pagar hasta', 'monto mínimo',
            'comprobante de pago', 'emisor', 'cliente', 'cheque', 'efectivo',
            'nombre', 'número de tarjeta', 'timbre', 'banco',
            'información compras en cuotas', 'de 3'
        ]
        
        print(f"   🔍 Buscando movimientos en {len(lines)} líneas...")
        
        i = 0
        in_movimientos_section = False
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Detectar inicio de sección de movimientos
            if 'PERÍODO ACTUAL' in line.upper() or 'TOTAL OPERACIONES' in line:
                in_movimientos_section = True
                print(f"   ➜ Sección de movimientos en línea {i}")
                i += 1
                continue
            
            # Saltar líneas vacías
            if not line or len(line) < 5:
                i += 1
                continue
            
            # Detectar fin de sección (cuando encontramos otra sección o fin de documento)
            if in_movimientos_section and any(keyword in line.lower() for keyword in ['emisor', 'comprobante de pago', 'cheque', 'efectivo', 'nombre', 'número de tarjeta', 'información compras']):
                if 'INFORMACIÓN COMPRAS' not in line.upper():  # No contar este
                    print(f"   ⏹️  Fin de sección en línea {i}")
                    in_movimientos_section = False
                i += 1
                continue
            
            # Si NO estamos en sección de movimientos, saltar
            if not in_movimientos_section:
                i += 1
                continue
            
            # Saltar líneas con palabras clave de exclusión
            if any(keyword in line.lower() for keyword in exclude_keywords):
                i += 1
                continue
            
            # Buscar fecha en formato DD/MM/YY
            fecha_match = re.search(fecha_pattern, line)
            if not fecha_match:
                i += 1
                continue
            
            try:
                # Extraer fecha
                day_str, month_str, year_short = fecha_match.groups()
                day = int(day_str)
                month = int(month_str)
                
                # Inferir año completo basado en mes
                mov_month = int(month_str)
                
                if mov_month > estado_month:
                    # El movimiento es del año anterior
                    year_full = estado_year - 1
                else:
                    # Mismo año que el estado de cuenta
                    year_full = estado_year
                
                fecha_str = f"{day:02d}/{mov_month:02d}/{year_full}"
                fecha = self._parse_date(fecha_str, '%d/%m/%Y')
                if not fecha:
                    i += 1
                    continue
                
                # Extraer descripción y monto
                fecha_end = fecha_match.end()
                resto = line[fecha_end:].strip()
                
                if not resto or len(resto) < 2:
                    i += 1
                    continue
                
                # Buscar monto (formato: $118.931 o $ -5.602 o $-3.000.000 o $29,745)
                monto_pattern = r'\$\s*(-?\d+(?:\.\d{3})*(?:,\d{2})?)\s*$'
                monto_match = re.search(monto_pattern, resto)
                
                if not monto_match:
                    i += 1
                    continue
                
                monto_str = monto_match.group(1)
                monto = self._parse_amount(monto_str)
                
                if not monto or monto == 0 or abs(monto) > 100000000:
                    i += 1
                    continue
                
                # Extraer descripción (todo antes del monto)
                monto_start = monto_match.start()
                descripcion_raw = resto[:monto_start].strip()
                
                # Limpiar descripción
                descripcion = self._clean_description(descripcion_raw)
                descripcion = self._clean_santander_tdc_description(descripcion)
                
                if not descripcion or len(descripcion) < 2:
                    i += 1
                    continue
                
                # Validar que tenga al menos una letra
                if not any(char.isalpha() for char in descripcion):
                    i += 1
                    continue
                
                # Determinar tipo (negativo = ingreso/abono, positivo = gasto/cargo)
                if monto < 0:
                    tipo = "ingreso"
                    monto_abs = abs(monto)
                else:
                    tipo = "gasto"
                    monto_abs = monto
                
                # Evitar duplicados
                existe = any(
                    m['fecha'] == fecha and 
                    m['monto'] == monto_abs and 
                    m['descripcion'].lower() == descripcion.lower()
                    for m in movements
                )
                if existe:
                    print(f"   ⏭️  DUPLICADO: {fecha} | {descripcion[:40]}")
                    i += 1
                    continue
                
                movement = {
                    "id": len(movements),
                    "fecha": fecha,
                    "descripcion": descripcion,
                    "monto": monto_abs,
                    "tipo": tipo,
                    "archivo_referencia": Path(file_path).name,
                    "categoria": "Sin Categoria",
                    "subcategoria": "Sin Subcategoria"
                }
                movements.append(movement)
                print(f"   ✅ [{len(movements):2d}] {fecha} | {tipo:7} | {descripcion[:50]:50} | ${monto_abs:>12,.0f}")
            
            except Exception as e:
                print(f"   ⚠️  Error línea {i}: {str(e)[:60]}")
            
            i += 1
        
        print(f"   Total movimientos extraídos: {len(movements)}")
        return movements
    
    def _clean_santander_tdc_description(self, desc: str) -> str:
        """Limpia descripción de Santander TDC"""
        
        # Remover "COMPRAS P.A.T." al final
        desc = re.sub(r'\s+COMPRAS\s+P\.A\.T\.\s*$', '', desc, flags=re.IGNORECASE)
        
        # Remover códigos al final (como "T", "A", "I")
        desc = re.sub(r'\s+[TAI]\s*$', '', desc)
        
        # Normalizar espacios
        desc = re.sub(r'\s+', ' ', desc).strip()
        
        return desc
                
    def _parse_cmr_cc(self, text: str, file_path: str) -> List[Dict]:
        """MEJORADO V9: Parser CMR - Permite movimientos duplicados (son reales)"""
        movements = []
        lines = text.split('\n')

        fecha_pattern = r'(\d{1,2}/\d{1,2}/\d{4})'
        
        exclude_keywords = [
            'compras nacionales', 'sin movimientos', 'cupo total', 'cupo compra',
            'cupo avance', 'tasa interes', 'periodo anterior', 'periodo actual',
            'saldo adeudado', 'informacion general', 'detalle',
            'encabezado', 'titulo', 'estado de cuenta', 'cliente elite',
            'resumen de pago', 'monto total', 'total pesos', 'total dolares',
            'fecha pactada', 'encabezado', 'paga hasta', 'cupon de pago',
            'iii detalle', 'ii informacion', 'i resumén', 'tasas', 'conceptos',
            'pago minimo', 'credito disponible', 'limite', 'financiamiento',
            'iv. costo', 'información de pago', 'vencimiento próximos',
            'monto interés', 'gasto de cobranza'
        ]

        for line in lines:
            line = line.strip()
            
            if not line or len(line) < 15:
                continue
            
            if any(keyword in line.lower() for keyword in exclude_keywords):
                continue
            
            # Filtro: Si la línea tiene MUCHAS fechas (>2), es basura
            fecha_count = len(re.findall(fecha_pattern, line))
            if fecha_count > 2:
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

                if not resto or len(resto) < 3:
                    continue

                # NUEVO: Detección especial para "Pago tarjeta cmr T"
                if 'pago tarjeta' in resto.lower():
                    pago_pattern = r'-\s*(\d+(?:\.\d{3})*(?:,\d{2})?)'
                    pago_match = re.search(pago_pattern, resto)
                    
                    if pago_match:
                        monto_str = pago_match.group(1)
                        monto = self._parse_amount(monto_str)
                        is_negative = True
                        monto_idx = resto.find('-')
                        descripcion_raw = resto[:monto_idx].strip()
                    else:
                        continue
                else:
                    # PARSER GENERAL para otros movimientos
                    monto_pattern = r'-?\s*\$?\s*(\d+(?:\.\d{3})*(?:,\d{2})?)'
                    montos_matches = list(re.finditer(monto_pattern, resto))
                    
                    if not montos_matches:
                        continue

                    # Usar el ÚLTIMO monto (más flexible)
                    monto_full = None
                    monto_str = None
                    monto = None
                    is_negative = False
                    
                    # Buscar el ÚLTIMO monto que sea >= 1
                    for match in reversed(montos_matches):
                        candidate = match.group(1)
                        candidate_monto = self._parse_amount(candidate)
                        
                        # Más flexible: acepta cualquier monto >= 1
                        if candidate_monto and candidate_monto >= 1 and candidate_monto < 100000000:
                            monto_str = candidate
                            monto = candidate_monto
                            monto_full = match.group(0)
                            is_negative = '-' in monto_full
                            break
                    
                    if not monto:
                        continue
                    
                    monto_idx = resto.rfind(monto_full)
                    if monto_idx > 0:
                        descripcion_raw = resto[:monto_idx].strip()
                    else:
                        descripcion_raw = resto

                # Validar monto
                if not monto or monto <= 0 or monto > 100000000:
                    continue

                # Limpiar descripción
                descripcion = self._clean_description(descripcion_raw)
                descripcion = self._clean_cmr_description(descripcion, monto)  # ✅ Agregar esta línea
                
                # VALIDACIONES DE DESCRIPCIÓN
                if not descripcion or len(descripcion.strip()) < 2:
                    continue
                
                # Aceptar descripciones que tengan al menos una palabra (con letras)
                if not any(char.isalpha() for char in descripcion):
                    continue
                
                # ✅ REMOVÍ EL FILTRO DE DUPLICADOS
                # Los movimientos iguales (misma fecha/descripción/monto) son reales
                # y deben capturarse todos

                # Determinar tipo
                if is_negative:
                    tipo = "ingreso"
                else:
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
    
    def _clean_cmr_description(self, desc: str, monto_real: float) -> str:
        """
        Limpia descripción CMR - Segunda pasada, elimina montos específicos
        """
        
        # ✅ ELIMINAR MONTOS DUPLICADOS (la segunda copia del monto)
        # Si el monto aparece al final de la descripción, eliminarlo
        monto_str = f"{monto_real:,.0f}".replace(',', '.')
        
        # Busca el monto al final (puede estar una o dos veces)
        desc = re.sub(rf'\s+{re.escape(monto_str)}\s+{re.escape(monto_str)}\s*$', '', desc)
        desc = re.sub(rf'\s+{re.escape(monto_str)}\s*$', '', desc)
        
        # ✅ LIMPIAR ESPACIOS FINALES
        desc = re.sub(r'\s+', ' ', desc).strip()
        
        return desc
        
    def _parse_santander_with_camelot(self, file_path: str) -> List[Dict]:
        """Extrae tabla Santander con Camelot"""
        import camelot

        movements = []

        try:
            tables = camelot.read_pdf(file_path, pages='1', flavor='stream')

            if not tables:
                return []

            df = tables[0].df

            # Extraer año y mes de HASTA (período de corte)
            year_hasta, month_name = self._extract_year_from_santander_pdf(file_path)
            print(f"   📅 Período de corte: {month_name} {year_hasta}")

            # Procesar filas (saltar encabezados: filas 0, 1, 2)
            for idx, row in df.iterrows():
                if idx < 3:
                    continue

                # Detener si encuentras "Resumen de Comisiones"
                descripcion_check = str(row[1]).strip().lower()
                if 'resumen' in descripcion_check and 'comisiones' in descripcion_check:
                    print(f"   ⚠️ Fin de movimientos en fila {idx}")
                    break

                try:
                    fecha_str = str(row[0]).strip()

                    if not fecha_str or '/' not in fecha_str:
                        continue

                    fecha_match = re.match(r'(\d{2})/(\d{2})', fecha_str)
                    if not fecha_match:
                        continue

                    # Extraer día y mes del movimiento
                    day = fecha_match.group(1)
                    month = fecha_match.group(2)
                    
                    # Determinar el año:
                    # Si el mes del movimiento es <= mes de corte, usa year_hasta
                    # Si es > mes de corte, es del año anterior
                    month_int = int(month)
                    month_hasta_int = int(self._get_month_number(month_name))
                    
                    if month_int <= month_hasta_int:
                        year = year_hasta
                    else:
                        year = str(int(year_hasta) - 1)
                    
                    fecha = self._parse_date(f"{day}/{month}/{year}", '%d/%m/%Y')
                    if not fecha:
                        continue

                    # Descripción
                    descripcion = str(row[1]).strip()
                    if not descripcion or len(descripcion) < 2:
                        continue

                    # Cargo y Abono
                    cargo_str = str(row[3]).strip()
                    abono_str = str(row[4]).strip()

                    monto_val = None
                    tipo = None

                    # CARGO = GASTO
                    if cargo_str and cargo_str.lower() != 'nan':
                        try:
                            monto_val = float(cargo_str.replace('.', '').replace(',', '.'))
                            tipo = "gasto"
                        except:
                            pass

                    # ABONO = INGRESO
                    if abono_str and abono_str.lower() != 'nan':
                        try:
                            monto_val = float(abono_str.replace('.', '').replace(',', '.'))
                            tipo = "ingreso"
                        except:
                            pass

                    if not monto_val or monto_val <= 0 or monto_val > 100000000:
                        continue

                    if not tipo:
                        continue

                    movement = {
                        "id": len(movements),
                        "fecha": fecha,
                        "descripcion": descripcion,
                        "monto": monto_val,
                        "tipo": tipo,
                        "archivo_referencia": Path(file_path).name,
                        "categoria": "Sin Categoria",
                        "subcategoria": "Sin Subcategoria"
                    }
                    movements.append(movement)

                except Exception as e:
                    continue

            print(f"   Total movimientos extraídos: {len(movements)}")
            return movements

        except Exception as e:
            print(f"   ❌ Error Camelot: {e}")
            return []
        
    def _extract_year_from_santander_pdf(self, file_path: str) -> Tuple[str, str]:
        """Extrae año y mes de la sección CARTOLA DESDE en PDFs de Santander"""
        import pdfplumber
        
        try:
            with pdfplumber.open(file_path) as pdf:
                text = pdf.pages[0].extract_text()
                text_lower = text.lower()
                
                print(f"      DEBUG: Buscando patrón CARTOLA...")
                
                # ✅ NUEVO: Buscar línea que tenga "CARTOLA DESDE HASTA"
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if 'cartola' in line.lower() and 'desde' in line.lower() and 'hasta' in line.lower():
                        print(f"      Línea CARTOLA: {line}")
                        
                        # La siguiente línea o esta misma tiene las fechas
                        # Buscar patrón: número FECHA1 FECHA2 número
                        for check_line in [line, lines[i+1] if i+1 < len(lines) else ""]:
                            # Buscar dos fechas consecutivas DD/MM/YYYY
                            matches = re.findall(r'(\d{2})/(\d{2})/(\d{4})', check_line)
                            print(f"      Fechas en línea: {matches}")
                            
                            if len(matches) >= 2:
                                # Primera fecha = DESDE, Segunda = HASTA
                                day_desde, month_desde, year_desde = matches[0]
                                day_hasta, month_hasta, year_hasta = matches[1]
                                
                                print(f"      DESDE: {day_desde}/{month_desde}/{year_desde}")
                                print(f"      HASTA: {day_hasta}/{month_hasta}/{year_hasta}")
                                
                                month_name = self._get_month_name(int(month_hasta))
                                print(f"      ✅ Período: {month_name} {year_hasta}")
                                return year_hasta, month_name
                
                print(f"      ❌ No encontró patrón CARTOLA, intentando alternativo...")
                
                # Fallback: buscar PRIMERA pareja de fechas (no la última)
                all_matches = re.findall(r'(\d{2})/(\d{2})/(\d{4})', text_lower)
                print(f"      Todas las fechas: {all_matches}")
                
                if len(all_matches) >= 2:
                    # Usar la segunda fecha como "HASTA" (primer par probablemente sea DESDE/HASTA)
                    day, month, year = all_matches[1]
                    month_name = self._get_month_name(int(month))
                    print(f"      ✅ Usando segunda fecha: {month_name} {year}")
                    return year, month_name
                
                from datetime import datetime
                now = datetime.now()
                year = str(now.year)
                month_name = self._get_month_name(now.month)
                print(f"      ⚠️ Sin fechas, usando actual: {month_name} {year}")
                return year, month_name
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
            from datetime import datetime
            now = datetime.now()
            return str(now.year), self._get_month_name(now.month)

    def _get_month_name(self, month_num: int) -> str:
        """Convierte número de mes a nombre en español"""
        months = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        return months.get(month_num, 'Desconocido')
    
    def _get_month_number(self, month_name: str) -> str:
        """Convierte nombre de mes a número (01-12)"""
        months = {
            'Enero': '01', 'Febrero': '02', 'Marzo': '03', 'Abril': '04',
            'Mayo': '05', 'Junio': '06', 'Julio': '07', 'Agosto': '08',
            'Septiembre': '09', 'Octubre': '10', 'Noviembre': '11', 'Diciembre': '12'
        }
        return months.get(month_name, '01')
            
    def _parse_bice_checking(self, text: str, file_path: str) -> List[Dict]:
        """Parser BICE Cuenta Corriente - Usa tabla en lugar de texto"""
        movements = []
        
        # Intentar extraer como tabla primero
        try:
            # Si el texto viene de una tabla, procesarlo como tal
            # Si no, usar el método de texto
            movements = self._parse_bice_from_table(file_path)
            if movements:
                return movements
        except:
            pass
        
        # Fallback a parsing de texto
        return self._parse_bice_from_text(text, file_path)

    def _parse_bice_from_table(self, file_path: str) -> List[Dict]:
        """Extrae movimientos de la tabla BICE usando pdfplumber"""
        movements = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    
                    if not tables:
                        continue
                    
                    for table in tables:
                        for row_idx, row in enumerate(table):
                            if not row or len(row) < 4:
                                continue
                            
                            # Saltar encabezados
                            if row_idx == 0 or any('fecha' in str(cell).lower() for cell in row):
                                continue
                            
                            # Estructura BICE: [Fecha, Categoría, N° operación, Descripción, Monto]
                            fecha_str = (row[0] or '').strip()
                            categoria = (row[1] or '').strip()
                            nro_operacion = (row[2] or '').strip()
                            descripcion_raw = (row[3] or '').strip()
                            monto_str = (row[4] or '').strip() if len(row) > 4 else ''
                            
                            # Parsear fecha
                            fecha_match = re.search(r'(\d{1,2})\s+([a-z]{3})\s+(\d{4})', fecha_str, re.IGNORECASE)
                            if not fecha_match:
                                continue
                            
                            month_map = {
                                'ene': 1, 'enero': 1, 'jan': 1, 'feb': 2, 'febrero': 2,
                                'mar': 3, 'marzo': 3, 'apr': 4, 'abr': 4, 'abril': 4,
                                'may': 5, 'mayo': 5, 'jun': 6, 'junio': 6, 'jul': 7,
                                'julio': 7, 'ago': 8, 'agos': 8, 'agosto': 8, 'aug': 8,
                                'sep': 9, 'sept': 9, 'septiembre': 9, 'oct': 10, 'octubre': 10,
                                'nov': 11, 'noviembre': 11, 'dic': 12, 'diciembre': 12, 'dec': 12
                            }
                            
                            dia_str, mes_str, ano_str = fecha_match.groups()
                            dia = int(dia_str)
                            ano = int(ano_str)
                            mes = month_map.get(mes_str.lower())
                            
                            if not mes or mes < 1 or mes > 12 or dia < 1 or dia > 31:
                                continue
                            
                            fecha = f"{ano}-{mes:02d}-{dia:02d}"
                            
                            # Parsear monto
                            monto_match = re.search(r'\$\s*([\d\.,]+)', monto_str)
                            if not monto_match:
                                continue
                            
                            monto = self._parse_amount(monto_match.group(1))
                            if not monto or monto <= 0 or monto > 500000000:
                                continue
                            
                            # Limpiar descripción
                            descripcion = self._clean_description(descripcion_raw)
                            descripcion = self._improve_bice_description(descripcion)
                            
                            if not descripcion or len(descripcion) < 3:
                                continue
                            
                            if not any(char.isalpha() for char in descripcion):
                                continue
                            
                            # Detectar tipo
                            desc_lower = descripcion.lower()
                            if any(word in desc_lower for word in ['abono', 'deposito', 'liquidacion', 'ingreso']):
                                tipo = "ingreso"
                            else:
                                tipo = "gasto"
                            
                            # Evitar duplicados
                            existe = any(
                                m['fecha'] == fecha and 
                                m['monto'] == monto and 
                                m['descripcion'].lower() == descripcion.lower()
                                for m in movements
                            )
                            if existe:
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
            print(f"   ⚠️ Error extrayendo tabla BICE: {e}")
            return []
        
        return movements

    def _parse_bice_from_text(self, text: str, file_path: str) -> List[Dict]:
        """Fallback: Parsear desde texto si la tabla no funciona"""
        movements = []
        lines = text.split('\n')
        
        fecha_pattern = r'(\d{1,2})\s+([a-z]{3})\s+(\d{4})'
        month_map = {
            'ene': 1, 'enero': 1, 'jan': 1, 'feb': 2, 'febrero': 2,
            'mar': 3, 'marzo': 3, 'apr': 4, 'abr': 4, 'abril': 4,
            'may': 5, 'mayo': 5, 'jun': 6, 'junio': 6, 'jul': 7,
            'julio': 7, 'ago': 8, 'agos': 8, 'agosto': 8, 'aug': 8,
            'sep': 9, 'sept': 9, 'septiembre': 9, 'oct': 10, 'octubre': 10,
            'nov': 11, 'noviembre': 11, 'dic': 12, 'diciembre': 12, 'dec': 12
        }
        
        palabras_descartables = ['saldo', 'resumen', 'periodo', 'total', 'cartola', 'página', 'derechos', 'abonos y cargos', 'fecha', 'categoría', 'descripción', 'monto']
        
        for line in lines:
            line = line.strip()
            
            if not line or len(line) < 20:
                continue
            
            if any(palabra in line.lower() for palabra in palabras_descartables):
                continue
            
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
                
                fecha_end = fecha_match.end()
                resto = line[fecha_end:].strip()
                
                if not resto or len(resto) < 10:
                    continue
                
                monto_pattern = r'\$\s*([\d\.,]+)\s*$'
                monto_match = re.search(monto_pattern, resto)
                
                if not monto_match:
                    continue
                
                monto_str = monto_match.group(1)
                monto = self._parse_amount(monto_str)
                
                if not monto or monto <= 0 or monto > 500000000:
                    continue
                
                monto_start = monto_match.start()
                descripcion_raw = resto[:monto_start].strip()
                
                partes = descripcion_raw.split('|')
                if len(partes) >= 3:
                    descripcion_raw = '|'.join(partes[2:]).strip()
                elif len(partes) >= 2:
                    descripcion_raw = partes[-1].strip()
                
                descripcion = self._clean_description(descripcion_raw)
                descripcion = self._improve_bice_description(descripcion)
                
                if not descripcion or len(descripcion) < 3:
                    continue
                
                if not any(char.isalpha() for char in descripcion):
                    continue
                
                desc_lower = descripcion.lower()
                if any(word in desc_lower for word in ['abono', 'deposito', 'liquidacion', 'ingreso']):
                    tipo = "ingreso"
                else:
                    tipo = "gasto"
                
                existe = any(
                    m['fecha'] == fecha and 
                    m['monto'] == monto and 
                    m['descripcion'].lower() == descripcion.lower()
                    for m in movements
                )
                if existe:
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

    def _rejoin_split_lines(self, lines: list) -> list:
        """Rejunta líneas que fueron divididas por el extractor de PDF"""
        rejoined = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Si la línea es muy corta o no empieza con fecha/categoría, puede ser continuación
            if i < len(lines) - 1 and line and len(line) < 50:
                next_line = lines[i + 1].strip()
                
                # Si la siguiente línea también es corta y no tiene fecha, probablemente es continuación
                if next_line and not re.match(r'^\d{1,2}\s+[a-z]{3}', next_line.lower()):
                    line = line + " " + next_line
                    i += 2
                    rejoined.append(line)
                    continue
            
            rejoined.append(line)
            i += 1
        
        return rejoined

    def _improve_bice_description(self, desc: str) -> str:
        """Mejora descripción de BICE - Versión ROBUSTA"""
        
        desc_lower = desc.lower()
        
        # ============ TRANSFERENCIAS ============
        if 'transferencia' in desc_lower:
            
            # PATRÓN 1: "Transferencia de [ORIGEN] ... a [DESTINATARIO]"
            # Buscar el último " a " en la descripción (el más probable destinatario)
            match = re.search(
                r'transferencia\s+de\s+([A-Za-zÁáÉéÍíÓóÚúñÑ\s]+?)\s+(?:rut|run)?\s*[\d\.\-]*\s+(?:desde\s+)?(?:banco[a-z]*\s+)?a\s+([A-Za-zÁáÉéÍíÓóÚúñÑ\s]+?)(?:\s+(?:rut|run|cuenta|corriente|pesos|chile|el\s+\d)|\s*$)',
                desc,
                re.IGNORECASE
            )
            if match:
                destinatario = match.group(2).strip()
                # Limpiar números de RUT o fechas al final
                destinatario = re.sub(r'\s+(?:rut|run|cuenta|corriente|el\s+\d).*$', '', destinatario, flags=re.IGNORECASE).strip()
                destinatario = re.sub(r'\d+[\.\-]*\d+.*$', '', destinatario).strip()  # Elimina RUT pegado
                
                if destinatario and 3 <= len(destinatario) <= 100 and any(c.isalpha() for c in destinatario):
                    return f"Transferencia a {destinatario}"
            
            # PATRÓN 2: Si no encontró "a [DESTINATARIO]", buscar nombre más simple
            # Esto captura "Transferencia de Juan Carlos Pantoja Robles"
            match = re.search(r'transferencia\s+(?:de\s+)?([A-Za-zÁáÉéÍíÓóÚúñÑ\s]+?)(?:\s+rut|\s+run|\s*$)', desc, re.IGNORECASE)
            if match:
                nombre = match.group(1).strip()
                nombre = re.sub(r'\s+(?:rut|run).*$', '', nombre, flags=re.IGNORECASE).strip()
                if nombre and 3 <= len(nombre) <= 100 and any(c.isalpha() for c in nombre):
                    return f"Transferencia {nombre}"
        
        # ============ ABONOS ============
        if 'abono' in desc_lower:
            if 'liquidacion' in desc_lower and 'capital' in desc_lower:
                return "Abono Liquidación Capital Depósito"
            
            if 'pago proveedores' in desc_lower or 'pago proveedor' in desc_lower:
                return "Abono Pago Proveedores"
            
            if 'transferencia' in desc_lower:
                # "Abono por transferencia de [ORIGEN]"
                match = re.search(
                    r'(?:abono\s+)?(?:por\s+)?transferencia\s+de\s+([A-Za-zÁáÉéÍíÓóÚúñÑ\s]+?)(?:\s+(?:rut|run|cuenta|el\s+\d)|\s*$)',
                    desc,
                    re.IGNORECASE
                )
                if match:
                    origen = match.group(1).strip()
                    origen = re.sub(r'\s+(?:rut|run|cuenta|el\s+\d).*$', '', origen, flags=re.IGNORECASE).strip()
                    if origen and 3 <= len(origen) <= 100 and any(c.isalpha() for c in origen):
                        return f"Abono de {origen}"
            
            # Abono genérico
            return "Abono"
        
        # ============ CARGOS ============
        if 'cargo' in desc_lower:
            if 'apertura' in desc_lower and 'deposito' in desc_lower:
                return "Cargo Apertura de Depósito"
            
            if 'dividendo' in desc_lower:
                return "Cargo Dividendo"
            
            if 'comision' in desc_lower or 'mantenimiento' in desc_lower:
                return "Cargo Comisión"
            
            if 'transferencia' in desc_lower:
                # "Cargo por transferencia a [DESTINATARIO]"
                match = re.search(
                    r'(?:cargo\s+)?(?:por\s+)?transferencia\s+a\s+([A-Za-zÁáÉéÍíÓóÚúñÑ\s]+?)(?:\s+(?:rut|run|cuenta)|\s*$)',
                    desc,
                    re.IGNORECASE
                )
                if match:
                    dest = match.group(1).strip()
                    dest = re.sub(r'\s+(?:rut|run|cuenta).*$', '', dest, flags=re.IGNORECASE).strip()
                    if dest and 3 <= len(dest) <= 100 and any(c.isalpha() for c in dest):
                        return f"Cargo Transferencia a {dest}"
            
            return "Cargo"
        
        # ============ FALLBACK ============
        # Si no encaja en ningún patrón, limpiar y retornar
        desc_clean = re.sub(r'\s+', ' ', desc).strip()
        
        # Limitar longitud
        if len(desc_clean) > 100:
            desc_clean = desc_clean[:100].rsplit(' ', 1)[0] + '...'
        
        return desc_clean
    
    def _parse_bice_checking_from_pdf(self, file_path: str) -> List[Dict]:
        """Extrae movimientos BICE - Intenta tabla, fallback a texto mejorado"""
        movements = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Intento 1: Extraer con configuración de tabla
                    settings = {
                        "vertical_strategy": "lines",
                        "horizontal_strategy": "lines",
                    }
                    tables = page.extract_tables(settings)
                    
                    if not tables or len(tables) == 0:
                        print(f"      ⚠️ No se encontraron tablas en página {page_num}, usando texto...")
                        
                        # Fallback: Procesar como texto pero juntando líneas correctamente
                        text = page.extract_text()
                        if text:
                            page_movements = self._parse_bice_from_text_improved(text, file_path)
                            movements.extend(page_movements)
                            print(f"      ✅ {len(page_movements)} movimientos extraídos del texto")
                        continue
                    
                    print(f"      📊 Tabla encontrada en página {page_num}, procesando...")
                    
                    for table in tables:
                        for row_idx, row in enumerate(table):
                            if not row or len(row) < 4:
                                continue
                            
                            row_text = ' '.join(str(cell or '') for cell in row).lower()
                            if any(word in row_text for word in ['fecha', 'categoría', 'descripción']):
                                continue
                            
                            try:
                                fecha_str = (row[0] or '').strip()
                                descripcion_raw = (row[3] or '').strip()
                                monto_str = (row[4] or '').strip() if len(row) > 4 else ''
                                
                                if not fecha_str or not descripcion_raw or not monto_str:
                                    continue
                                
                                fecha_match = re.search(r'(\d{1,2})\s+([a-z]{3})\s+(\d{4})', fecha_str, re.IGNORECASE)
                                if not fecha_match:
                                    continue
                                
                                month_map = {
                                    'ene': 1, 'enero': 1, 'feb': 2, 'febrero': 2, 'mar': 3, 'marzo': 3,
                                    'apr': 4, 'abr': 4, 'may': 5, 'mayo': 5, 'jun': 6, 'junio': 6,
                                    'jul': 7, 'julio': 7, 'ago': 8, 'agos': 8, 'sep': 9, 'sept': 9,
                                    'oct': 10, 'octubre': 10, 'nov': 11, 'noviembre': 11, 'dic': 12
                                }
                                
                                dia_str, mes_str, ano_str = fecha_match.groups()
                                mes = month_map.get(mes_str.lower())
                                
                                if not mes:
                                    continue
                                
                                fecha = f"{int(ano_str):04d}-{mes:02d}-{int(dia_str):02d}"
                                
                                monto_match = re.search(r'\$\s*([\d\.,]+)', monto_str)
                                if not monto_match:
                                    continue
                                
                                monto = self._parse_amount(monto_match.group(1))
                                if not monto or monto <= 0 or monto > 500000000:
                                    continue
                                
                                descripcion = self._clean_description(descripcion_raw)
                                descripcion = self._improve_bice_description(descripcion)
                                
                                if not descripcion or len(descripcion) < 3 or not any(char.isalpha() for char in descripcion):
                                    continue
                                
                                desc_lower = descripcion.lower()
                                tipo = "ingreso" if any(w in desc_lower for w in ['abono', 'liquidacion']) else "gasto"
                                
                                existe = any(m['fecha'] == fecha and m['monto'] == monto and m['descripcion'].lower() == descripcion.lower() for m in movements)
                                if existe:
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
        
        except Exception as e:
            print(f"      ❌ Error: {e}")
        
        return movements

    def _parse_bice_from_text_improved(self, text: str, file_path: str) -> List[Dict]:
        """
        Parser BICE ROBUSTO v6 - N° operación solo para evitar duplicados
        """
        movements = []
        lines = text.split('\n')
        
        fecha_pattern = r'^(\d{1,2})\s+([a-z]{3})\s+(\d{4})'
        monto_pattern = r'\$\s*([\d\.,]+)\s*$'
        numero_operacion_pattern = r'\b(\d{8})\b'
        
        month_map = {
            'ene': 1, 'enero': 1, 'jan': 1, 'feb': 2, 'febrero': 2, 'fev': 2,
            'mar': 3, 'marzo': 3, 'apr': 4, 'abr': 4, 'abril': 4,
            'may': 5, 'mayo': 5, 'jun': 6, 'junio': 6, 'jul': 7, 'julio': 7,
            'ago': 8, 'agos': 8, 'agosto': 8, 'aug': 8, 'sep': 9, 'sept': 9,
            'oct': 10, 'octubre': 10, 'nov': 11, 'noviembre': 11,
            'dic': 12, 'diciembre': 12, 'dec': 12
        }
        
        palabras_descartables = [
            'saldo inicial', 'saldo final', 'saldo contable',
            'resumen del periodo', 'resumen', 
            'total abonos', 'total cargos',
            'sobregiro usado', 'sobregiro disponible',
            'abonos y cargos', 'fecha', 'categoría', 'descripción', 'monto',
            'saldos diarios', 'n° operación', 'número operación',
            'página', 'derechos reservados', 'casa matriz',
            'tu ejecutiva', 'email', 'sucursal', 'dirección'
        ]
        
        print(f"\n=== PARSING BICE FROM TEXT v6 ===\n")
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line or len(line) < 10:
                i += 1
                continue
            
            if any(palabra in line.lower() for palabra in palabras_descartables):
                i += 1
                continue
            
            if '©' in line or line.startswith('www') or ('@' in line and 'Nombre' not in line):
                i += 1
                continue
            
            fecha_match = re.match(fecha_pattern, line, re.IGNORECASE)
            if not fecha_match:
                i += 1
                continue
            
            try:
                dia_str, mes_str, ano_str = fecha_match.groups()
                mes = month_map.get(mes_str.lower())
                if not mes or mes < 1 or mes > 12:
                    i += 1
                    continue
                
                fecha = f"{int(ano_str):04d}-{mes:02d}-{int(dia_str):02d}"
                
                # Extraer número de operación (para duplicados)
                numero_operacion_match = re.search(numero_operacion_pattern, line)
                numero_operacion = numero_operacion_match.group(1) if numero_operacion_match else None
                
                monto_match = re.search(monto_pattern, line)
                
                if monto_match:
                    monto_str = monto_match.group(1)
                    monto_start = monto_match.start()
                    descripcion_raw = line[fecha_match.end():monto_start].strip()
                else:
                    descripcion_raw = line[fecha_match.end():].strip()
                    monto_str = None
                    
                    siguiente_idx = i + 1
                    while siguiente_idx < len(lines) and siguiente_idx < i + 5:
                        siguiente_line = lines[siguiente_idx].strip()
                        
                        if re.match(fecha_pattern, siguiente_line, re.IGNORECASE):
                            break
                        
                        if not siguiente_line:
                            break
                        
                        monto_match_obj = re.search(monto_pattern, siguiente_line)
                        if monto_match_obj:
                            monto_str = monto_match_obj.group(1)
                            linea_sin_monto = siguiente_line[:monto_match_obj.start()].strip()
                            if linea_sin_monto:
                                descripcion_raw += " " + linea_sin_monto
                            break
                        
                        if siguiente_line and not siguiente_line.startswith('$'):
                            descripcion_raw += " " + siguiente_line
                        
                        siguiente_idx += 1
                    
                    if not monto_str:
                        i += 1
                        continue
                
                monto = self._parse_amount(monto_str)
                if not monto or monto <= 0 or monto > 500000000:
                    i += 1
                    continue
                
                if any(palabra in descripcion_raw.lower() for palabra in ['saldo inicial', 'saldo final', 'total abonos', 'total cargos']):
                    i += 1
                    continue
                
                descripcion = self._clean_bice_description_robust(descripcion_raw)
                descripcion = self._improve_bice_description(descripcion)
                
                if not descripcion or len(descripcion) < 3:
                    i += 1
                    continue
                
                if not any(char.isalpha() for char in descripcion):
                    i += 1
                    continue
                
                desc_raw_lower = descripcion_raw.lower()
                if 'abono' in desc_raw_lower:
                    tipo = "ingreso"
                elif 'cargo' in desc_raw_lower:
                    tipo = "gasto"
                else:
                    tipo = "gasto"
                
                # ✅ CAMBIO: Usa número de operación en la clave de duplicados
                existe = any(
                    m['fecha'] == fecha and 
                    m['monto'] == monto and 
                    m['descripcion'].lower() == descripcion.lower() and
                    m.get('numero_operacion') == numero_operacion  # Permite mismo desc con diferente N° op
                    for m in movements
                )
                if existe:
                    i += 1
                    continue
                
                movement = {
                    "id": len(movements),
                    "fecha": fecha,
                    "descripcion": descripcion,
                    "monto": abs(monto),
                    "tipo": tipo,
                    "archivo_referencia": Path(file_path).name,
                    "categoria": "Sin Categoria",
                    "subcategoria": "Sin Subcategoria",
                    "numero_operacion": numero_operacion  # Guardarlo internamente
                }
                movements.append(movement)
                print(f"   ✅ [{len(movements):2d}] {fecha} | {tipo:7} | {descripcion[:60]:60} | ${monto:>12,.0f}")
            
            except Exception as e:
                print(f"   ❌ Error línea {i}: {str(e)[:50]}")
            
            i += 1
        
        print(f"\n=== TOTAL: {len(movements)} movimientos ===\n")
        return movements

    def _clean_bice_description_robust(self, text: str) -> str:
        """Limpia descripción BICE - Minimalista, solo lo necesario"""
        
        # Solo eliminar las cosas MÁS molestas:
        
        # 1. Eliminar URLs y emails
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        text = re.sub(r'www\.[A-Za-z0-9.-]+\.[A-Za-z]{2,}', '', text)
        
        # 2. Eliminar copyright/símbolos especiales
        text = re.sub(r'[©®™]', '', text)
        
        # 3. Eliminar "Página X de Y"
        text = re.sub(r'P[áa]gina\s+\d+\s+de\s+\d+', '', text, flags=re.IGNORECASE)
        
        # 4. Limpiar espacios múltiples
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _rejoin_bice_lines(self, lines: list) -> list:
        """Rejunta líneas de BICE que fueron divididas por el extractor"""
        rejoin = []
        i = 0
        
        print(f"\n=== DEBUG _rejoin_bice_lines ===")
        print(f"Total de líneas: {len(lines)}")
        print(f"\nPrimeras 20 líneas:")
        for idx, line in enumerate(lines[:20]):
            print(f"  [{idx}] {repr(line[:80])}")
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Si empieza con fecha, es inicio de movimiento
            if re.match(r'^\d{1,2}\s+[a-z]{3}', line, re.IGNORECASE):
                # Juntar con siguientes líneas hasta encontrar otra fecha o fin
                combined = line
                start_i = i
                i += 1
                
                while i < len(lines):
                    next_line = lines[i].strip()
                    
                    # Si la siguiente línea empieza con fecha, parar
                    if re.match(r'^\d{1,2}\s+[a-z]{3}', next_line, re.IGNORECASE):
                        break
                    
                    # Si es vacía, parar
                    if not next_line:
                        break
                    
                    # Agregar a la línea combinada
                    combined += " " + next_line
                    i += 1
                
                print(f"✅ [Movimiento {len(rejoin)+1}] Líneas {start_i}-{i}: {combined[:80]}...")
                rejoin.append(combined)
            else:
                i += 1
        
        print(f"\nTotal movimientos rejuntados: {len(rejoin)}")
        print(f"=== FIN DEBUG ===\n")
        
        return rejoin
    
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
        """Limpia descripción - MEJORADO para remover T, A, I finales"""
        desc = str(desc).strip()

        # NUEVO: Remover letras al final (T, A, I = códigos de tipo de transacción)
        # Ejemplo: "Ikea.com T" -> "Ikea.com"
        desc = re.sub(r'\s+[TAI]\s*$', '', desc)
        
        # Remover montos al final de la descripción
        desc = re.sub(r'\s+\d+(?:\.\d{3})*(?:,\d{2})?(?:\s+\d+(?:\.\d{3})*(?:,\d{2})?)*\s*$', '', desc)
        
        # Remover patrones de fecha
        desc = re.sub(r'\d{1,2}/\d{1,2}\s+\w+-\d{4}', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'\s*RUT\s+[\d\-\.]+.*', '', desc, flags=re.IGNORECASE)
        
        # Remover números largos (RUT, referencias)
        desc = re.sub(r'\s+\d{7,}\s*', ' ', desc)
        
        # Remover fechas al final
        desc = re.sub(r'\b\d{1,2}/\d{1,2}/\s*$', '', desc)
        desc = re.sub(r'\b\d{1,2}/\d{1,2}[\s|]*$', '', desc)
        
        # Normalizar espacios
        desc = re.sub(r'\s+', ' ', desc).strip()

        # Limitar longitud
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