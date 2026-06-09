import { useState, useRef, useEffect } from "react";

const API_BASE = "http://localhost:8000";

const UploadIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
);

const SendIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="22" y1="2" x2="11" y2="13"/>
    <polygon points="22 2 15 22 11 13 2 9 22 2"/>
  </svg>
);

const FileIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
  </svg>
);

const BotIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="11" width="18" height="10" rx="2"/>
    <circle cx="12" cy="5" r="2"/>
    <path d="M12 7v4"/>
    <line x1="8" y1="16" x2="8" y2="16"/>
    <line x1="16" y1="16" x2="16" y2="16"/>
  </svg>
);

const UserIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
);

const PulseLoader = () => (
  <div style={{ display: "flex", gap: "5px", padding: "4px 0", alignItems: "center" }}>
    {[0, 1, 2].map(i => (
      <div key={i} style={{
        width: "7px", height: "7px", borderRadius: "50%",
        background: "#6C8EEF",
        animation: "pulse 1.2s ease-in-out infinite",
        animationDelay: `${i * 0.2}s`
      }} />
    ))}
  </div>
);

export default function RAGSystem() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Hello! Upload a PDF and ask me anything about it. I'll search through your documents to find relevant answers.",
      ts: new Date()
    }
  ]);
  const [input, setInput] = useState("");
  const [isQuerying, setIsQuerying] = useState(false);
  const [uploadState, setUploadState] = useState({ status: "idle", filename: "", chunks: 0, error: "" });
  const [stats, setStats] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [activeTab, setActiveTab] = useState("chat");
  const fileRef = useRef(null);
  const chatEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    fetchStats();
  }, []);

  async function fetchStats() {
    try {
      const res = await fetch(`${API_BASE}/stats`);
      if (res.ok) setStats(await res.json());
    } catch {}
  }

  async function handleUpload(file) {
    if (!file || !file.name.endsWith(".pdf")) {
      setUploadState({ status: "error", filename: "", chunks: 0, error: "Only PDF files are supported." });
      return;
    }
    setUploadState({ status: "uploading", filename: file.name, chunks: 0, error: "" });
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      setUploadState({ status: "success", filename: file.name, chunks: data.chunks_created, error: "" });
      setMessages(prev => [...prev, {
        role: "assistant",
        content: `📄 **${file.name}** indexed successfully — ${data.chunks_created} chunks ready. Ask me anything about it.`,
        ts: new Date()
      }]);
      fetchStats();
    } catch (e) {
      setUploadState({ status: "error", filename: file.name, chunks: 0, error: e.message });
    }
  }

  async function handleQuery() {
    const q = input.trim();
    if (!q || isQuerying) return;
    setMessages(prev => [...prev, { role: "user", content: q, ts: new Date() }]);
    setInput("");
    setIsQuerying(true);
    setMessages(prev => [...prev, { role: "assistant", content: null, ts: new Date() }]);
    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input: q })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Query failed");
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = { role: "assistant", content: data.response, ts: new Date() };
        return updated;
      });
      fetchStats();
    } catch (e) {
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = { role: "assistant", content: `⚠️ ${e.message}`, ts: new Date(), isError: true };
        return updated;
      });
    } finally {
      setIsQuerying(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleQuery();
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  }

  const formatTime = (d) => d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500;600&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #0D0F14; }
        @keyframes pulse {
          0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
          40% { opacity: 1; transform: scale(1); }
        }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .msg-bubble { animation: fadeUp 0.25s ease; }
        textarea:focus { outline: none; }
        button:focus-visible { outline: 2px solid #6C8EEF; outline-offset: 2px; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #2A2D3A; border-radius: 10px; }
      `}</style>

      <div style={{
        fontFamily: "'Inter', sans-serif",
        background: "#0D0F14",
        minHeight: "100vh",
        color: "#E2E4EC",
        display: "flex",
        flexDirection: "column",
        maxWidth: "900px",
        margin: "0 auto",
        padding: "0 16px"
      }}>

        {/* Header */}
        <div style={{
          padding: "20px 0 16px",
          borderBottom: "1px solid #1E2130",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{
              width: "36px", height: "36px",
              background: "linear-gradient(135deg, #3B5BDB 0%, #6C8EEF 100%)",
              borderRadius: "10px",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "18px"
            }}>⚡</div>
            <div>
              <div style={{ fontWeight: 600, fontSize: "15px", letterSpacing: "-0.01em" }}>DocQuery</div>
              <div style={{ fontSize: "11px", color: "#5A5F72", fontFamily: "'IBM Plex Mono', monospace" }}>Multi-RAG System v1</div>
            </div>
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            {["chat", "upload", "stats"].map(tab => (
              <button key={tab} onClick={() => setActiveTab(tab)} style={{
                padding: "6px 14px",
                borderRadius: "8px",
                border: "none",
                cursor: "pointer",
                fontSize: "12px",
                fontWeight: 500,
                fontFamily: "'Inter', sans-serif",
                background: activeTab === tab ? "#1E2130" : "transparent",
                color: activeTab === tab ? "#6C8EEF" : "#5A5F72",
                transition: "all 0.15s"
              }}>
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* CHAT TAB */}
        {activeTab === "chat" && (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", paddingTop: "8px" }}>
            {/* Messages */}
            <div style={{
              flex: 1, overflowY: "auto",
              padding: "8px 0 16px",
              display: "flex", flexDirection: "column", gap: "12px",
              minHeight: "420px", maxHeight: "520px"
            }}>
              {messages.map((msg, i) => (
                <div key={i} className="msg-bubble" style={{
                  display: "flex",
                  flexDirection: msg.role === "user" ? "row-reverse" : "row",
                  alignItems: "flex-start",
                  gap: "10px"
                }}>
                  {/* Avatar */}
                  <div style={{
                    width: "28px", height: "28px",
                    borderRadius: "8px",
                    background: msg.role === "user" ? "#1E2740" : "#141824",
                    border: `1px solid ${msg.role === "user" ? "#2A3A60" : "#1E2130"}`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    flexShrink: 0,
                    color: msg.role === "user" ? "#6C8EEF" : "#4A6FA5"
                  }}>
                    {msg.role === "user" ? <UserIcon /> : <BotIcon />}
                  </div>

                  <div style={{ maxWidth: "75%" }}>
                    <div style={{
                      padding: "10px 14px",
                      borderRadius: msg.role === "user" ? "14px 4px 14px 14px" : "4px 14px 14px 14px",
                      background: msg.role === "user" ? "#1B2545" : "#141824",
                      border: `1px solid ${msg.role === "user" ? "#2A3A60" : "#1E2130"}`,
                      fontSize: "13.5px",
                      lineHeight: "1.6",
                      color: msg.isError ? "#FF6B6B" : "#D4D7E3"
                    }}>
                      {msg.content === null ? <PulseLoader /> : msg.content}
                    </div>
                    <div style={{
                      fontSize: "10px",
                      color: "#3A3F52",
                      marginTop: "4px",
                      textAlign: msg.role === "user" ? "right" : "left",
                      fontFamily: "'IBM Plex Mono', monospace"
                    }}>
                      {formatTime(msg.ts)}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>

            {/* Input bar */}
            <div style={{
              position: "sticky", bottom: 0,
              padding: "12px 0 20px",
              background: "#0D0F14"
            }}>
              <div style={{
                display: "flex",
                alignItems: "flex-end",
                gap: "8px",
                background: "#141824",
                border: "1px solid #1E2130",
                borderRadius: "14px",
                padding: "10px 10px 10px 16px",
                transition: "border-color 0.15s"
              }}
                onFocus={() => {}}
              >
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask something about your documents..."
                  rows={1}
                  style={{
                    flex: 1,
                    background: "transparent",
                    border: "none",
                    color: "#E2E4EC",
                    fontSize: "13.5px",
                    lineHeight: "1.5",
                    resize: "none",
                    fontFamily: "'Inter', sans-serif",
                    maxHeight: "100px",
                    overflowY: "auto"
                  }}
                />
                <button
                  onClick={handleQuery}
                  disabled={!input.trim() || isQuerying}
                  style={{
                    width: "34px", height: "34px",
                    borderRadius: "10px",
                    border: "none",
                    background: input.trim() && !isQuerying ? "#3B5BDB" : "#1E2130",
                    color: input.trim() && !isQuerying ? "#fff" : "#3A3F52",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    cursor: input.trim() && !isQuerying ? "pointer" : "not-allowed",
                    flexShrink: 0,
                    transition: "all 0.15s"
                  }}
                >
                  <SendIcon />
                </button>
              </div>
              <div style={{ fontSize: "11px", color: "#2E3245", textAlign: "center", marginTop: "8px" }}>
                Enter to send · Shift+Enter for new line
              </div>
            </div>
          </div>
        )}

        {/* UPLOAD TAB */}
        {activeTab === "upload" && (
          <div style={{ padding: "24px 0" }}>
            <div
              onDragOver={e => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileRef.current?.click()}
              style={{
                border: `2px dashed ${dragging ? "#3B5BDB" : "#1E2130"}`,
                borderRadius: "16px",
                padding: "48px 24px",
                textAlign: "center",
                cursor: "pointer",
                background: dragging ? "#0F1320" : "transparent",
                transition: "all 0.2s"
              }}
            >
              <div style={{
                width: "52px", height: "52px",
                borderRadius: "14px",
                background: "#141824",
                border: "1px solid #1E2130",
                display: "flex", alignItems: "center", justifyContent: "center",
                margin: "0 auto 16px",
                color: "#3B5BDB"
              }}>
                <UploadIcon />
              </div>
              <div style={{ fontWeight: 600, fontSize: "15px", marginBottom: "6px" }}>
                Drop a PDF here
              </div>
              <div style={{ fontSize: "13px", color: "#5A5F72", marginBottom: "20px" }}>
                or click to browse your files
              </div>
              <div style={{
                display: "inline-block",
                padding: "8px 20px",
                borderRadius: "10px",
                background: "#141824",
                border: "1px solid #1E2130",
                fontSize: "12px",
                color: "#6C8EEF",
                fontFamily: "'IBM Plex Mono', monospace"
              }}>
                .pdf only
              </div>
              <input
                ref={fileRef}
                type="file"
                accept=".pdf"
                style={{ display: "none" }}
                onChange={e => { if (e.target.files[0]) handleUpload(e.target.files[0]); }}
              />
            </div>

            {/* Upload status */}
            {uploadState.status !== "idle" && (
              <div style={{
                marginTop: "16px",
                padding: "14px 16px",
                borderRadius: "12px",
                background: "#141824",
                border: `1px solid ${
                  uploadState.status === "success" ? "#1A3A2A" :
                  uploadState.status === "error" ? "#3A1A1A" : "#1E2130"
                }`,
                display: "flex",
                alignItems: "center",
                gap: "12px"
              }}>
                {uploadState.status === "uploading" && (
                  <div style={{
                    width: "18px", height: "18px", borderRadius: "50%",
                    border: "2px solid #1E2130",
                    borderTop: "2px solid #6C8EEF",
                    animation: "spin 0.8s linear infinite",
                    flexShrink: 0
                  }} />
                )}
                {uploadState.status === "success" && <div style={{ color: "#4CAF7D", flexShrink: 0 }}>✓</div>}
                {uploadState.status === "error" && <div style={{ color: "#FF6B6B", flexShrink: 0 }}>✗</div>}
                <div>
                  <div style={{ fontSize: "13px", fontWeight: 500, display: "flex", alignItems: "center", gap: "6px" }}>
                    <FileIcon />
                    {uploadState.filename}
                  </div>
                  <div style={{
                    fontSize: "12px",
                    color: uploadState.status === "success" ? "#4CAF7D" : uploadState.status === "error" ? "#FF6B6B" : "#5A5F72",
                    marginTop: "2px"
                  }}>
                    {uploadState.status === "uploading" && "Processing and indexing..."}
                    {uploadState.status === "success" && `${uploadState.chunks} chunks indexed — switch to Chat to start querying`}
                    {uploadState.status === "error" && uploadState.error}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* STATS TAB */}
        {activeTab === "stats" && (
          <div style={{ padding: "24px 0" }}>
            {stats ? (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                {[
                  { label: "Total Uploads", value: stats.stats?.total_uploads ?? 0, unit: "documents", accent: "#3B5BDB" },
                  { label: "Total Queries", value: stats.stats?.total_queries ?? 0, unit: "questions answered", accent: "#6C8EEF" },
                  { label: "Indexed PDFs", value: stats.uploaded_documents ?? 0, unit: "files on disk", accent: "#4A6FA5" },
                  {
                    label: "Uptime Since",
                    value: stats.stats?.start_time ? new Date(stats.stats.start_time).toLocaleDateString() : "—",
                    unit: "system start",
                    accent: "#2A4A80",
                    isText: true
                  }
                ].map(({ label, value, unit, accent, isText }) => (
                  <div key={label} style={{
                    padding: "20px",
                    borderRadius: "14px",
                    background: "#141824",
                    border: "1px solid #1E2130",
                    borderLeft: `3px solid ${accent}`
                  }}>
                    <div style={{ fontSize: "11px", color: "#5A5F72", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                      {label}
                    </div>
                    <div style={{
                      fontSize: isText ? "18px" : "28px",
                      fontWeight: 600,
                      color: "#E2E4EC",
                      fontFamily: "'IBM Plex Mono', monospace",
                      letterSpacing: "-0.02em",
                      marginBottom: "4px"
                    }}>
                      {value}
                    </div>
                    <div style={{ fontSize: "11px", color: "#3A3F52" }}>{unit}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: "center", color: "#3A3F52", padding: "48px 0", fontSize: "13px" }}>
                Loading stats...
              </div>
            )}

            <div style={{
              marginTop: "16px",
              padding: "14px 16px",
              borderRadius: "12px",
              background: "#141824",
              border: "1px solid #1E2130",
              fontSize: "12px",
              color: "#3A3F52",
              fontFamily: "'IBM Plex Mono', monospace"
            }}>
              API · {API_BASE} · sentence-transformers/all-MiniLM-L6-v2
            </div>
          </div>
        )}

      </div>
    </>
  );
}