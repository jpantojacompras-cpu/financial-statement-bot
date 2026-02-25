"""
Módulo para leer archivos Excel y PDF con soporte para múltiples bancos
Soporta: BICE, CMR, Santander (Cuenta Corriente y Tarjeta de Crédito)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
import re
from datetime import datetime

class FileReader:
    """Lee archivos XLSX y PDF con cartolas bancarias de diferentes bancos"""
    
    def __init__(self):
        self.supported_formats = ['.xlsx', '.pdf']
        self.banks = ['santander', 'bice', 'cmr', 'itau', 'bbva', 'scotiabank', 'corfo']
        self.detected_year = 2025
    
    def read_xlsx(self, file_path):
        """Lee un archivo Excel y extrae movimientos"""
        try:
            filename = Path(file_path).name.lower()
            print(f"\n📄 Procesando XLSX: {filename}")
            
            bank = self._detect_bank(filename)
            print(f"   Banco detectado: {bank}")
            
            if 'cmr' in filename:
                return self._read_cmr_xlsx(file_path)
            elif 'santander' in filename:
                return self._read_santander_xlsx(file_path)
            elif 'bice' in filename:
                return self._read_bice_xlsx(file_path)
            
            df = pd.read_excel(file_path)
            movements = self._extract_movements(df, file_path)
            
            if movements:
                return movements
            
            print(f"   Intentando saltar filas...")
            for skip_rows in range(1, 15):
                try:
                    df = pd.read_excel(file_path, skiprows=skip_rows)
                    movements = self._extract_movements(df, file_path)
                    if movements:
                        print(f"   Datos encontrados saltando {skip_rows} fila(s)")
                        return movements
                except:
                    continue
            
            return []
            
        except Exception as e:
            print(f"Error leyendo XLSX: {e}")
            return []
    
    def read_pdf(self, file_path):
        """Lee un archivo PDF y extrae movimientos"""
        try:
            import pdfplumber
            
            filename = Path(file_path).name.lower()
            print(f"\n📄 Procesando PDF: {filename}")
            
            bank = self._detect_bank(filename)
            print(f"   Banco detectado: {bank}")
            
            if 'cmr' in filename:
                return self._read_cmr_pdf(file_path)
            elif 'santander' in filename:
                return self._read_santander_pdf(file_path)
            
            movements = []
            
            with pdfplumber.open(file_path) as pdf:
                print(f"   Total de paginas: {len(pdf.pages)}")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    print(f"   Procesando pagina {page_num}...")
                    
                    text = page.extract_text()
                    if text:
                        page_movements = self._parse_pdf_text_bice(text, file_path, bank)
                        movements.extend(page_movements)
                        if page_movements:
                            print(f"      {len(page_movements)} movimientos encontrados")
            
            print(f"   Total movimientos extraidos: {len(movements)}")
            return movements
            
        except ImportError:
            print(f"Error: pdfplumber no instalado")
            return []
        except Exception as e:
            print(f"Error leyendo PDF: {e}")
            return []
    
    def _detect_bank(self, filename: str) -> str:
        """Detecta el banco por nombre del archivo"""
        filename_lower = filename.lower()
        for bank in self.banks:
            if bank in filename_lower:
                return bank.capitalize()
        return "Desconocido"
    
    def _read_santander_xlsx(self, file_path):
        """Parser para Santander XLSX"""
        try:
            print(f"   Usando parser Santander XLSX")
            
            xls = pd.ExcelFile(file_path)
            movements = []
            
            for sheet_name in xls.sheet_names:
                print(f"   Procesando hoja: {sheet_name}")
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                is_credit_card = any(keyword in sheet_name.lower() for keyword in ['tarjeta', 'credito', 'credit', 'cc', 'tdc'])
                
                sheet_movements = self._extract_santander_movements(df, file_path, is_credit_card)
                movements.extend(sheet_movements)
            
            return movements
            
        except Exception as e:
            print(f"Error en parser Santander XLSX: {e}")
            return []

    def _extract_santander_movements(self, df, file_path, is_credit_card=False):
        """Extrae movimientos Santander Excel"""
        movements = []
        
        if df.empty:
            return movements
        
        df.columns = [str(col).strip() for col in df.columns]
        
        fecha_idx = None
        desc_idx = None
        monto_idx = None
        
        for idx, col in enumerate(df.columns):
            col_lower = str(col).lower().strip()
            
            if 'fecha' in col_lower or 'date' in col_lower:
                fecha_idx = idx
            if 'descripcion' in col_lower or 'concepto' in col_lower or 'detalle' in col_lower:
                desc_idx = idx
            if 'monto' in col_lower or 'valor' in col_lower or 'amount' in col_lower:
                if 'debe' not in col_lower and 'haber' not in col_lower:
                    monto_idx = idx
            if 'debe' in col_lower and monto_idx is None:
                monto_idx = idx
        
        if fecha_idx is None or desc_idx is None or monto_idx is None:
            if len(df.columns) >= 4:
                fecha_idx = fecha_idx or 0
                desc_idx = desc_idx or 1
                monto_idx = monto_idx or 2
        
        if fecha_idx is None or desc_idx is None or monto_idx is None:
            return movements
        
        for idx, row in df.iterrows():
            try:
                fecha_val = row.iloc[fecha_idx] if fecha_idx < len(row) else None
                desc_val = row.iloc[desc_idx] if desc_idx < len(row) else None
                monto_val = row.iloc[monto_idx] if monto_idx < len(row) else None
                
                if pd.isna(fecha_val) or pd.isna(desc_val) or pd.isna(monto_val):
                    continue
                
                fecha_str = str(fecha_val).strip()
                desc_str = str(desc_val).strip()
                monto_str = str(monto_val).strip()
                
                if not fecha_str or len(fecha_str) < 5:
                    continue
                
                if any(palabra in desc_str.lower() for palabra in ['saldo inicial', 'saldo final', 'total', 'resumen']):
                    continue
                
                fecha = self._parse_date_santander(fecha_str)
                if not fecha:
                    continue
                
                descripcion = self._clean_description(desc_str)
                if not descripcion or len(descripcion) < 3:
                    continue
                
                monto = self._parse_amount(monto_str)
                if monto is None:
                    continue
                
                if monto < 0:
                    tipo = "gasto"
                    monto = abs(monto)
                else:
                    tipo = "ingreso"
                
                if monto <= 0:
                    continue
                
                movement = {
                    "id": len(movements),
                    "fecha": fecha,
                    "descripcion": descripcion,
                    "monto": monto,
                    "tipo": tipo,
                    "archivo_referencia": Path(file_path).name,
                    "categoria": "Sin Categoria",
                    "subcategoria": "Sin Subcategoria"
                }
                movements.append(movement)
                
            except Exception as e:
                continue
        
        return movements

    def _read_santander_pdf(self, file_path):
        """Parser para Santander PDF"""
        try:
            import pdfplumber
            
            print(f"   Usando parser Santander PDF")
            
            filename_lower = Path(file_path).name.lower()
            is_credit_card = any(keyword in filename_lower for keyword in ['tarjeta', 'tdc', 'tc', 'credito'])
            
            if not is_credit_card:
                try:
                    with pdfplumber.open(file_path) as pdf:
                        first_page_text = pdf.pages[0].extract_text() if pdf.pages else ""
                        if first_page_text:
                            is_credit_card = any(keyword in first_page_text.lower() for keyword in ['tarjeta', 'tarjeta de credito', 'tdc'])
                            year_match = re.search(r'(20\d{2}|19\d{2})', first_page_text)
                            if year_match:
                                self.detected_year = int(year_match.group(1))
                except:
                    pass
            
            movements = []
            
            with pdfplumber.open(file_path) as pdf:
                print(f"   Total de paginas: {len(pdf.pages)}")
                print(f"   Tipo: {'Tarjeta Credito' if is_credit_card else 'Cuenta Corriente'}")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    print(f"   Procesando pagina {page_num}...")
                    
                    page_movements = []
                    
                    try:
                        tables = page.extract_tables()
                        if tables and len(tables) > 0:
                            for table in tables:
                                if is_credit_card:
                                    table_movements = self._parse_santander_credit_card_table(table, file_path)
                                else:
                                    table_movements = self._parse_santander_table(table, file_path)
                                
                                if table_movements:
                                    page_movements.extend(table_movements)
                    except Exception as e:
                        pass
                    
                    if not page_movements:
                        try:
                            text = page.extract_text()
                            if text:
                                if is_credit_card:
                                    text_movements = self._parse_santander_credit_card_text(text, file_path)
                                else:
                                    text_movements = self._parse_santander_pdf_text(text, file_path)
                                
                                if text_movements:
                                    page_movements.extend(text_movements)
                        except Exception as e:
                            pass
                    
                    if page_movements:
                        print(f"      Pagina {page_num}: {len(page_movements)} movimientos")
                        movements.extend(page_movements)
            
            print(f"   Total movimientos extraidos: {len(movements)}")
            return movements
            
        except Exception as e:
            print(f"Error en parser Santander PDF: {e}")
            return []

    def _parse_santander_table(self, table: list, file_path: str) -> List[Dict]:
        """Parsea tabla Santander Cuenta Corriente"""
        if not table or len(table) < 2:
            return []
        
        movements = []
        
        header_row_idx = -1
        for idx, row in enumerate(table):
            row_str = ' '.join([str(cell) if cell else '' for cell in row]).lower()
            if 'fecha' in row_str and 'descripcion' in row_str:
                header_row_idx = idx
                break
        
        if header_row_idx == -1:
            return movements
        
        headers = table[header_row_idx]
        cargos_col = None
        abonos_col = None
        
        for idx, header in enumerate(headers):
            if header is None:
                continue
            header_lower = str(header).lower()
            if 'cargos' in header_lower:
                cargos_col = idx
            if 'depositos' in header_lower or 'abonos' in header_lower:
                abonos_col = idx
        
        for row_idx in range(header_row_idx + 1, len(table)):
            row = table[row_idx]
            if not row:
                continue
            
            try:
                fecha_cell = str(row[0]) if len(row) > 0 else ""
                desc_cell = str(row[1]) if len(row) > 1 else ""
                cargos_cell = str(row[cargos_col]) if cargos_col and cargos_col < len(row) else ""
                abonos_cell = str(row[abonos_col]) if abonos_col and abonos_col < len(row) else ""
                
                if not fecha_cell or not desc_cell:
                    continue
                
                fecha_pattern = r'(\d{1,2}/\d{1,2})'
                fechas = re.findall(fecha_pattern, fecha_cell)
                descripciones = [d.strip() for d in desc_cell.split('\n') if d.strip()]
                montos_cargos = re.findall(r'(\d+(?:\.\d{3})*)', cargos_cell)
                montos_abonos = re.findall(r'(\d+(?:\.\d{3})*)', abonos_cell)
                
                for move_idx, desc_raw in enumerate(descripciones):
                    if not desc_raw or len(desc_raw) < 3:
                        continue
                    
                    try:
                        if move_idx >= len(fechas):
                            break
                        
                        fecha_str = fechas[move_idx]
                        dia, mes = fecha_str.split('/')
                        ano = self.detected_year
                        fecha = f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"
                        
                        desc_limpia = re.sub(r'^\d+[\s\-]*', '', desc_raw).strip()
                        descripcion = self._clean_description(desc_limpia)
                        
                        if not descripcion or len(descripcion) < 3:
                            continue
                        
                        monto = None
                        tipo = None
                        
                        if move_idx < len(montos_cargos) and montos_cargos[move_idx]:
                            monto = self._parse_amount(montos_cargos[move_idx])
                            if monto and monto > 0:
                                tipo = "gasto"
                        
                        if (not tipo or tipo is None) and move_idx < len(montos_abonos) and montos_abonos[move_idx]:
                            monto = self._parse_amount(montos_abonos[move_idx])
                            if monto and monto > 0:
                                tipo = "ingreso"
                        
                        if not monto or monto == 0 or not tipo:
                            continue
                        
                        if monto > 5000000:
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
                continue
        
        return movements

    def _parse_santander_credit_card_table(self, table: list, file_path: str) -> List[Dict]:
        """Parsea tabla TDC Santander"""
        if not table or len(table) < 2:
            return []
        
        movements = []
        
        header_row_idx = -1
        for idx, row in enumerate(table):
            row_str = ' '.join([str(cell) if cell else '' for cell in row]).lower()
            if 'movimientos tarjeta' in row_str or 'periodo actual' in row_str:
                header_row_idx = idx
                break
        
        if header_row_idx == -1:
            for idx, row in enumerate(table):
                if len(row) >= 3:
                    row_str = ' '.join([str(cell) if cell else '' for cell in row]).lower()
                    if 'fecha' in row_str or 'operacion' in row_str:
                        header_row_idx = idx
                        break
        
        if header_row_idx == -1:
            return movements
        
        for row_idx in range(header_row_idx + 1, len(table)):
            row = table[row_idx]
            if not row or len(row) < 3:
                continue
            
            try:
                row_text = ' | '.join([str(cell) if cell else '' for cell in row])
                
                if any(palabra in row_text.lower() for palabra in [
                    'total operaciones', 'productos o servicios', 'cargos, comisiones',
                    'informacion', 'periodo anterior', 'banco', 'comprobante'
                ]):
                    continue
                
                fecha_pattern = r'(\d{1,2}/\d{1,2}/\d{4})'
                fecha_match = re.search(fecha_pattern, row_text)
                
                if not fecha_match:
                    continue
                
                fecha_str = fecha_match.group(1)
                
                try:
                    partes_fecha = fecha_str.split('/')
                    dia = int(partes_fecha[0])
                    mes = int(partes_fecha[1])
                    ano = int(partes_fecha[2])
                    
                    if mes < 1 or mes > 12 or dia < 1 or dia > 31:
                        continue
                    
                    fecha = f"{ano}-{mes:02d}-{dia:02d}"
                except:
                    continue
                
                fecha_end = fecha_match.end()
                resto = row_text[fecha_end:].strip()
                
                monto_pattern = r'\$\s*(\d+(?:\.\d{3})*(?:,\d{2})?|\d+,\d+)'
                monto_match = re.search(monto_pattern, resto)
                
                if not monto_match:
                    monto_pattern = r'(\d+(?:\.\d{3})*)'
                    monto_matches = re.findall(monto_pattern, resto)
                    if monto_matches:
                        monto_str = monto_matches[-1]
                    else:
                        continue
                else:
                    monto_str = monto_match.group(1)
                
                if monto_match:
                    descripcion_raw = resto[:monto_match.start()].strip()
                else:
                    descripcion_raw = resto
                
                descripcion_raw = re.sub(r'\s+\|\s+', ' ', descripcion_raw)
                descripcion = self._clean_description(descripcion_raw)
                
                if not descripcion or len(descripcion) < 5:
                    continue
                
                if any(palabra in descripcion.lower() for palabra in [
                    'banco', 'comprobante', 'cliente', 'timbro', 'emisor'
                ]):
                    continue
                
                monto = self._parse_amount(monto_str)
                
                if not monto or monto == 0 or monto > 50000000:
                    continue
                
                if 'monto cancelado' in descripcion.lower():
                    tipo = "ingreso"
                    descripcion = "Pago Tarjeta de Credito"
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

    def _parse_santander_pdf_text(self, text: str, file_path: str) -> List[Dict]:
        """Parsea texto CC Santander"""
        if not text or len(text) < 20:
            return []
        
        movements = []
        lines = text.split('\n')
        
        year_match = re.search(r'(20\d{2}|19\d{2})', text)
        if year_match:
            self.detected_year = int(year_match.group(1))
        
        palabras_descartables = ['estado de cuenta', 'saldo', 'total', 'informacion', 'cartola']
        
        fecha_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4})'
        
        for line_idx, line in enumerate(lines):
            line = line.strip()
            
            if not line or len(line) < 20:
                continue
            
            if any(palabra in line.lower() for palabra in palabras_descartables):
                continue
            
            fecha_match = re.search(fecha_pattern, line)
            if not fecha_match:
                continue
            
            try:
                fecha_str = fecha_match.group(1)
                
                partes = fecha_str.split('/')
                dia = int(partes[0])
                mes = int(partes[1])
                ano = int(partes[2])
                
                if ano < 100:
                    ano += 2000
                
                if mes < 1 or mes > 12 or dia < 1 or dia > 31:
                    continue
                
                fecha = f"{ano}-{mes:02d}-{dia:02d}"
                
                fecha_end = fecha_match.end()
                resto = line[fecha_end:].strip()
                
                if not resto or len(resto) < 10:
                    continue
                
                monto_pattern = r'(\d+(?:\.\d{3})*(?:\,\d{2})?|\d+)'
                montos = re.findall(monto_pattern, resto)
                
                if not montos:
                    continue
                
                montos_validos = [m for m in montos if int(m.replace('.', '').replace(',', '')) >= 100]
                if montos_validos:
                    monto_str = montos_validos[-1]
                else:
                    monto_str = montos[-1]
                
                monto_match = re.search(re.escape(monto_str), resto)
                if monto_match:
                    descripcion_raw = resto[:monto_match.start()].strip()
                else:
                    descripcion_raw = resto
                
                descripcion = self._clean_description(descripcion_raw)
                
                if not descripcion or len(descripcion) < 5:
                    continue
                
                monto = self._parse_amount(monto_str)
                if monto is None or monto == 0:
                    continue
                
                if monto > 10000000:
                    continue
                
                tipo = "ingreso"
                if any(palabra in descripcion.lower() for palabra in ['transf', 'pago', 'giro', 'cheque', 'retiro']):
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

# Reemplaza solo este método en file_reader.py

    def _parse_santander_credit_card_text(self, text: str, file_path: str) -> List[Dict]:
        """Parsea texto TDC Santander - MEJORADO"""
        if not text or len(text) < 20:
            return []
        
        movements = []
        lines = text.split('\n')
        
        year_match = re.search(r'(20\d{2}|19\d{2})', text)
        if year_match:
            self.detected_year = int(year_match.group(1))
            print(f"         Año detectado: {self.detected_year}")
        
        palabras_descartables = [
            'estado de cuenta', 'periodo anterior', 'periodo actual', 'saldo',
            'total operaciones', 'informacion', 'cartola', 'banco', 'timbro',
            'total a pagar', 'pago minimo'
        ]
        
        # Patrones múltiples de fecha
        fecha_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{4})',  # dd/mm/yyyy
            r'(\d{1,2}/\d{1,2}/\d{2})',   # dd/mm/yy
            r'(\d{2}\d{2})',               # ddmm en algunos PDFs
        ]
        
        print(f"         Procesando {len(lines)} lineas...")
        
        for line_idx, line in enumerate(lines):
            line = line.strip()
            
            if not line or len(line) < 15:
                continue
            
            if any(palabra in line.lower() for palabra in palabras_descartables):
                continue
            
            # Intentar encontrar fecha
            fecha_match = None
            fecha_str = None
            
            for pattern in fecha_patterns:
                fecha_match = re.search(pattern, line)
                if fecha_match:
                    fecha_str = fecha_match.group(1)
                    break
            
            if not fecha_match or not fecha_str:
                continue
            
            try:
                # Parsear fecha
                if len(fecha_str.split('/')) == 3:
                    partes = fecha_str.split('/')
                    dia = int(partes[0])
                    mes = int(partes[1])
                    ano = int(partes[2])
                    
                    if ano < 100:
                        ano += 2000
                else:
                    continue
                
                # Validar rango
                if mes < 1 or mes > 12 or dia < 1 or dia > 31:
                    continue
                
                fecha = f"{ano}-{mes:02d}-{dia:02d}"
                
                # Extraer resto de la línea
                fecha_end = fecha_match.end()
                resto = line[fecha_end:].strip()
                
                if not resto or len(resto) < 8:
                    continue
                
                # Buscar descripcion y monto
                # Patrón: descripcion seguida de monto
                # El monto puede estar al final
                
                # Buscar números (monto)
                monto_pattern = r'(\d+(?:\.\d{3})*(?:,\d{2})?|\d+,\d+|\d+)'
                montos = re.findall(monto_pattern, resto)
                
                if not montos:
                    continue
                
                # El último número es probablemente el monto
                monto_str = montos[-1]
                
                # Validar que sea un monto razonable
                monto_test = self._parse_amount(monto_str)
                if not monto_test or monto_test == 0 or monto_test > 100000000:
                    continue
                
                # Extraer descripción (antes del monto)
                monto_idx = resto.rfind(monto_str)
                if monto_idx > 0:
                    descripcion_raw = resto[:monto_idx].strip()
                else:
                    descripcion_raw = resto
                
                # Limpiar
                descripcion_raw = re.sub(r'\s+\|\s+', ' ', descripcion_raw)
                descripcion_raw = re.sub(r'\s{2,}', ' ', descripcion_raw)
                descripcion = self._clean_description(descripcion_raw)
                
                # Validaciones
                if not descripcion or len(descripcion) < 3:
                    continue
                
                if any(palabra in descripcion.lower() for palabra in [
                    'banco', 'comprobante', 'cliente', 'timbro', 'emisor',
                    'valor cuota', 'numero', 'rut'
                ]):
                    continue
                
                # Parsear monto
                monto = self._parse_amount(monto_str)
                
                if not monto or monto == 0:
                    continue
                
                # Determinar tipo
                if 'monto cancelado' in descripcion.lower():
                    tipo = "ingreso"
                    descripcion = "Pago Tarjeta de Credito"
                elif 'pago' in descripcion.lower():
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
                
                emoji = "💰" if tipo == "ingreso" else "📉"
                print(f"         {emoji} {fecha} | {descripcion[:35]:35} | ${monto:>12,.0f}")
                
            except Exception as e:
                continue
        
        print(f"         Total movimientos TDC: {len(movements)}")
        return movements

    def _parse_date_santander(self, date_str: str) -> str:
        """Parsea fecha Santander"""
        if not date_str:
            return None
        
        date_str = str(date_str).strip()
        
        formats = ['%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y', '%Y-%m-%d', '%d %m %Y']
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    
    def _read_cmr_xlsx(self, file_path):
        """Parser CMR XLSX"""
        try:
            print(f"   Usando parser CMR XLSX")
            
            xls = pd.ExcelFile(file_path)
            movements = []
            
            for sheet_name in xls.sheet_names:
                print(f"   Procesando hoja: {sheet_name}")
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                sheet_movements = self._extract_cmr_movements(df, file_path)
                movements.extend(sheet_movements)
            
            return movements
            
        except Exception as e:
            print(f"Error en parser CMR XLSX: {e}")
            return []
    
    def _extract_cmr_movements(self, df, file_path):
        """Extrae movimientos CMR"""
        movements = []
        
        if df.empty:
            return movements
        
        df.columns = [str(col).strip() for col in df.columns]
        
        fecha_idx = None
        desc_idx = None
        monto_idx = None
        
        for idx, col in enumerate(df.columns):
            col_lower = str(col).lower().strip()
            
            if 'fecha' in col_lower:
                fecha_idx = idx
            if 'descripcion' in col_lower:
                desc_idx = idx
            if 'monto' in col_lower and monto_idx is None:
                monto_idx = idx
        
        if fecha_idx is None or desc_idx is None or monto_idx is None:
            if len(df.columns) >= 5:
                fecha_idx = fecha_idx or 1
                desc_idx = desc_idx or 2
                monto_idx = monto_idx or 4
        
        if fecha_idx is None or desc_idx is None or monto_idx is None:
            return movements
        
        for idx, row in df.iterrows():
            try:
                fecha_val = row.iloc[fecha_idx] if fecha_idx < len(row) else None
                desc_val = row.iloc[desc_idx] if desc_idx < len(row) else None
                monto_val = row.iloc[monto_idx] if monto_idx < len(row) else None
                
                if pd.isna(fecha_val) or pd.isna(desc_val) or pd.isna(monto_val):
                    continue
                
                fecha_str = str(fecha_val).strip()
                desc_str = str(desc_val).strip()
                monto_str = str(monto_val).strip()
                
                if not fecha_str or len(fecha_str) < 5:
                    continue
                
                fecha = self._parse_date_cmr(fecha_str)
                if not fecha:
                    continue
                
                descripcion = self._clean_description(desc_str)
                if not descripcion or len(descripcion) < 3:
                    continue
                
                monto = self._parse_amount(monto_str)
                if monto is None:
                    continue
                
                if monto < 0:
                    tipo = "ingreso"
                    monto = abs(monto)
                else:
                    tipo = "gasto"
                
                if monto <= 0:
                    continue
                
                movement = {
                    "id": len(movements),
                    "fecha": fecha,
                    "descripcion": descripcion,
                    "monto": monto,
                    "tipo": tipo,
                    "archivo_referencia": Path(file_path).name,
                    "categoria": "Sin Categoria",
                    "subcategoria": "Sin Subcategoria"
                }
                movements.append(movement)
                
            except Exception as e:
                continue
        
        return movements
    
    def _read_cmr_pdf(self, file_path):
        """Parser CMR PDF"""
        try:
            import pdfplumber
            
            print(f"   Usando parser CMR PDF")
            movements = []
            
            with pdfplumber.open(file_path) as pdf:
                print(f"   Total de paginas: {len(pdf.pages)}")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    print(f"   Procesando pagina {page_num}...")
                    
                    text = page.extract_text()
                    
                    if text:
                        page_movements = self._parse_cmr_pdf_text(text, file_path)
                        movements.extend(page_movements)
            
            return movements
            
        except Exception as e:
            print(f"Error en parser CMR PDF: {e}")
            return []
    
    def _parse_cmr_pdf_text(self, text: str, file_path: str) -> List[Dict]:
        """Parsea texto CMR PDF"""
        if not text or len(text) < 20:
            return []
        
        movements = []
        lines = text.split('\n')
        
        palabras_encabezado = ['COMPRAS NACIONALES', 'Sin Movimientos', 'Cargos, Comisiones', 'resumen', 'total']
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            if not line or len(line) < 15:
                continue
            
            if any(palabra in line for palabra in palabras_encabezado):
                continue
            
            fecha_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
            if not fecha_match:
                continue
            
            try:
                fecha_str = fecha_match.group(1)
                fecha = self._parse_date_cmr(fecha_str)
                if not fecha:
                    continue
                
                fecha_end = fecha_match.end()
                resto = line[fecha_end:].strip()
                
                partes = resto.split()
                
                if not partes:
                    continue
                
                descripcion_parts = []
                monto_str = None
                ta_encontrado = False
                
                for i, parte in enumerate(partes):
                    if parte in ['T', 'A', 'A1']:
                        ta_encontrado = True
                        
                        for j in range(i + 1, len(partes)):
                            numero = partes[j]
                            
                            if re.match(r'^-?\d+(?:\.\d{3})*$', numero):
                                monto_val = self._parse_amount(numero)
                                if monto_val:
                                    monto_str = numero
                                    break
                        break
                    else:
                        descripcion_parts.append(parte)
                
                if not ta_encontrado or not monto_str or not descripcion_parts:
                    continue
                
                descripcion_raw = ' '.join(descripcion_parts)
                descripcion = self._clean_description(descripcion_raw)
                
                if not descripcion or len(descripcion) < 3:
                    continue
                
                monto = self._parse_amount(monto_str)
                if monto is None or monto == 0:
                    continue
                
                if monto < 0:
                    tipo = "ingreso"
                    monto = abs(monto)
                else:
                    tipo = "gasto"
                
                movement = {
                    "id": len(movements),
                    "fecha": fecha,
                    "descripcion": descripcion,
                    "monto": monto,
                    "tipo": tipo,
                    "archivo_referencia": Path(file_path).name,
                    "categoria": "Sin Categoria",
                    "subcategoria": "Sin Subcategoria"
                }
                movements.append(movement)
                
            except Exception as e:
                continue
        
        return movements
    
    def _read_bice_xlsx(self, file_path):
        """Parser BICE XLSX"""
        try:
            print(f"   Usando parser BICE XLSX")
            
            df = pd.read_excel(file_path)
            movements = self._extract_movements(df, file_path)
            
            return movements
            
        except Exception as e:
            print(f"Error en parser BICE XLSX: {e}")
            return []
    
    def _parse_pdf_text_bice(self, text: str, file_path: str, bank: str) -> List[Dict]:
        """Parsea texto BICE PDF"""
        if not text or len(text) < 20:
            return []
        
        movements = []
        lines = text.split('\n')
        
        fecha_pattern = r'^(\d{1,2}\s+[a-z]{3}\s+\d{4})'
        
        for line in lines:
            line = line.strip()
            
            fecha_match = re.search(fecha_pattern, line, re.IGNORECASE)
            if not fecha_match:
                continue
            
            try:
                fecha_str = fecha_match.group(1)
                fecha = self._parse_date(fecha_str)
                if not fecha:
                    continue
                
                tipo = "ingreso" if "abono" in line.lower() else "gasto"
                
                monto_pattern = r'\$\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:[,\.][0-9]{2})?)'
                monto_matches = list(re.finditer(monto_pattern, line))
                
                if not monto_matches:
                    continue
                
                monto_str = monto_matches[-1].group(1)
                monto = self._parse_amount(monto_str)
                
                if monto is None or monto <= 0:
                    continue
                
                desc = line
                desc = re.sub(fecha_pattern, '', desc, flags=re.IGNORECASE)
                desc = re.sub(r'\$\s*[0-9]{1,3}(?:\.[0-9]{3})*', '', desc)
                desc = desc.strip()
                
                descripcion = self._clean_description(desc)
                
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
    
    def _extract_movements(self, df, file_path):
        """Extrae movimientos Excel generico"""
        if df.empty:
            return []
        
        movements = []
        df.columns = df.columns.str.strip()
        df.columns = [str(col).lower().strip() for col in df.columns]
        
        date_col = self._find_column(df, ['fecha', 'date'])
        desc_col = self._find_column(df, ['descripcion', 'description'])
        amount_col = self._find_column(df, ['monto', 'amount'])
        
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
                    "monto": monto,
                    "tipo": "ingreso" if monto > 0 else "gasto",
                    "archivo_referencia": Path(file_path).name,
                    "categoria": "Sin Categoria",
                    "subcategoria": "Sin Subcategoria"
                }
                movements.append(movement)
                
            except Exception as e:
                continue
        
        return movements
    
    def _clean_description(self, desc: str) -> str:
        """Limpia descripcion"""
        desc = str(desc).strip()
        
        desc = re.sub(r'\d{1,2}/\d{1,2}\s+\w+-\d{4}', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'\s*RUT\s+[\d\-\.]+.*', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'\s+\d{7,}\s*', ' ', desc)
        desc = re.sub(r'\b\d{1,2}/\d{1,2}/\s*$', '', desc)
        desc = re.sub(r'\b\d{1,2}/\d{1,2}[\s|]*$', '', desc)
        desc = re.sub(r'\s+', ' ', desc).strip()
        
        if len(desc) > 100:
            desc = desc[:97] + "..."
        
        return desc.strip()
    
    def _parse_date(self, date_str: str) -> str:
        """Parsea fecha"""
        if not date_str or date_str.lower() == 'nan':
            return None
        
        date_str = str(date_str).strip()
        
        formats = ['%d %b %Y', '%d %B %Y', '%d %m %Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y']
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    
    def _parse_date_cmr(self, date_str: str) -> str:
        """Parsea fecha CMR"""
        if not date_str:
            return None
        
        date_str = str(date_str).strip()
        
        formats = ['%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y', '%Y-%m-%d']
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parsea monto"""
        if not amount_str or amount_str.lower() == 'nan':
            return None
        
        amount_str = str(amount_str).strip().replace(' ', '')
        
        if not amount_str:
            return None
        
        is_negative = amount_str.startswith('-')
        if is_negative:
            amount_str = amount_str[1:]
        
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
    
    def _find_column(self, df, possible_names):
        """Busca columna"""
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