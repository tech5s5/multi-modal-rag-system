import streamlit as st
import requests
from datetime import datetime
import time
from typing import Optional
import json
import os

# Page configuration
st.set_page_config(
    page_title="Multi-Modal RAG System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        font-weight: 600;
    }
    .upload-section {
        background-color: #f0f2f6;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .query-section {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    .stat-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .success-message {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-message {
        padding: 1rem;
        border-radius: 5px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
    }
    </style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = os.getenv("BACKEND_URL")

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'api_status' not in st.session_state:
    st.session_state.api_status = None
if 'system_stats' not in st.session_state:
    st.session_state.system_stats = None

# Helper functions
def check_api_health() -> Optional[dict]:
    """Check if API is healthy and return status"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None

def get_system_stats() -> Optional[dict]:
    """Fetch system statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            st.session_state.system_stats = data  # Store in session state
            return data
        return None
    except requests.exceptions.RequestException:
        return None

def upload_pdf(file) -> tuple[bool, str, Optional[dict]]:
    """Upload PDF to API"""
    try:
        files = {"file": (file.name, file, "application/pdf")}
        response = requests.post(f"{API_BASE_URL}/upload", files=files, timeout=300)
        
        if response.status_code == 200:
            # Auto-refresh stats after successful upload
            get_system_stats()
            return True, "Success", response.json()
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            return False, f"Error: {error_detail}", None
    except requests.exceptions.Timeout:
        return False, "Request timeout. File may be too large.", None
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}", None

