from langchain_core.documents import Document


# Raw Documents to Langchain Documents
def get_langchain_docs(docs:str):
    lc_docs = []
    for doc in docs:
        document = Document(
            page_content=doc['content'],
            metadata=doc['metadata']
        )
        lc_docs.append(document)
    return lc_docs

