import pdfplumber
import fitz
import camelot
import pytesseract
from PIL import Image
import io


# Raw Documents
def raw_document_text(pdf_path: str):
    documents = []

    # Open PDF
    with pdfplumber.open(pdf_path) as pdf:
        doc_fitz = fitz.open(pdf_path)

        for page_index, page in enumerate(pdf.pages, start=1):

            # TEXT
            text = page.extract_text()
            if text:
                documents.append({
                    "content": text,
                    "metadata": {
                        "page": page_index,
                        "type": "text"
                    }
                })

            
            # TABLES
            tables = camelot.read_pdf(
                pdf_path,
                pages=str(page_index),
                flavor="stream"
            )

            for t_idx, table in enumerate(tables):
                table_text = table.df.to_string(index=False)
                documents.append({
                    "content": table_text,
                    "metadata": {
                        "page": page_index,
                        "type": "table",
                        "ref": f"Table {t_idx + 1}"
                    }
                })

            
            # IMAGES + OCR
            page_fitz = doc_fitz[page_index - 1]
            images = page_fitz.get_images(full=True)

            for img_idx, img in enumerate(images):
                xref = img[0]
                base_image = doc_fitz.extract_image(xref)
                image_bytes = base_image["image"]

                image = Image.open(io.BytesIO(image_bytes))
                ocr_text = pytesseract.image_to_string(image)

                if ocr_text.strip():
                    documents.append({
                        "content": ocr_text,
                        "metadata": {
                            "page": page_index,
                            "type": "image",
                            "ref": f"Image {img_idx + 1}"
                        }
                    })

    return documents


