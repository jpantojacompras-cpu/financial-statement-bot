from modules.file_detector import FileDetector
from pathlib import Path

detector = FileDetector()

# Buscar archivos PDF en processed_files
processed_dir = Path("processed_files")

for pdf_file in processed_dir.glob("*.pdf"):
    print(f"\n{'='*70}")
    print(f"🔍 Analizando: {pdf_file.name}")
    print(f"{'='*70}")
    
    detection = detector.detect_from_file(str(pdf_file))
    
    print(f"Institución: {detection['institution']}")
    print(f"Tipo: {detection['product_type']}")
    print(f"Confianza: {detection['confidence']}")
    print(f"Detalles: {detection['details']}")