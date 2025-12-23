from fastapi import FastAPI, UploadFile, File, status
import os
from fastapi.exceptions import HTTPException
import shutil
from rag.smart_chunking import get_chunked_docs
from rag.chain import store_documents, load_documents, get_rag_chain
from langchain_huggingface import HuggingFaceEmbeddings
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware


embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
upload_dir = "upload"
os.makedirs(upload_dir, exist_ok=True)

app = FastAPI(
    title="Multi_Rag_System_API",
    description="This is Api for Multi Rag System",
    version="V1"
)

# CORS middleware 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track system stats
system_stats = {
    "total_uploads": 0,
    "total_queries": 0,
    "start_time": datetime.now().isoformat()
}

# Info about API
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Multi-Modal RAG System API",
        "version": "v1.0.0",
        "endpoints": {
            "health": "/health",
            "upload": "/upload",
            "query": "/query",
            "stats": "/stats",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check if upload directory exists
        upload_dir_exists = os.path.exists(upload_dir)
        
        # Count uploaded files
        uploaded_files = len([f for f in os.listdir(upload_dir) if f.endswith('.pdf')]) if upload_dir_exists else 0
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "upload_directory": upload_dir_exists,
            "uploaded_documents": uploaded_files,
            "embeddings_model": "sentence-transformers/all-MiniLM-L6-v2"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )
        

# Tracks the System_stats
@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    return {
        "stats": system_stats,
        "uploaded_documents": len([f for f in os.listdir(upload_dir) if f.endswith('.pdf')]),
        "current_time": datetime.now().isoformat()
    }
    

# This Endpoint upload Pdf and store into VectorDatabase
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    chunked_docs = get_chunked_docs(file_path)

    if not chunked_docs:
        raise HTTPException(status_code=500, detail="No content extracted from PDF")

    store_documents(chunked_docs, embeddings)
    
    # INCREMENT THE COUNTER HERE!
    system_stats["total_uploads"] += 1

    return {
        "message": "PDF uploaded and indexed successfully",
        "chunks_created": len(chunked_docs)
    }
    

# This Endpoint Load the VectorDataBase and answer the User question
@app.post('/query')
async def get_response(input: str):
    try:
        vectorstore = load_documents(embedding_model=embeddings)
        retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 3})
        chain = get_rag_chain(retriever)
        response = chain.invoke(input)
        
        # INCREMENT THE COUNTER HERE!
        system_stats["total_queries"] += 1
        
        return {
            "question": input,
            "response": response.content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))