from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pathlib import Path
import shutil
import json
import threading
from datetime import datetime
import hashlib
import asyncio
from modules.file_reader import FileReader
from modules.file_detector import FileDetector
from modules.categorization_service import CategorizationService
from difflib import SequenceMatcher
import uuid
from config import (
    ALLOWED_ORIGINS,
    MAX_FILES_PER_BATCH,
    MAX_FILE_SIZE_MB,
    BACKEND_HOST,
    BACKEND_PORT,
)
from logging_config import logger

# =====================================================================
# FUNCIÓN DE GENERACIÓN DE IDs CONSISTENTES
# =====================================================================

def generate_movement_id(movement: dict, filename: str = "") -> str:
    """
    Genera un ID único para un movimiento usando UUID
    Esto garantiza unicidad absoluta sin colisiones
    """
    # Usar UUID basado en el contenido + filename para reproducibilidad
    id_str = f"{filename}|{movement.get('fecha', '')}|{movement.get('descripcion', '')}|{movement.get('monto', '')}"
    
    # Crear un namespace UUID basado en el contenido
    # Así obtenemos IDs determinísticos pero únicos
    namespace = uuid.NAMESPACE_DNS
    mov_uuid = uuid.uuid5(namespace, id_str)
    
    return str(mov_uuid)

def enrich_movements_with_ids(movements: list, filename: str = "") -> list:
    """Añade IDs únicos a los movimientos"""
    seen = set()
    for idx, mov in enumerate(movements):
        if 'id' not in mov or not mov['id']:
            base_id = generate_movement_id(mov, filename)
            
            # Si por alguna razón hay colisión, agregar sufijo
            mov_id = base_id
            counter = 1
            while mov_id in seen:
                mov_id = f"{base_id}-{counter}"
                counter += 1
            
            mov['id'] = mov_id
            seen.add(mov_id)
    
    return movements

# =====================================================================
# INICIALIZACIÓN DE BD DE MOVIMIENTOS
# =====================================================================

MOVEMENTS_DB = Path("backend/data/movements_db.json")

