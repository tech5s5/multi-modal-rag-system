from langchain_groq import ChatGroq
from .smart_chunking import get_chunked_docs
from langchain_core.documents import Document
from typing import List
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import os
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate

VECTOR_PATH = "vectorstore/faiss_index"

llm = ChatGroq(model="llama-3.3-70b-versatile")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


# This funtion include page_content + metadata fot better retrieval
def format_docs_with_metadata(docs):
    formatted = []
    for d in docs:
        meta = d.metadata
        citation = f"(Page {meta.get('page')}"
        if meta.get("ref"):
            citation += f", {meta.get('ref')}"
        citation += ")"

        formatted.append(
            f"{citation}\n{d.page_content}"
        )
    return "\n\n".join(formatted)


# Funtion For Storing Documents into VectorDatabase
def store_documents(docs:List[Document],embedding_model:str):
    vectorstore = FAISS.from_documents(docs,embedding=embedding_model)
    vectorstore.save_local(VECTOR_PATH)
    return vectorstore

# Funtion to load VectorDatabase for Retrieval Process
def load_documents(embedding_model:str):
    if not os.path.exists(VECTOR_PATH):
        raise ValueError("Vectorstore not found,Upload Your Document First")
    return FAISS.load_local(VECTOR_PATH,embeddings=embedding_model,allow_dangerous_deserialization=True)
    

# Prompt for LLM to execute Your task more efficiently
prompt = ChatPromptTemplate.from_template(
    """You are a professional research analyst.

Answer the question strictly using the information contained in the document excerpts below.
Do not mention the phrases "provided context", "given context", or similar meta-references.
Do not include conversational language or assumptions.

Writing guidelines:
- Use a formal, neutral, and analytical tone.
- Present information directly and concisely.
- If information is missing, clearly state that it is not available in the document.
- Do not speculate or add external knowledge.

Citation rules:
- List citations in a separate section highlighted with blue.
- Each citation must include page number and table/figure/image reference if available.
- Use this format exactly:
  • Page X, Table/Figure/Image Y (if applicable)

<Document Excerpts>
{context}
</Document Excerpts>

Question:
{input}
"""
)

# Get Retrieval chain
def get_rag_chain(retriever):
    chain = (
    {
        "context": retriever | format_docs_with_metadata,
        "input": RunnablePassthrough()
    }
    |prompt
    |llm
    )
    return chain



