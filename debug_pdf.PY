import pdfplumber

pdf_path = 'sample_files/santander-noviembre.pdf'

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    text = page.extract_text()
    print(text)