def load_movements_db():
    """Carga la BD de movimientos"""
    if MOVEMENTS_DB.exists():
        with open(MOVEMENTS_DB, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_movements_db(db):
    """Guarda la BD de movimientos"""
    MOVEMENTS_DB.parent.mkdir(parents=True, exist_ok=True)
    with open(MOVEMENTS_DB, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

# BD global
movements_db = load_movements_db()

# =====================================================================
# ESTADO DE PROGRESO GLOBAL
# =====================================================================

file_processing_progress = {
    "is_processing": False,
    "progress": 0,
    "current_file": "",
    "total_files": 0,
    "processed_files": 0,
    "message": ""
}

def reset_progress():
    """Reinicia el estado de progreso"""
    global file_processing_progress
    file_processing_progress = {
        "is_processing": False,
        "progress": 0,
        "current_file": "",
        "total_files": 0,
        "processed_files": 0,
        "message": ""
    }

# =====================================================================
# CONFIGURACIÓN
# =====================================================================

app = FastAPI(
    title="Financial Statement Bot",
    description="API para procesar y analizar cartolas bancarias",
    version="1.0.0"
)

# Gzip compression for large responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
    max_age=3600,
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

PROCESSED_DIR = Path("processed_files")
PROCESSED_DIR.mkdir(exist_ok=True)

uploaded_files_registry = {}
active_files = set()
file_reader = FileReader()
file_detector = FileDetector()
categorization_service = CategorizationService()

# In-memory movements cache with thread safety
_movements_cache: dict = {}
_movements_cache_lock = threading.Lock()

# =====================================================================
# CACHÉ DE MOVIMIENTOS
# =====================================================================

def invalidate_movements_cache() -> None:
    """Invalida el caché de movimientos (llamar al modificar archivos activos)."""
    with _movements_cache_lock:
        _movements_cache.clear()

# =====================================================================
# INICIALIZACIÓN DE CATEGORÍAS
# =====================================================================

def initialize_categories_json():
    """Inicializa el archivo JSON de categorías desde el CSV si no existe"""
    categories_path = Path("backend/data/categories.json")
    
    if categories_path.exists():
        logger.info("✅ Categorías ya existen, preservando cambios del usuario")
        return
    
    logger.info("🔄 Inicializando categorías desde CSV...")
    try:
        all_categories_list = categorization_service.get_all_categories()
        categories_data = {}
        
        for category in all_categories_list:
            subcats = categorization_service.get_subcategories(category)
            categories_data[category] = subcats if subcats else ["Sin Subcategoría"]
        
        categories_path.parent.mkdir(parents=True, exist_ok=True)
        with open(categories_path, 'w', encoding='utf-8') as f:
            json.dump(categories_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Categorías inicializadas en JSON: {len(categories_data)} categorías")
    except Exception as e:
        logger.warning(f"⚠️  Error inicializando categorías: {e}")

# =====================================================================
# FUNCIONES AUXILIARES
# =====================================================================

def calculate_file_hash(file_path: Path) -> str:
    """Calcula hash SHA256 del archivo"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def is_file_already_uploaded(file_hash: str) -> dict:
    """Verifica si un archivo ya fue cargado"""
    if file_hash in uploaded_files_registry:
        return {
            "is_duplicate": True,
            "file_info": uploaded_files_registry[file_hash]
        }
    return {"is_duplicate": False}

def register_uploaded_file(file_hash: str, filename: str, movements_count: int, movements: list = None, detection: dict = None):
    """Registra un archivo como cargado"""
    file_info = {
        "nombre": filename,
        "fecha_carga": datetime.now().isoformat(),
        "movimientos": movements_count,
        "hash": file_hash
    }
    
    if detection:
        file_info["institucion"] = detection.get("institution", "unknown")
        file_info["tipo_producto"] = detection.get("product_type", "unknown")
        file_info["deteccion_confianza"] = detection.get("confidence", 0.0)
    
    if movements:
        fechas = [m.get('fecha') for m in movements if m.get('fecha')]
        if fechas:
            ultima_fecha = max(fechas)
            file_info["ultimo_mes"] = ultima_fecha[:7]
        else:
            file_info["ultimo_mes"] = "N/A"
    else:
        file_info["ultimo_mes"] = "N/A"
    
    uploaded_files_registry[file_hash] = file_info
    save_registry()

def save_registry():
    """Guarda el registro de archivos"""
    registry_file = PROCESSED_DIR / "uploaded_files.json"
    with open(registry_file, "w", encoding="utf-8") as f:
        json.dump(uploaded_files_registry, f, ensure_ascii=False, indent=2)

def load_registry():
    """Carga el registro de archivos"""
    global uploaded_files_registry
    registry_file = PROCESSED_DIR / "uploaded_files.json"
    if registry_file.exists():
        with open(registry_file, "r", encoding="utf-8") as f:
            uploaded_files_registry = json.load(f)

def save_active_files():
    """Guarda la lista de archivos activos"""
    active_file = PROCESSED_DIR / "active_files.json"
    with open(active_file, "w", encoding="utf-8") as f:
        json.dump({"active": list(active_files)}, f, ensure_ascii=False, indent=2)

def load_active_files():
    """Carga la lista de archivos activos"""
    global active_files
    active_file = PROCESSED_DIR / "active_files.json"
    if active_file.exists():
        with open(active_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            active_files = set(data.get("active", []))

load_registry()
load_active_files()
initialize_categories_json()

# =====================================================================
# RUTAS API - CARGA Y GESTIÓN DE ARCHIVOS
# =====================================================================

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "status": "API conectada",
        "servicio": "Financial Statement Bot",
        "version": "1.0.0",
        "archivos_cargados": len(uploaded_files_registry),
        "archivos_activos": len(active_files),
        "limites": {
            "max_archivos_por_carga": MAX_FILES_PER_BATCH,
            "max_tamaño_archivo_mb": MAX_FILE_SIZE_MB
        }
    }

@app.get("/processing-status")
async def get_processing_status():
    """Retorna el estado del procesamiento"""
    return file_processing_progress

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Carga un archivo individual"""
    global file_processing_progress
    
    temp_path = None
    try:
        logger.info(f"\n{'='*70}")
        logger.info(f"📁 SOLICITUD DE CARGA INDIVIDUAL")
        logger.info(f"{'='*70}")
        logger.info(f"📄 Archivo: {file.filename}")
        
        file_processing_progress["is_processing"] = True
        file_processing_progress["current_file"] = file.filename
        file_processing_progress["progress"] = 5
        file_processing_progress["message"] = f"Validando {file.filename}..."
        
        allowed_extensions = ['.xlsx', '.xls', '.pdf']
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            logger.error(f"❌ RECHAZO: Extensión no permitida ({file_ext})")
            file_processing_progress["is_processing"] = False
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": f"Formato no permitido. Use: {', '.join(allowed_extensions)}",
                    "file": file.filename
                }
            )
        
        temp_path = UPLOAD_DIR / file.filename
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        file_processing_progress["progress"] = 15
        file_processing_progress["message"] = f"Verificando tamaño de {file.filename}..."
        
        file_size_mb = temp_path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            temp_path.unlink()
            logger.error(f"❌ Archivo muy grande: {file_size_mb:.2f}MB (máx: {MAX_FILE_SIZE_MB}MB)")
            file_processing_progress["is_processing"] = False
            return JSONResponse(
                status_code=413,
                content={
                    "status": "error",
                    "message": f"Archivo muy grande: {file_size_mb:.2f}MB (máximo: {MAX_FILE_SIZE_MB}MB)",
                    "file": file.filename
                }
            )
        
        logger.info(f"✅ Archivo guardado: {file_size_mb:.2f}MB")
        
        file_processing_progress["progress"] = 25
        file_processing_progress["message"] = f"Calculando hash de {file.filename}..."
        
        file_hash = calculate_file_hash(temp_path)
        logger.info(f"🔐 Hash: {file_hash[:16]}...")
        
        file_processing_progress["progress"] = 35
        file_processing_progress["message"] = f"Verificando duplicados..."
        
        duplicate_check = is_file_already_uploaded(file_hash)
        
        if duplicate_check["is_duplicate"]:
            logger.warning(f"⚠️  ARCHIVO DUPLICADO")
            temp_path.unlink()
            file_processing_progress["is_processing"] = False
            
            file_info = duplicate_check["file_info"]
            return JSONResponse(
                status_code=409,
                content={
                    "status": "warning",
                    "message": "Este archivo ya fue cargado anteriormente",
                    "is_duplicate": True,
                    "original_file": {
                        "nombre": file_info['nombre'],
                        "fecha_carga": file_info['fecha_carga'],
                        "movimientos": file_info['movimientos'],
                        "institucion": file_info.get('institucion', 'unknown'),
                        "tipo_producto": file_info.get('tipo_producto', 'unknown')
                    }
                }
            )
        
        logger.info(f"✅ Archivo NUEVO")
        
        file_processing_progress["progress"] = 45
        file_processing_progress["message"] = f"Detectando institución..."
        
        logger.info(f"🔍 Detectando institución y tipo de producto...")
        detection = file_detector.detect_from_file(str(temp_path))
        logger.info(f"🏦 Institución detectada: {detection['institution']} (confianza: {detection['confidence']})")
        logger.info(f"💳 Tipo de producto: {detection['product_type']}")
        
        file_processing_progress["progress"] = 60
        file_processing_progress["message"] = f"Extrayendo movimientos..."
        
        logger.info(f"🔄 Extrayendo movimientos...")
        movements = []
        
        if file_ext == '.pdf':
            movements = file_reader.read_pdf(str(temp_path))
        else:
            movements = file_reader.read_xlsx(str(temp_path))
        
        # ✅ GENERAR IDs CONSISTENTES
        movements = enrich_movements_with_ids(movements, file.filename)
        
        file_processing_progress["progress"] = 75
        file_processing_progress["message"] = f"Inicializando categorías..."
        
        for movement in movements:
            if 'categoria' not in movement:
                movement['categoria'] = ''
            if 'subcategoria' not in movement:
                movement['subcategoria'] = ''

        if not movements:
            logger.error(f"❌ Sin movimientos extraídos")
            temp_path.unlink()
            file_processing_progress["is_processing"] = False
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "No se pudieron extraer movimientos del archivo",
                    "file": file.filename
                }
            )
        
        for movement in movements:
            movement['institucion'] = detection['institution']
            movement['tipo_producto'] = detection['product_type']
            movement['deteccion_confianza'] = detection['confidence']
        
        file_processing_progress["progress"] = 95
        file_processing_progress["message"] = f"Guardando {file.filename}..."
        
        register_uploaded_file(file_hash, file.filename, len(movements), movements, detection)
        active_files.add(file_hash)
        save_active_files()
        
        processed_path = PROCESSED_DIR / file.filename
        shutil.move(str(temp_path), str(processed_path))
        
        file_processing_progress["progress"] = 100
        file_processing_progress["message"] = f"✅ {file.filename} cargado"
        
        logger.info(f"✅ ÉXITO: {len(movements)} movimientos")
        logger.info(f"🔌 Estado: ACTIVO")
        
        await asyncio.sleep(2)
        file_processing_progress["is_processing"] = False
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": f"{len(movements)} movimientos extraídos",
                "file": file.filename,
                "movements_count": len(movements),
                "institucion": detection['institution'],
                "tipo_producto": detection['product_type'],
                "deteccion_confianza": detection['confidence'],
                "movements": movements,
                "file_info": {
                    "hash": file_hash,
                    "activo": True
                }
            }
        )
        
    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)}")
        file_processing_progress["is_processing"] = False
        
        if temp_path and temp_path.exists():
            temp_path.unlink()
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Error procesando archivo: {str(e)}",
                "file": file.filename if 'file' in locals() else "desconocido"
            }
        )

