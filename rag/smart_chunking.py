from langchain_core.documents import Document
from .combine import raw_document_text
from .lang_doc import get_langchain_docs

# Smart Chunks Documents
def smart_text_chunker(doc, max_chars=500):
    chunks = []
    buffer = ""

    paragraphs = doc.page_content.split("\n\n")

    for para in paragraphs:
        if len(buffer) + len(para) <= max_chars:
            buffer += para + "\n\n"
        else:
            chunks.append(
                Document(
                    page_content=buffer.strip(),
                    metadata=doc.metadata
                )
            )
            buffer = para + "\n\n"

    if buffer.strip():
        chunks.append(
            Document(
                page_content=buffer.strip(),
                metadata=doc.metadata
            )
        )

    return chunks


# Funtion for Raw Documents -> Langchain Document -> Smart Chunking Documents
def get_chunked_docs(pdf:str):
    chunked_docs = []
    docs = raw_document_text(pdf)
    documents = get_langchain_docs(docs)
    for doc in documents:
        doc_type = doc.metadata["type"]
        if doc_type == "text":
            chunked_docs.extend(smart_text_chunker(doc))
        elif doc_type == "table":
            chunked_docs.append(doc)
        elif doc_type == "image":
            chunked_docs.append(doc)
    return chunked_docs
        

        
        



    

    

   


