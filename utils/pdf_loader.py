import fitz

def extract_pdf_pages(file_bytes, filename):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text").strip()
        if text:
            pages.append({"source": filename, "page": i + 1, "text": text})
    return pages