@app.post("/upload-batch")
async def upload_batch(files: list[UploadFile] = File(...)):
    """Carga múltiples archivos"""
    global file_processing_progress
    
    logger.info(f"\n{'='*70}")
    logger.info(f"📁 SOLICITUD DE CARGA MASIVA")
    logger.info(f"{'='*70}")
    logger.info(f"📦 Total archivos: {len(files)}")
    
    file_processing_progress["is_processing"] = True
    file_processing_progress["total_files"] = len(files)
    file_processing_progress["processed_files"] = 0
    
    if len(files) > MAX_FILES_PER_BATCH:
        logger.error(f"❌ RECHAZO: Demasiados archivos ({len(files)} > {MAX_FILES_PER_BATCH})")
        file_processing_progress["is_processing"] = False
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": f"Máximo {MAX_FILES_PER_BATCH} archivos por carga (enviaste {len(files)})",
                "limite": MAX_FILES_PER_BATCH,
                "enviados": len(files)
            }
        )
    
    results = []
    total_movements = 0
    successful = 0
    duplicates = 0
    errors = 0
    
    for idx, file in enumerate(files, 1):
        logger.info(f"\n[{idx}/{len(files)}] Procesando: {file.filename}")
        
        file_processing_progress["current_file"] = file.filename
        file_processing_progress["processed_files"] = idx - 1
        file_processing_progress["progress"] = int((idx / len(files)) * 100)
        file_processing_progress["message"] = f"Procesando {file.filename} ({idx}/{len(files)})"
        
        temp_path = None
        try:
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ['.xlsx', '.xls', '.pdf']:
                logger.info(f"   ❌ Extensión no permitida")
                results.append({
                    "file": file.filename,
                    "status": "error",
                    "message": "Extensión no permitida",
                    "movements": 0
                })
                errors += 1
                continue
            
            temp_path = UPLOAD_DIR / file.filename
            content = await file.read()
            
            with open(temp_path, "wb") as f:
                f.write(content)
            
            file_size_mb = temp_path.stat().st_size / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                temp_path.unlink()
                logger.info(f"   ❌ Archivo muy grande ({file_size_mb:.2f}MB)")
                results.append({
                    "file": file.filename,
                    "status": "error",
                    "message": f"Archivo muy grande ({file_size_mb:.2f}MB > {MAX_FILE_SIZE_MB}MB)",
                    "movements": 0
                })
                errors += 1
                continue
            
            logger.info(f"   ✅ Guardado ({file_size_mb:.2f}MB)")
            
            file_hash = calculate_file_hash(temp_path)
            
            duplicate_check = is_file_already_uploaded(file_hash)
            if duplicate_check["is_duplicate"]:
                temp_path.unlink()
                logger.info(f"   ⚠️  DUPLICADO")
                results.append({
                    "file": file.filename,
                    "status": "duplicate",
                    "message": "Archivo ya fue cargado",
                    "movements": duplicate_check["file_info"]["movimientos"]
                })
                duplicates += 1
                continue
            
            logger.info(f"   🔍 Detectando institución y tipo...")
            detection = file_detector.detect_from_file(str(temp_path))
            logger.info(f"   🏦 {detection['institution']} - {detection['product_type']} (confianza: {detection['confidence']})")
            
            movements = []
            if file_ext == '.pdf':
                movements = file_reader.read_pdf(str(temp_path))
            else:
                movements = file_reader.read_xlsx(str(temp_path))
            
            # ✅ GENERAR IDs CONSISTENTES
            movements = enrich_movements_with_ids(movements, file.filename)
                
            if not movements:
                temp_path.unlink()
                logger.info(f"   ❌ Sin movimientos")
                results.append({
                    "file": file.filename,
                    "status": "error",
                    "message": "No se extrajeron movimientos",
                    "movements": 0
                })
                errors += 1
                continue
            
            for movement in movements:
                if 'categoria' not in movement:
                    movement['categoria'] = ''
                if 'subcategoria' not in movement:
                    movement['subcategoria'] = ''

            for movement in movements:
                movement['institucion'] = detection['institution']
                movement['tipo_producto'] = detection['product_type']
                movement['deteccion_confianza'] = detection['confidence']
            
            register_uploaded_file(file_hash, file.filename, len(movements), movements, detection)
            active_files.add(file_hash)
            save_active_files()
            
            processed_path = PROCESSED_DIR / file.filename
            shutil.move(str(temp_path), str(processed_path))
            
            logger.info(f"   ✅ ÉXITO: {len(movements)} movimientos")
            results.append({
                "file": file.filename,
                "status": "success",
                "message": f"{len(movements)} movimientos extraídos",
                "movements": len(movements),
                "institucion": detection['institution'],
                "tipo_producto": detection['product_type'],
                "deteccion_confianza": detection['confidence'],
                "activo": True
            })
            
            successful += 1
            total_movements += len(movements)
            
        except Exception as e:
            logger.info(f"   ❌ ERROR: {str(e)}")
            if temp_path and temp_path.exists():
                temp_path.unlink()
            
            results.append({
                "file": file.filename,
                "status": "error",
                "message": str(e),
                "movements": 0
            })
            errors += 1
    
    logger.info(f"\n{'='*70}")
    logger.info(f"📊 RESUMEN DE CARGA MASIVA")
    logger.info(f"{'='*70}")
    logger.info(f"✅ Exitosos: {successful}")
    logger.warning(f"⚠️  Duplicados: {duplicates}")
    logger.error(f"❌ Errores: {errors}")
    logger.info(f"📈 Total movimientos: {total_movements}")
    logger.info(f"{'='*70}\n")
    
    file_processing_progress["progress"] = 100
    file_processing_progress["message"] = "✅ Carga completada"
    
    await asyncio.sleep(2)
    file_processing_progress["is_processing"] = False
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "completed",
            "message": f"Carga masiva completada: {successful} exitosos, {duplicates} duplicados, {errors} errores",
            "resumen": {
                "total_archivos": len(files),
                "exitosos": successful,
                "duplicados": duplicates,
                "errores": errors,
                "total_movimientos": total_movements
            },
            "resultados": results,
            "limites": {
                "max_archivos_por_carga": MAX_FILES_PER_BATCH,
                "max_tamaño_archivo_mb": MAX_FILE_SIZE_MB
            }
        }
    )

