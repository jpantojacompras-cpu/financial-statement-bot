from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import json
from datetime import datetime
import hashlib
from modules.file_reader import FileReader
from modules.file_detector import FileDetector
from modules.categorization_service import CategorizationService

# =====================================================================
# CONFIGURACIÓN
# =====================================================================

app = FastAPI(
    title="Financial Statement Bot",
    description="API para procesar y analizar cartolas bancarias",
    version="1.0.0"
)

# CORS - Solo localhost por ahora
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",      # Frontend Vite
        "http://localhost:3000",      # Alternativa
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
    max_age=3600,
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

PROCESSED_DIR = Path("processed_files")
PROCESSED_DIR.mkdir(exist_ok=True)

# Configuración de carga masiva
MAX_FILES_PER_BATCH = 10  # Máximo de archivos por carga
MAX_FILE_SIZE_MB = 50  # Máximo tamaño por archivo en MB

uploaded_files_registry = {}
active_files = set()
file_reader = FileReader()
file_detector = FileDetector()
categorization_service = CategorizationService()

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
    
    # Agregar información de detección si está disponible
    if detection:
        file_info["institucion"] = detection.get("institution", "unknown")
        file_info["tipo_producto"] = detection.get("product_type", "unknown")
        file_info["deteccion_confianza"] = detection.get("confidence", 0.0)
    
    # ✅ NUEVO: Calcular último mes desde los movimientos
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

# Cargar registros al iniciar
load_registry()
load_active_files()