def query_rag(question: str) -> tuple[bool, str]:
    """Query the RAG system"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/query",
            params={"input": question},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            # Auto-refresh stats after successful query
            get_system_stats()
            return True, data.get('response', 'No response')
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            return False, f"Error: {error_detail}"
    except requests.exceptions.Timeout:
        return False, "Query timeout. Please try again."
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"

# Sidebar
with st.sidebar:
    st.title("📚 RAG System")
    st.markdown("---")
    
    # API Status
    st.subheader("🔌 System Status")
    if st.button("Check Connection", use_container_width=True):
        with st.spinner("Checking..."):
            st.session_state.api_status = check_api_health()
            get_system_stats()  # Also fetch stats
    
    if st.session_state.api_status:
        st.success("✅ API Connected")
        with st.expander("Health Details"):
            st.json(st.session_state.api_status)
    elif st.session_state.api_status is None and st.session_state.get('checked', False):
        st.error("❌ API Disconnected")
        st.warning("Make sure FastAPI server is running on http://localhost:8000")
    
    st.markdown("---")
    
    # System Stats - Auto-display
    st.subheader("📊 Statistics")
    
    # Auto-fetch stats if not available
    if st.session_state.system_stats is None:
        get_system_stats()
    
    if st.session_state.system_stats:
        stats_data = st.session_state.system_stats
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📤 Uploads", stats_data.get('stats', {}).get('total_uploads', 0))
            st.metric("📄 Docs", stats_data.get('uploaded_documents', 0))
        with col2:
            st.metric("🔍 Queries", stats_data.get('stats', {}).get('total_queries', 0))
    
    if st.button("🔄 Refresh Stats", use_container_width=True):
        with st.spinner("Refreshing..."):
            stats = get_system_stats()
            if stats:
                st.success("Stats updated!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.warning("Unable to fetch statistics")
    
    st.markdown("---")
    
    # Settings
    st.subheader("⚙️ Settings")
    api_url = st.text_input("API URL", value=API_BASE_URL)
    if api_url != API_BASE_URL:
        API_BASE_URL = api_url
        st.rerun()
    
    # Clear chat history
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# Main content
st.title("🤖 Multi-Modal RAG System")
st.markdown("Upload documents and interact with your intelligent document assistant")

# Create tabs
tab1, tab2, tab3 = st.tabs(["📤 Upload Documents", "💬 Query System", "📈 Dashboard"])

# Tab 1: Upload
with tab1:
    st.header("Upload PDF Documents")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload PDF documents to add to the knowledge base"
        )
        
        if uploaded_file:
            st.info(f"📄 Selected: {uploaded_file.name} ({uploaded_file.size / 1024:.2f} KB)")
            
            if st.button("🚀 Upload and Process", type="primary", use_container_width=True):
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)
                        progress_bar.progress(i + 1)
                    
                    success, message, result = upload_pdf(uploaded_file)
                    
                    if success:
                        st.markdown(f'<div class="success-message">✅ {message}</div>', unsafe_allow_html=True)
                        if result:
                            st.success(f"Created {result.get('chunks_created', 0)} chunks")
                            st.session_state.uploaded_files.append({
                                'name': uploaded_file.name,
                                'size': uploaded_file.size,
                                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                'chunks': result.get('chunks_created', 0)
                            })
                        time.sleep(1)
                        st.rerun()  # Refresh to show updated stats
                    else:
                        st.markdown(f'<div class="error-message">❌ {message}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📋 Upload Guidelines")
        st.markdown("""
        - ✅ Only PDF files supported
        - 📏 Recommended size: < 10MB
        - 🔄 Processing time varies
        - 💾 Documents stored in vector DB
        - 🔍 Automatically indexed for search
        """)
    
    # Upload History
    if st.session_state.uploaded_files:
        st.markdown("---")
        st.subheader("📚 Recently Uploaded")
        
        for idx, file_info in enumerate(reversed(st.session_state.uploaded_files[-5:])):
            with st.expander(f"📄 {file_info['name']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                col1.metric("Size", f"{file_info['size'] / 1024:.2f} KB")
                col2.metric("Chunks", file_info['chunks'])
                col3.metric("Uploaded", file_info['timestamp'].split()[1])

# Tab 2: Query
with tab2:
    st.header("Ask Questions")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        question = st.text_area(
            "Enter your question:",
            height=100,
            placeholder="What would you like to know about your documents?",
            help="Ask questions about the uploaded documents"
        )
    
    with col2:
        st.markdown("### 💡 Tips")
        st.markdown("""
        - Be specific
        - Use keywords
        - Ask one question
        - Reference context
        """)
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        submit_query = st.button("🔍 Ask Question", type="primary", use_container_width=True)
    with col2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    if submit_query and question.strip():
        with st.spinner("Thinking..."):
            success, answer = query_rag(question)
            
            if success:
                st.session_state.chat_history.append({
                    'question': question,
                    'answer': answer,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                time.sleep(0.5)
                st.rerun()  # Refresh to show updated stats
            else:
                st.error(answer)
    
    # Display chat history
    if st.session_state.chat_history:
        st.markdown("---")
        st.subheader("💬 Conversation History")
        
        for idx, chat in enumerate(reversed(st.session_state.chat_history)):
            st.markdown(f'<div class="chat-message user-message"><strong>Q:</strong> {chat["question"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-message bot-message"><strong>A:</strong> {chat["answer"]}</div>', unsafe_allow_html=True)
            st.caption(f"🕐 {chat['timestamp']}")
            st.markdown("---")

# Tab 3: Dashboard
with tab3:
    st.header("System Dashboard")
    
    # Auto-refresh button at top
    if st.button("🔄 Refresh Dashboard", type="primary"):
        get_system_stats()
        check_api_health()
        st.rerun()
    
    col1, col2, col3 = st.columns(3)
    
    # Fetch fresh stats
    stats = st.session_state.system_stats or get_system_stats()
    health = check_api_health()
    
    with col1:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.metric(
            "📄 Total Documents",
            stats.get('uploaded_documents', 0) if stats else "N/A",
            help="Total PDF documents uploaded"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.metric(
            "📤 Total Uploads",
            stats.get('stats', {}).get('total_uploads', 0) if stats else "N/A",
            help="Total upload operations"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.metric(
            "🔍 Total Queries",
            stats.get('stats', {}).get('total_queries', 0) if stats else "N/A",
            help="Total queries processed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏥 System Health")
        if health:
            st.success("System Operational")
            st.json(health)
        else:
            st.error("Unable to connect to API")
    
    with col2:
        st.subheader("⚡ Recent Activity")
        if st.session_state.chat_history:
            st.write(f"Last query: {st.session_state.chat_history[-1]['timestamp']}")
        if st.session_state.uploaded_files:
            st.write(f"Last upload: {st.session_state.uploaded_files[-1]['timestamp']}")
        
        if not st.session_state.chat_history and not st.session_state.uploaded_files:
            st.info("No recent activity")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>Multi-Modal RAG System v1.0.0 | Powered by FastAPI & Streamlit</p>
        <p>🔒 Production Ready | 🚀 High Performance | 💡 Intelligent Search</p>
    </div>
""", unsafe_allow_html=True)