@app.get("/uploaded-files")
async def get_uploaded_files():
    """Obtiene lista de archivos cargados"""
    try:
        archivos = []
        
        for file_hash, file_info in uploaded_files_registry.items():
            
            if "ultimo_mes" not in file_info or file_info.get("ultimo_mes") == "N/A":
                try:
                    file_path = None
                    nombre_archivo = file_info.get("nombre", "")
                    
                    if PROCESSED_DIR.exists():
                        for f in PROCESSED_DIR.glob("*"):
                            if nombre_archivo in f.name or f.name in nombre_archivo:
                                file_path = f
                                break
                    
                    if file_path:
                        if nombre_archivo.lower().endswith('.pdf'):
                            movements = file_reader.read_pdf(str(file_path))
                        else:
                            movements = file_reader.read_xlsx(str(file_path))
                        
                        if movements:
                            fechas = [m.get('fecha') for m in movements if m.get('fecha')]
                            
                            if fechas:
                                ultima_fecha = max(fechas)
                                mes = ultima_fecha[:7]
                                file_info["ultimo_mes"] = mes
                            else:
                                file_info["ultimo_mes"] = "N/A"
                        else:
                            file_info["ultimo_mes"] = "N/A"
                        
                        save_registry()
                    else:
                        file_info["ultimo_mes"] = "N/A"
                except Exception as e:
                    file_info["ultimo_mes"] = "N/A"
            
            archivos.append({
                "hash": file_hash,
                "nombre": file_info.get('nombre', 'Desconocido'),
                "fecha_carga": file_info.get('fecha_carga', ''),
                "movimientos": file_info.get('movimientos', 0),
                "activo": file_hash in active_files,
                "institucion": file_info.get('institucion', 'Desconocida'),
                "ultimo_mes": file_info.get('ultimo_mes', 'N/A'),
            })

        return {"status": "success", "archivos": archivos}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/uploaded-files/{file_hash}/activate")
