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

def register_uploaded_file(file_hash: str, filename: str, movements_count: int, detection: dict = None):
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
    """Guarda el registro de archivos activos"""
    active_file = PROCESSED_DIR / "active_files.json"
    with open(active_file, "w", encoding="utf-8") as f:
        json.dump(list(active_files), f, ensure_ascii=False, indent=2)

def load_active_files():
    """Carga el registro de archivos activos"""
    global active_files
    active_file = PROCESSED_DIR / "active_files.json"
    if active_file.exists():
        with open(active_file, "r", encoding="utf-8") as f:
            active_files = set(json.load(f))

# =====================================================================
# ENDPOINTS - CARGA DE ARCHIVOS
# =====================================================================

@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """Carga múltiples archivos"""
    
    # Validar cantidad de archivos
    if len(files) > MAX_FILES_PER_BATCH:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": f"Máximo {MAX_FILES_PER_BATCH} archivos por carga"
            }
        )
    
    results = []
    
    for file in files:
        try:
            # Validar tamaño
            content = await file.read()
            file_size_mb = len(content) / (1024 * 1024)
            
            if file_size_mb > MAX_FILE_SIZE_MB:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": f"Archivo muy grande ({file_size_mb:.2f}MB > {MAX_FILE_SIZE_MB}MB)"
                })
                continue
            
            # Guardar temporalmente
            temp_path = UPLOAD_DIR / file.filename
            with open(temp_path, "wb") as f:
                f.write(content)
            
            # Calcular hash
            file_hash = calculate_file_hash(temp_path)
            
            # Verificar duplicado
            duplicate_check = is_file_already_uploaded(file_hash)
            if duplicate_check["is_duplicate"]:
                temp_path.unlink()
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "Archivo duplicado",
                    "previous_upload": duplicate_check["file_info"]["fecha_carga"]
                })
                continue
            
            # Detectar tipo de documento
            detection = file_detector.detect(str(temp_path))
            
            # Procesar archivo
            if file.filename.lower().endswith('.pdf'):
                movements = file_reader.read_pdf(str(temp_path))
            elif file.filename.lower().endswith('.xlsx'):
                movements = file_reader.read_xlsx(str(temp_path))
            else:
                temp_path.unlink()
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "Tipo de archivo no soportado"
                })
                continue
            
            # Mover a carpeta procesada
            processed_path = PROCESSED_DIR / file.filename
            shutil.move(str(temp_path), str(processed_path))
            
            # Registrar archivo
            register_uploaded_file(file_hash, file.filename, len(movements), detection)
            active_files.add(file_hash)
            save_active_files()
            
            print(f"✅ Cargado: {file.filename} ({len(movements)} movimientos)")
            
            results.append({
                "filename": file.filename,
                "status": "success",
                "file_hash": file_hash,
                "movements_count": len(movements),
                "detection": detection
            })
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e)
            })
    
    return {
        "status": "success",
        "files_processed": len(results),
        "results": results
    }

# =====================================================================
# ENDPOINTS - GESTIÓN DE ARCHIVOS
# =====================================================================

@app.get("/uploaded-files")
async def get_uploaded_files():
    """Obtiene lista de archivos cargados"""
    load_registry()
    load_active_files()
    
    files_list = []
    for file_hash, file_info in uploaded_files_registry.items():
        file_info["is_active"] = file_hash in active_files
        files_list.append(file_info)
    
    return {
        "status": "success",
        "total_files": len(files_list),
        "active_files": len(active_files),
        "files": files_list
    }

@app.post("/activate-file/{file_hash}")
async def activate_file(file_hash: str):
    """Activa un archivo para análisis"""
    if file_hash not in uploaded_files_registry:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": f"Archivo no encontrado: {file_hash}"}
        )
    
    active_files.add(file_hash)
    save_active_files()
    
    file_info = uploaded_files_registry[file_hash]
    print(f"✅ Activado: {file_info['nombre']}")
    
    return {
        "status": "success",
        "message": f"Archivo activado: {file_info['nombre']}",
        "file_info": file_info
    }

@app.post("/deactivate-file/{file_hash}")
async def deactivate_file(file_hash: str):
    """Desactiva un archivo para análisis"""
    if file_hash not in uploaded_files_registry:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": f"Archivo no encontrado: {file_hash}"}
        )
    
    active_files.discard(file_hash)
    save_active_files()
    
    file_info = uploaded_files_registry[file_hash]
    print(f"❌ Desactivado: {file_info['nombre']}")
    
    return {
        "status": "success",
        "message": f"Archivo desactivado: {file_info['nombre']}",
        "file_info": file_info
    }

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
    """Health check endpoint"""
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
def delete_all_files():
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