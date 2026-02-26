"""
Actualiza el registry JSON con información de detección
"""

import json
from pathlib import Path
from modules.file_detector import FileDetector

detector = FileDetector()
registry_file = Path("processed_files/uploaded_files.json")
processed_dir = Path("processed_files")

# Cargar registry
with open(registry_file, "r", encoding="utf-8") as f:
    registry = json.load(f)

print(f"📋 Actualizando {len(registry)} archivos en el registry...")

for file_hash, file_info in registry.items():
    filename = file_info['nombre']
    file_path = processed_dir / filename
    
    print(f"\n🔍 {filename}")
    
    if file_path.exists():
        try:
            detection = detector.detect_from_file(str(file_path))
            
            file_info['institucion'] = detection['institution']
            file_info['tipo_producto'] = detection['product_type']
            file_info['deteccion_confianza'] = detection['confidence']
            
            print(f"   ✅ {detection['institution']} - {detection['product_type']} ({detection['confidence']*100:.0f}%)")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    else:
        print(f"   ⚠️  Archivo no encontrado")

# Guardar registry actualizado
with open(registry_file, "w", encoding="utf-8") as f:
    json.dump(registry, f, ensure_ascii=False, indent=2)

print(f"\n✅ Registry actualizado!")