async def activate_file(file_hash: str):
    """Activa un archivo"""
    if file_hash not in uploaded_files_registry:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": f"Archivo no encontrado: {file_hash}"}
        )
    
    try:
        file_info = uploaded_files_registry[file_hash]
        active_files.add(file_hash)
        save_active_files()
        invalidate_movements_cache()
        
        logger.info(f"✅ Activado: {file_info['nombre']}")
        
        return {
            "status": "success",
            "message": f"Archivo activado: {file_info['nombre']}",
            "file_info": file_info
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/uploaded-files/{file_hash}/deactivate")
async def deactivate_file(file_hash: str):
    """Desactiva un archivo"""
    if file_hash not in uploaded_files_registry:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": f"Archivo no encontrado: {file_hash}"}
        )
    
    try:
        file_info = uploaded_files_registry[file_hash]
        active_files.discard(file_hash)
        save_active_files()
        invalidate_movements_cache()
        
        logger.info(f"⏸️  Desactivado: {file_info['nombre']}")
        
        return {
            "status": "success",
            "message": f"Archivo desactivado: {file_info['nombre']}",
            "file_info": file_info
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.delete("/uploaded-files/{file_hash}")
async def delete_uploaded_file(file_hash: str):
    """Elimina un archivo"""
    if file_hash not in uploaded_files_registry:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": f"Archivo no encontrado: {file_hash}"}
        )
    
    try:
        file_info = uploaded_files_registry[file_hash]
        filename = file_info['nombre']
        
        processed_path = PROCESSED_DIR / filename
        if processed_path.exists():
            processed_path.unlink()
        
        active_files.discard(file_hash)
        save_active_files()
        
        del uploaded_files_registry[file_hash]
        save_registry()
        invalidate_movements_cache()
        
        logger.info(f"🗑️  Eliminado: {filename}")
        
        return {
            "status": "success",
            "message": f"Archivo eliminado: {filename}",
            "file_info": file_info
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/movements")
async def get_movements(
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=0, ge=0, description="Elementos por página (0 = todos)"),
):
    """Retorna movimientos de archivos activos con IDs únicos y soporte de paginación."""
    global movements_db

    cache_key = "all_movements"
    with _movements_cache_lock:
        cached = _movements_cache.get(cache_key)

    if cached is None:
        all_movements: list = []
        logger.info("📊 Recargando movimientos desde archivos...")
        logger.info("   Archivos activos: %d de %d", len(active_files), len(uploaded_files_registry))

        for file_hash in active_files:
            if file_hash in uploaded_files_registry:
                file_info = uploaded_files_registry[file_hash]
                filename = file_info["nombre"]

                file_path = PROCESSED_DIR / filename
                if file_path.exists():
                    try:
                        if filename.lower().endswith(".pdf"):
                            movements = file_reader.read_pdf(str(file_path))
                        else:
                            movements = file_reader.read_xlsx(str(file_path))

                        movements = enrich_movements_with_ids(movements, filename)

                        if movements:
                            for movement in movements:
                                mov_id = movement.get("id")

                                if mov_id in movements_db:
                                    db_mov = movements_db[mov_id]
                                    movement["categoria"] = db_mov.get("categoria", "")
                                    movement["subcategoria"] = db_mov.get("subcategoria", "")
                                else:
                                    cat = movement.get("categoria", "").strip()
                                    subcat = movement.get("subcategoria", "").strip()

                                    if not cat or cat.lower() == "sin categoría":
                                        movement["categoria"] = ""
                                        movement["subcategoria"] = ""
                                    else:
                                        movement["categoria"] = cat
                                        movement["subcategoria"] = subcat

                                movement["institucion"] = file_info.get("institucion", "unknown")
                                movement["tipo_producto"] = file_info.get("tipo_producto", "unknown")

                            logger.info("   ✅ %s: %d movimientos", filename, len(movements))
                            all_movements.extend(movements)
                    except Exception as e:
                        logger.error("   ❌ %s: Error - %s", filename, e)

        logger.info("   Total: %d movimientos", len(all_movements))

        with _movements_cache_lock:
            _movements_cache[cache_key] = all_movements
        cached = all_movements

    total = len(cached)

    if page_size and page_size > 0:
        start = (page - 1) * page_size
        end = start + page_size
        page_movements = cached[start:end]
        total_pages = (total + page_size - 1) // page_size
    else:
        page_movements = cached
        total_pages = 1

    return {
        "status": "success",
        "total_movimientos": total,
        "archivos_activos": len(active_files),
        "pagina": page,
        "pagina_size": page_size or total,
        "total_paginas": total_pages,
        "movimientos": page_movements,
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "Healthy",
        "timestamp": datetime.now().isoformat(),
        "archivos_cargados": len(uploaded_files_registry),
        "archivos_activos": len(active_files),
        "limites": {
            "max_archivos_por_carga": MAX_FILES_PER_BATCH,
            "max_tamaño_archivo_mb": MAX_FILE_SIZE_MB
        }
    }

