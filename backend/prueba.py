import pdfplumber
from pathlib import Path

# Revisar CMR
pdf_path = Path('processed_files/Cartola_21-72804-7_20250530_20250630.pdf')

if pdf_path.exists():
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()
        print("=== CMR CARTOLA (primeras 80 líneas) ===")
        lines = text.split('\n')
        for i, line in enumerate(lines[:80]):
            print(f"{i}: {line}")
else:
    print(f"Archivo no encontrado: {pdf_path}")