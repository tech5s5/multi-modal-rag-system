from langchain_core.documents import Document
from collections import defaultdict
import re
import pdfplumber
import fitz  # PyMuPDF
import camelot
import pytesseract
from PIL import Image
import io


# -------------------------------
# STEP 1: EXTRACT RAW CONTENT
# -------------------------------
def raw_document_text(pdf_path: str):
    documents = []

    with pdfplumber.open(pdf_path) as pdf:
        doc_fitz = fitz.open(pdf_path)

        for page_index, page in enumerate(pdf.pages, start=1):

            # -------- TEXT --------
            text = page.extract_text()
            if text:
                documents.append({
                    "content": text,
                    "metadata": {
                        "page": page_index,
                        "type": "text"
                    }
                })

            # -------- TABLES --------
            try:
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
            except Exception:
                pass

            # -------- IMAGES + OCR --------
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


# -------------------------------
# STEP 2: RAW → LANGCHAIN DOCS
# -------------------------------
def to_langchain_documents(raw_docs):
    lc_docs = []
    for doc in raw_docs:
        lc_docs.append(
            Document(
                page_content=doc["content"],
                metadata=doc["metadata"]
            )
        )
    return lc_docs


# -------------------------------
# STEP 3: BUILD INVERTED INDEX
# -------------------------------
def build_inverted_index(lc_docs):
    index = defaultdict(set)

    for doc_id, doc in enumerate(lc_docs):
        words = re.findall(r"\b\w+\b", doc.page_content.lower())

        for word in words:
            index[word].add(doc_id)

    return index


# -------------------------------
# STEP 4: RUN PIPELINE
# -------------------------------
if __name__ == "__main__":
    pdf_path = "Report.pdf"  # <-- change path

    raw_docs = raw_document_text(pdf_path)
    lc_docs = to_langchain_documents(raw_docs)
    index = build_inverted_index(lc_docs)

    print(f"Total LangChain Documents: {len(lc_docs)}")
    print(f"Total Indexed Words: {len(index)}")

    # Preview index
    print(dict(list(index.items())[:20]))