@app.delete("/uploaded-files")
async def delete_all_files():
    """Elimina TODOS los archivos cargados"""
    try:
        global uploaded_files_registry, active_files

        if PROCESSED_DIR.exists():
            for file_path in PROCESSED_DIR.glob("*.pdf"):
                file_path.unlink()
            for file_path in PROCESSED_DIR.glob("*.xlsx"):
                file_path.unlink()

        uploaded_files_registry = {}
        active_files = set()

        save_registry()
        save_active_files()

        logger.info("\n" + "="*70)
        logger.info("🗑️  TODOS LOS ARCHIVOS HAN SIDO ELIMINADOS")
        logger.info("="*70 + "\n")

        return {
            "status": "success",
            "message": "Todos los archivos han sido eliminados"
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

# =====================================================================
# ENDPOINTS DE CATEGORIZACIÓN
# =====================================================================

@app.post("/movements/find-similar")
async def find_similar_movements(request: dict):
    """Encuentra movimientos similares a uno dado"""
    try:
        movement_id = request.get("movement_id")
        descripcion = request.get("descripcion", "")
        categoria = request.get("categoria")
        subcategoria = request.get("subcategoria")
        
        if not all([movement_id, descripcion]):
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Faltan parámetros"}
            )
        
        similar_movements = []
        threshold = 0.65
        
        for file_hash in active_files:
            if file_hash in uploaded_files_registry:
                file_info = uploaded_files_registry[file_hash]
                filename = file_info['nombre']
                file_path = PROCESSED_DIR / filename
                
                if file_path.exists():
                    try:
                        if filename.lower().endswith('.pdf'):
                            movements = file_reader.read_pdf(str(file_path))
                        else:
                            movements = file_reader.read_xlsx(str(file_path))
                        
                        # ✅ GENERAR IDs ÚNICOS
                        movements = enrich_movements_with_ids(movements, filename)
                        
                        if not movements:
                            continue
                        
                        for mov in movements:
                            mov_id = mov.get('id')
                            
                            if mov_id == movement_id:
                                continue
                            
                            mov_descripcion = mov.get('descripcion', '').lower().strip()
                            input_descripcion = descripcion.lower().strip()
                            
                            if mov_descripcion == input_descripcion:
                                similar_movements.append({
                                    "id": mov_id,
                                    "descripcion": mov.get('descripcion'),
                                    "fecha": mov.get('fecha'),
                                    "monto": mov.get('monto'),
                                    "categoria_actual": mov.get('categoria', 'Sin Categoría'),
                                    "subcategoria_actual": mov.get('subcategoria', 'Sin Subcategoría'),
                                    "similitud": 100.0,
                                    "tipo_similitud": "Exacta"
                                })
                            else:
                                similarity = SequenceMatcher(
                                    None,
                                    input_descripcion,
                                    mov_descripcion
                                ).ratio()
                                
                                if similarity >= threshold:
                                    similar_movements.append({
                                        "id": mov_id,
                                        "descripcion": mov.get('descripcion'),
                                        "fecha": mov.get('fecha'),
                                        "monto": mov.get('monto'),
                                        "categoria_actual": mov.get('categoria', 'Sin Categoría'),
                                        "subcategoria_actual": mov.get('subcategoria', 'Sin Subcategoría'),
                                        "similitud": round(similarity * 100, 1),
                                        "tipo_similitud": "Parcial"
                                    })
                    
                    except Exception as e:
                        logger.warning(f"⚠️  Error procesando {filename}: {e}")
        
        similar_movements.sort(
            key=lambda x: (x['tipo_similitud'] != 'Exacta', -x['similitud'])
        )
        
        logger.info(f"✅ {len(similar_movements)} similares encontrados para: '{descripcion}'")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "original": {
                    "id": movement_id,
                    "descripcion": descripcion,
                    "categoria": categoria,
                    "subcategoria": subcategoria
                },
                "similares": similar_movements[:50],
                "encontrados": len(similar_movements)
            }
        )
    
    except Exception as e:
        logger.error(f"❌ Error en find_similar: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/movements/batch-categorize")