# =====================================================================
# RUTAS API
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

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Carga un archivo individual"""
    temp_path = None
    try:
        print(f"\n{'='*70}")
        print(f"📁 SOLICITUD DE CARGA INDIVIDUAL")
        print(f"{'='*70}")
        print(f"📄 Archivo: {file.filename}")
        
        # Validar extensión
        allowed_extensions = ['.xlsx', '.xls', '.pdf']
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            print(f"❌ RECHAZO: Extensión no permitida ({file_ext})")
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": f"Formato no permitido. Use: {', '.join(allowed_extensions)}",
                    "file": file.filename
                }
            )
        
        # Guardar temporalmente
        temp_path = UPLOAD_DIR / file.filename
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Validar tamaño
        file_size_mb = temp_path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            temp_path.unlink()
            print(f"❌ Archivo muy grande: {file_size_mb:.2f}MB (máx: {MAX_FILE_SIZE_MB}MB)")
            return JSONResponse(
                status_code=413,
                content={
                    "status": "error",
                    "message": f"Archivo muy grande: {file_size_mb:.2f}MB (máximo: {MAX_FILE_SIZE_MB}MB)",
                    "file": file.filename
                }
            )
        
        print(f"✅ Archivo guardado: {file_size_mb:.2f}MB")
        
        # Calcular hash
        file_hash = calculate_file_hash(temp_path)
        print(f"🔐 Hash: {file_hash[:16]}...")
        
        # Verificar duplicado
        duplicate_check = is_file_already_uploaded(file_hash)
        
        if duplicate_check["is_duplicate"]:
            print(f"⚠️  ARCHIVO DUPLICADO")
            temp_path.unlink()
            
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
        
        print(f"✅ Archivo NUEVO")
        
        # Detectar institución y tipo de producto automáticamente
        print(f"🔍 Detectando instituci��n y tipo de producto...")
        detection = file_detector.detect_from_file(str(temp_path))
        print(f"🏦 Institución detectada: {detection['institution']} (confianza: {detection['confidence']})")
        print(f"💳 Tipo de producto: {detection['product_type']}")
        
        # Procesar
        print(f"🔄 Extrayendo movimientos...")
        movements = []
        
        if file_ext == '.pdf':
            movements = file_reader.read_pdf(str(temp_path))
        else:
            movements = file_reader.read_xlsx(str(temp_path))
        
        # ← AGREGAR AQUÍ (después de extraer)
        from modules.categorization_service import CategorizationService
        categorization_service = CategorizationService()

        for movement in movements:
            categoria, subcategoria = categorization_service.categorize(
                movement['descripcion']
            )
            movement['categoria'] = categoria
            movement['subcategoria'] = subcategoria

        if not movements:
            print(f"❌ Sin movimientos extraídos")
            temp_path.unlink()
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "No se pudieron extraer movimientos del archivo",
                    "file": file.filename
                }
            )
        
        # Agregar información de detección a cada movimiento
        for movement in movements:
            movement['institucion'] = detection['institution']
            movement['tipo_producto'] = detection['product_type']
            movement['deteccion_confianza'] = detection['confidence']
        
        # Registrar y activar
        register_uploaded_file(file_hash, file.filename, len(movements), movements, detection)
        active_files.add(file_hash)
        save_active_files()
        
        processed_path = PROCESSED_DIR / file.filename
        shutil.move(str(temp_path), str(processed_path))
        
        print(f"✅ ÉXITO: {len(movements)} movimientos")
        print(f"🔌 Estado: ACTIVO")
        
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
        print(f"❌ ERROR: {str(e)}")
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
    """Carga múltiples archivos (máximo definido)"""
    print(f"\n{'='*70}")
    print(f"📁 SOLICITUD DE CARGA MASIVA")
    print(f"{'='*70}")
    print(f"📦 Total archivos: {len(files)}")
    
    # Validar cantidad
    if len(files) > MAX_FILES_PER_BATCH:
        print(f"❌ RECHAZO: Demasiados archivos ({len(files)} > {MAX_FILES_PER_BATCH})")
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
        print(f"\n[{idx}/{len(files)}] Procesando: {file.filename}")
        
        temp_path = None
        try:
            # Validar extensión
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ['.xlsx', '.xls', '.pdf']:
                print(f"   ❌ Extensión no permitida")
                results.append({
                    "file": file.filename,
                    "status": "error",
                    "message": "Extensión no permitida",
                    "movements": 0
                })
                errors += 1
                continue
            
            # Guardar temporalmente
            temp_path = UPLOAD_DIR / file.filename
            content = await file.read()
            
            with open(temp_path, "wb") as f:
                f.write(content)
            
            # Validar tamaño
            file_size_mb = temp_path.stat().st_size / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                temp_path.unlink()
                print(f"   ❌ Archivo muy grande ({file_size_mb:.2f}MB)")
                results.append({
                    "file": file.filename,
                    "status": "error",
                    "message": f"Archivo muy grande ({file_size_mb:.2f}MB > {MAX_FILE_SIZE_MB}MB)",
                    "movements": 0
                })
                errors += 1
                continue
            
            print(f"   ✅ Guardado ({file_size_mb:.2f}MB)")
            
            # Calcular hash
            file_hash = calculate_file_hash(temp_path)
            
            # Verificar duplicado
            duplicate_check = is_file_already_uploaded(file_hash)
            if duplicate_check["is_duplicate"]:
                temp_path.unlink()
                print(f"   ⚠️  DUPLICADO")
                results.append({
                    "file": file.filename,
                    "status": "duplicate",
                    "message": "Archivo ya fue cargado",
                    "movements": duplicate_check["file_info"]["movimientos"]
                })
                duplicates += 1
                continue
            
            # Detectar institución y tipo de producto
            print(f"   🔍 Detectando institución y tipo...")
            detection = file_detector.detect_from_file(str(temp_path))
            print(f"   🏦 {detection['institution']} - {detection['product_type']} (confianza: {detection['confidence']})")
            
            # Procesar
            movements = []
            if file_ext == '.pdf':
                movements = file_reader.read_pdf(str(temp_path))
            else:
                movements = file_reader.read_xlsx(str(temp_path))
                
            if not movements:
                temp_path.unlink()
                print(f"   ❌ Sin movimientos")
                results.append({
                    "file": file.filename,
                    "status": "error",
                    "message": "No se extrajeron movimientos",
                    "movements": 0
                })
                errors += 1
                continue
            
            # ← AGREGAR AQUÍ
            for movement in movements:
                categoria, subcategoria = categorization_service.categorize(
                    movement['descripcion']
                )
                movement['categoria'] = categoria
                movement['subcategoria'] = subcategoria

            # Agregar información de detección a cada movimiento
            for movement in movements:
                movement['institucion'] = detection['institution']
                movement['tipo_producto'] = detection['product_type']
                movement['deteccion_confianza'] = detection['confidence']
            
            # Registrar y activar
            register_uploaded_file(file_hash, file.filename, len(movements), movements, detection)
            active_files.add(file_hash)
            save_active_files()
            
            processed_path = PROCESSED_DIR / file.filename
            shutil.move(str(temp_path), str(processed_path))
            
            print(f"   ✅ ÉXITO: {len(movements)} movimientos")
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
            print(f"   ❌ ERROR: {str(e)}")
            if temp_path and temp_path.exists():
                temp_path.unlink()
            
            results.append({
                "file": file.filename,
                "status": "error",
                "message": str(e),
                "movements": 0
            })
            errors += 1
    
    print(f"\n{'='*70}")
    print(f"📊 RESUMEN DE CARGA MASIVA")
    print(f"{'='*70}")
    print(f"✅ Exitosos: {successful}")
    print(f"⚠️  Duplicados: {duplicates}")
    print(f"❌ Errores: {errors}")
    print(f"📈 Total movimientos: {total_movements}")
    print(f"{'='*70}\n")
    
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
        
        # Debug: mostrar archivos en PROCESSED_DIR
        print(f"\n=== DEBUG: Buscando archivos en {PROCESSED_DIR} ===")
        if PROCESSED_DIR.exists():
            archivos_encontrados = list(PROCESSED_DIR.glob("*"))
            print(f"Archivos en directorio: {[f.name for f in archivos_encontrados]}")
        
        print(f"Registro: {list(uploaded_files_registry.keys())}")
        
        # Usar directamente el registro
        for file_hash, file_info in uploaded_files_registry.items():
            print(f"\nProcesando: {file_hash} -> {file_info.get('nombre')}")
            
            # Si no tiene ultimo_mes, calcularlo ahora
            if "ultimo_mes" not in file_info or file_info.get("ultimo_mes") == "N/A":
                try:
                    # Buscar archivo
                    file_path = None
                    nombre_archivo = file_info.get("nombre", "")
                    
                    print(f"  Buscando archivo con nombre: {nombre_archivo}")
                    
                    if PROCESSED_DIR.exists():
                        for f in PROCESSED_DIR.glob("*"):
                            if nombre_archivo in f.name or f.name in nombre_archivo:
                                file_path = f
                                print(f"  ✓ Archivo encontrado: {f.name}")
                                break
                    
                    if not file_path:
                        print(f"  ✗ Archivo NO encontrado")
                        file_info["ultimo_mes"] = "N/A"
                    else:
                        print(f"  Leyendo movimientos...")
                        movements = file_reader.read(str(file_path))
                        print(f"  Movimientos encontrados: {len(movements) if movements else 0}")
                        
                        if movements:
                            fechas = [m.get('fecha') for m in movements if m.get('fecha')]
                            print(f"  Fechas extraídas: {fechas[:3] if fechas else 'ninguna'}...")
                            
                            if fechas:
                                ultima_fecha = max(fechas)
                                mes = ultima_fecha[:7]
                                print(f"  ✓ Última fecha: {ultima_fecha} -> Mes: {mes}")
                                file_info["ultimo_mes"] = mes
                            else:
                                print(f"  Sin fechas válidas")
                                file_info["ultimo_mes"] = "N/A"
                        else:
                            print(f"  Sin movimientos")
                            file_info["ultimo_mes"] = "N/A"
                        
                        save_registry()
                except Exception as e:
                    print(f"  ✗ Error: {e}")
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
        print(f"Error en get_uploaded_files: {e}")
        import traceback
        traceback.print_exc()
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
        
        print(f"✅ Activado: {file_info['nombre']}")
        
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
        
        print(f"⏸️  Desactivado: {file_info['nombre']}")
        
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
        
        print(f"🗑️  Eliminado: {filename}")
        
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
async def get_movements():
    """Retorna movimientos de archivos activos"""
    all_movements = []
    
    print(f"\n📊 Obteniendo movimientos...")
    print(f"   Archivos activos: {len(active_files)} de {len(uploaded_files_registry)}")
    
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
                    
                    if movements:
                        # Agregar información de institución y tipo a cada movimiento
                        for movement in movements:
                            movement['institucion'] = file_info.get('institucion', 'unknown')
                            movement['tipo_producto'] = file_info.get('tipo_producto', 'unknown')
                        
                          # ← AGREGAR AQUÍ (categorizar si no está hecho)
                        for movement in movements:
                            if 'categoria' not in movement or movement.get('categoria') is None:
                                categoria, subcategoria = categorization_service.categorize(
                                    movement['descripcion']
                                )
                                movement['categoria'] = categoria
                                movement['subcategoria'] = subcategoria

                        print(f"   ✅ {filename}: {len(movements)} movimientos")
                        all_movements.extend(movements)
                except Exception as e:
                    print(f"   ❌ {filename}: Error - {e}")
    
    print(f"   Total: {len(all_movements)} movimientos\n")
    
    return {
        "status": "success",
        "total_movimientos": len(all_movements),
        "archivos_activos": len(active_files),
        "movimientos": all_movements
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

# ... resto del código ...

@app.delete("/uploaded-files")
async def delete_all_files():
    """Elimina TODOS los archivos cargados"""
    try:
        global uploaded_files_registry, active_files

        # Eliminar archivos físicos
        if PROCESSED_DIR.exists():
            for file_path in PROCESSED_DIR.glob("*.pdf"):
                file_path.unlink()
            for file_path in PROCESSED_DIR.glob("*.xlsx"):
                file_path.unlink()

        # Limpiar registros
        uploaded_files_registry = {}
        active_files = set()

        # Guardar cambios
        save_registry()
        save_active_files()

        print("\n" + "="*70)
        print("🗑️  TODOS LOS ARCHIVOS HAN SIDO ELIMINADOS")
        print("="*70 + "\n")

        return {
            "status": "success",
            "message": "Todos los archivos han sido eliminados"
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)