async def batch_categorize_movements(request: dict):
    """Categoriza múltiples movimientos"""
    global movements_db
    
    try:
        movements_to_update = request.get("movements", [])
        learn = request.get("learn", True)
        
        if not movements_to_update:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Lista vacía"}
            )
        
        logger.info(f"\n🔄 Actualizando {len(movements_to_update)} movimientos")
        
        updated_count = 0
        
        for update_data in movements_to_update:
            mov_id = str(update_data.get('movement_id'))
            categoria = update_data.get('categoria')
            subcategoria = update_data.get('subcategoria')
            descripcion = update_data.get('descripcion', '')
            
            logger.info(f"   ✅ {descripcion[:50]}... → {categoria} / {subcategoria}")
            
            movements_db[mov_id] = {
                'categoria': categoria,
                'subcategoria': subcategoria,
                'descripcion': descripcion,
                'actualizado': datetime.now().isoformat()
            }
            
            if learn and descripcion and categoria:
                try:
                    categorization_service.learn_mapping(
                        pattern=descripcion,
                        categoria=categoria,
                        subcategoria=subcategoria
                    )
                except Exception as e:
                    logger.warning(f"⚠️  Error aprendiendo patrón: {e}")
            
            updated_count += 1
        
        save_movements_db(movements_db)
        logger.info(f"💾 Guardados {updated_count} movimientos en BD")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": f"{updated_count} movimientos categorizados",
                "updated_count": updated_count,
                "learn": learn
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error en batch_categorize: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/movements/categorize")
async def categorize_movement(request: dict):
    """Recategoriza un movimiento individual"""
    try:
        movement_id = request.get("movement_id")
        descripcion = request.get("descripcion", "")
        categoria = request.get("categoria")
        subcategoria = request.get("subcategoria")
        learn = request.get("learn", True)
        
        if not all([movement_id, categoria, subcategoria]):
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Faltan parámetros requeridos"
                }
            )
        
        if learn and descripcion:
            categorization_service.learn_mapping(
                pattern=descripcion,
                categoria=categoria,
                subcategoria=subcategoria
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Movimiento categorizado",
                "movement": {
                    "id": movement_id,
                    "categoria": categoria,
                    "subcategoria": subcategoria,
                    "learned": learn
                }
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/categorization-stats")
async def get_categorization_stats():
    """Retorna estadísticas de categorización"""
    try:
        db_path = Path("backend/data/movements_db.json")
        if not db_path.exists():
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "stats": {
                        "total_movements": 0,
                        "categorized": 0,
                        "uncategorized": 0,
                        "categorization_rate": 0.0
                    }
                }
            )
        
        total = len(movements_db)
        categorized = len([m for m in movements_db.values() if m.get('categoria') and m.get('categoria') != 'Sin Categoría'])
        uncategorized = total - categorized
        rate = (categorized / total * 100) if total > 0 else 0
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "stats": {
                    "total_movements": total,
                    "categorized": categorized,
                    "uncategorized": uncategorized,
                    "categorization_rate": round(rate, 2)
                }
            }
        )
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Error: {str(e)}"
            }
        )

# =====================================================================
# ENDPOINTS DE CATEGORÍAS
# =====================================================================

@app.get("/categories")
async def get_categories():
    """Retorna todas las categorías y subcategorías disponibles"""
    try:
        categories_path = Path("backend/data/categories.json")
        
        if categories_path.exists():
            with open(categories_path, 'r', encoding='utf-8') as f:
                categories_data = json.load(f)
        else:
            all_categories_list = categorization_service.get_all_categories()
            categories_data = {}
            for category in all_categories_list:
                subcats = categorization_service.get_subcategories(category)
                categories_data[category] = subcats
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "categories": categories_data
            }
        )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/categories/add")
async def add_category(request: dict):
    """Agrega una nueva categoría"""
    try:
        categoria = request.get("categoria")
        
        if not categoria:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Falta el nombre de categoría"}
            )
        
        categories_path = Path("backend/data/categories.json")
        
        if categories_path.exists():
            with open(categories_path, 'r', encoding='utf-8') as f:
                categories_data = json.load(f)
        else:
            categories_data = {}
        
        if categoria not in categories_data:
            categories_data[categoria] = ["Sin Subcategoría"]
            
            with open(categories_path, 'w', encoding='utf-8') as f:
                json.dump(categories_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Categoría '{categoria}' agregada")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": f"Categoría '{categoria}' agregada",
                    "categoria": categoria
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "La categoría ya existe"}
            )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/categories/delete")
async def delete_category(request: dict):
    """Elimina una categoría"""
    try:
        categoria = request.get("categoria")
        
        if not categoria:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Falta el nombre de categoría"}
            )
        
        categories_path = Path("backend/data/categories.json")
        
        if categories_path.exists():
            with open(categories_path, 'r', encoding='utf-8') as f:
                categories_data = json.load(f)
            
            if categoria in categories_data:
                del categories_data[categoria]
                
                with open(categories_path, 'w', encoding='utf-8') as f:
                    json.dump(categories_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"✅ Categoría '{categoria}' eliminada")
                return JSONResponse(
                    status_code=200,
                    content={"status": "success", "message": f"Categoría '{categoria}' eliminada"}
                )
            else:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": "Categoría no encontrada"}
                )
        else:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "Sin categorías guardadas"}
            )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/categories/add-subcategory")
async def add_subcategory(request: dict):
    """Agrega una subcategoría a una categoría existente"""
    try:
        categoria = request.get("categoria")
        subcategoria = request.get("subcategoria")
        
        if not categoria or not subcategoria:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Faltan parámetros (categoria, subcategoria)"}
            )
        
        categories_path = Path("backend/data/categories.json")
        
        if categories_path.exists():
            with open(categories_path, 'r', encoding='utf-8') as f:
                categories_data = json.load(f)
        else:
            categories_data = {}
        
        if categoria not in categories_data:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": f"Categoría '{categoria}' no existe"}
            )
        
        if subcategoria not in categories_data[categoria]:
            categories_data[categoria].append(subcategoria)
            
            with open(categories_path, 'w', encoding='utf-8') as f:
                json.dump(categories_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Subcategoría '{subcategoria}' agregada a '{categoria}'")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": f"Subcategoría '{subcategoria}' agregada",
                    "categoria": categoria,
                    "subcategoria": subcategoria
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "La subcategoría ya existe en esa categoría"}
            )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/categories/delete-subcategory")
async def delete_subcategory(request: dict):
    """Elimina una subcategoría"""
    try:
        categoria = request.get("categoria")
        subcategoria = request.get("subcategoria")
        
        if not categoria or not subcategoria:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Faltan parámetros"}
            )
        
        if subcategoria == "Sin Subcategoría":
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "No se puede eliminar 'Sin Subcategoría'"}
            )
        
        categories_path = Path("backend/data/categories.json")
        
        if categories_path.exists():
            with open(categories_path, 'r', encoding='utf-8') as f:
                categories_data = json.load(f)
            
            if categoria in categories_data and subcategoria in categories_data[categoria]:
                categories_data[categoria].remove(subcategoria)
                
                with open(categories_path, 'w', encoding='utf-8') as f:
                    json.dump(categories_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"✅ Subcategoría '{subcategoria}' eliminada de '{categoria}'")
                return JSONResponse(
                    status_code=200,
                    content={"status": "success", "message": "Subcategoría eliminada"}
                )
            else:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": "Subcategoría no encontrada"}
                )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)