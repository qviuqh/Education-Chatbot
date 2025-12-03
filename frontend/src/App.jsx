import React, { useState, useEffect, useRef } from 'react';
import { Send, Plus, Menu, X, Book, FileText, LogOut, User, Upload, Loader2, AlertCircle, Trash2, StopCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

// API Configuration
// const API_BASE_URL = 'http://localhost:8000/api/v1';
// API Configuration
const API_BASE_URL = '/api/v1';


// --- THEME CONSTANTS ---
const THEME = {
    bg: 'bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-800 via-gray-950 to-black',
    glass: 'bg-[#1c1c1e]/60 backdrop-blur-3xl border border-white/[0.08] shadow-2xl',
    input: 'bg-black/20 border border-white/10 text-white placeholder-gray-500 focus:border-white/30 focus:ring-1 focus:ring-white/30 transition-all',
    modal: 'bg-[#1c1c1e]/90 backdrop-blur-3xl border border-white/10 shadow-2xl text-white'
};

// --- ERROR BOUNDARY COMPONENT ---
// Giúp bắt lỗi render để không bị trắng trang
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Rendering Error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <div className="p-4 text-red-400 text-sm bg-red-500/10 rounded-lg">Đã xảy ra lỗi hiển thị tin nhắn.</div>;
    }
    return this.props.children;
  }
}

// --- AUTH CONTEXT ---
const AuthContext = React.createContext(null);

const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(null);

  useEffect(() => {
    if (token) fetchUserProfile();
  }, [token]);

  const fetchUserProfile = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setUser(data);
      } else {
        logout();
      }
    } catch (error) { console.error(error); }
  };

  const login = async (email, password) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login/json`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      if (response.ok) {
        const data = await response.json();
        setToken(data.access_token);
        localStorage.setItem('token', data.access_token);
        return true;
      }
      return false;
    } catch (error) { return false; }
  };

  const register = async (email, password, fullName) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: fullName })
      });
      return response.ok;
    } catch (error) { return false; }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// --- LOGIN PAGE ---
const LoginPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login, register } = React.useContext(AuthContext);

  const handleSubmit = async () => {
    setError('');
    setIsLoading(true);
    try {
      if (isLogin) {
        const success = await login(email, password);
        if (!success) setError('Thông tin đăng nhập không chính xác');
      } else {
        const success = await register(email, password, fullName);
        if (success) {
          setIsLogin(true);
          alert('Đăng ký thành công. Vui lòng đăng nhập.');
        } else {
          setError('Email này có thể đã được sử dụng');
        }
      }
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className={`min-h-screen flex items-center justify-center p-4 ${THEME.bg} font-sans tracking-tight text-white`}>
      <div className={`${THEME.glass} rounded-[2rem] p-10 w-full max-w-[400px]`}>
        <div className="text-center mb-10">
            <div className="w-12 h-12 bg-white rounded-xl mx-auto mb-6 flex items-center justify-center shadow-[0_0_20px_rgba(255,255,255,0.2)]">
                <Book className="w-6 h-6 text-black" />
            </div>
          <h1 className="text-2xl font-semibold tracking-tight">RAG Intelligence</h1>
          <p className="mt-2 text-sm text-gray-400">Nền tảng học tập thông minh</p>
        </div>

        <div className="space-y-5">
          {!isLogin && (
            <input type="text" placeholder="Họ và tên" value={fullName} onChange={(e) => setFullName(e.target.value)} className={`w-full px-5 py-3 rounded-xl outline-none ${THEME.input}`} />
          )}
          <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className={`w-full px-5 py-3 rounded-xl outline-none ${THEME.input}`} />
          <input type="password" placeholder="Mật khẩu" value={password} onChange={(e) => setPassword(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleSubmit()} className={`w-full px-5 py-3 rounded-xl outline-none ${THEME.input}`} />
          
          {error && <p className="text-red-400 text-xs text-center">{error}</p>}

          <button onClick={handleSubmit} disabled={isLoading} className={`w-full py-3.5 rounded-xl font-semibold text-sm tracking-wide transition-all shadow-lg hover:shadow-white/10 active:scale-[0.98] bg-white text-black hover:bg-gray-200 flex items-center justify-center`}>
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : (isLogin ? 'Sign In' : 'Create Account')}
          </button>
        </div>

        <div className="mt-8 text-center">
          <button onClick={() => setIsLogin(!isLogin)} className="text-sm font-medium text-gray-400 hover:text-white transition">
            {isLogin ? 'Chưa có tài khoản? Đăng ký ngay' : 'Đã có tài khoản? Đăng nhập'}
          </button>
        </div>
      </div>
    </div>
  );
};

// --- CHAT APP ---
const ChatApp = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [vectorStatus, setVectorStatus] = useState('ready'); 
  const abortControllerRef = useRef(null);
  
  // Modals
  const [showNewSubjectModal, setShowNewSubjectModal] = useState(false);
  const [showNewConversationModal, setShowNewConversationModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [documents, setDocuments] = useState([]);
  
  const messagesEndRef = useRef(null);
  const { token, logout, user } = React.useContext(AuthContext);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  useEffect(() => {
    if (token) fetchSubjects();
  }, [token]);

  useEffect(() => {
    if (selectedSubject) {
      fetchConversations(selectedSubject.id);
      fetchDocuments(selectedSubject.id);
    }
  }, [selectedSubject]);

  // Polling logic an toàn hơn
  useEffect(() => {
    if (!selectedConversation) return;

    fetchMessages(selectedConversation.id);
    setVectorStatus('checking');

    let isMounted = true;
    let timeoutId;

    const checkStatus = async () => {
        if (!isMounted) return;
        try {
            const response = await fetch(`${API_BASE_URL}/conversations/${selectedConversation.id}/vector-status`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                if (isMounted) {
                    setVectorStatus(data.status);
                    // Nếu chưa ready/error thì check lại sau 2s
                    if (data.status !== 'ready' && data.status !== 'error') {
                        timeoutId = setTimeout(checkStatus, 2000);
                    }
                }
            }
        } catch (e) {
            console.error(e);
        }
    };

    checkStatus();

    return () => {
        isMounted = false;
        clearTimeout(timeoutId);
    };
  }, [selectedConversation]); // Re-run khi chuyển hội thoại

  const apiCall = async (endpoint, options = {}) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    if (response.status === 204) return null;
    if (!response.ok) throw new Error('API call failed');
    return response;
  };

  const fetchSubjects = async () => {
    try {
      const response = await apiCall('/subjects');
      const data = await response.json();
      setSubjects(data);
      if (data.length > 0 && !selectedSubject) setSelectedSubject(data[0]);
    } catch (error) { console.error(error); }
  };

  const fetchConversations = async (subjectId) => {
    try {
      const response = await apiCall(`/subjects/${subjectId}/conversations`);
      const data = await response.json();
      setConversations(data);
    } catch (error) { console.error(error); }
  };

  const fetchMessages = async (conversationId) => {
    try {
      const response = await apiCall(`/conversations/${conversationId}/messages`);
      const data = await response.json();
      setMessages(data);
    } catch (error) { console.error(error); }
  };

  const fetchDocuments = async (subjectId) => {
    try {
      const response = await apiCall(`/subjects/${subjectId}/documents`);
      const data = await response.json();
      setDocuments(data);
    } catch (error) { console.error(error); }
  };

  const createSubject = async (name, description) => {
    try {
      const response = await apiCall('/subjects', {
        method: 'POST',
        body: JSON.stringify({ name, description })
      });
      const data = await response.json();
      setSubjects([...subjects, data]);
      setSelectedSubject(data);
      setShowNewSubjectModal(false);
    } catch (error) { alert('Failed to create subject'); }
  };

  const createConversation = async (title, documentIds) => {
    try {
      const response = await apiCall(`/subjects/${selectedSubject.id}/conversations`, {
        method: 'POST',
        body: JSON.stringify({
          title,
          subject_id: selectedSubject.id,
          document_ids: documentIds
        })
      });
      const data = await response.json();
      setConversations([data, ...conversations]);
      setSelectedConversation(data);
      setShowNewConversationModal(false);
    } catch (error) { alert('Failed to create conversation'); }
  };

  const handleDeleteConversation = async (e, convId) => {
    e.stopPropagation();
    if (!window.confirm("Bạn có chắc muốn xóa hội thoại này?")) return;

    try {
      await apiCall(`/conversations/${convId}`, { method: 'DELETE' });
      setConversations(conversations.filter(c => c.id !== convId));
      if (selectedConversation?.id === convId) {
        setSelectedConversation(null);
        setMessages([]);
      }
    } catch (error) {
      alert("Xóa thất bại");
    }
  };

  const handleFileUpload = async (file) => {
    if (!selectedSubject) return;
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/subjects/${selectedSubject.id}/documents`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      
      if (response.ok) {
        await fetchDocuments(selectedSubject.id);
        setShowUploadModal(false);
      } else { alert('Upload failed'); }
    } catch (error) { alert('Upload error'); }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !selectedConversation || isStreaming || vectorStatus !== 'ready') return;

    // Abort controller để hủy request nếu cần
    abortControllerRef.current = new AbortController();

    const userMsg = { role: 'user', content: inputMessage, created_at: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    setInputMessage('');
    setIsStreaming(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          question: userMsg.content,
          conversation_id: selectedConversation.id
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) throw new Error('Chat failed');

      // Placeholder message
      const assistantMsg = { role: 'assistant', content: '', created_at: new Date().toISOString() };
      setMessages(prev => [...prev, assistantMsg]);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        // Stream decode an toàn
        buffer += decoder.decode(value, { stream: true });
        
        // Xử lý từng dòng data
        const lines = buffer.split('\n\n');
        // Giữ lại phần dư ở cuối buffer (chưa hoàn thành line)
        buffer = lines.pop(); 

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') break;
            
            // Cập nhật state an toàn
            setMessages(prev => {
              if (prev.length === 0) return prev;
              const newMsgs = [...prev];
              const lastMsgIndex = newMsgs.length - 1;
              
              // Chỉ cập nhật nếu tin cuối cùng là assistant
              if (newMsgs[lastMsgIndex].role === 'assistant') {
                const updatedMsg = { ...newMsgs[lastMsgIndex] };
                updatedMsg.content = (updatedMsg.content || "") + data;
                newMsgs[lastMsgIndex] = updatedMsg;
              }
              return newMsgs;
            });
          }
        }
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        setMessages(prev => [...prev, { role: 'assistant', content: 'Lỗi: ' + error.message }]);
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        setIsStreaming(false);
    }
  };

  return (
    <div className={`h-screen flex flex-col ${THEME.bg} text-white font-sans selection:bg-white/20`}>
      <header className="h-16 flex items-center justify-between px-6 z-10 border-b border-white/[0.06] bg-black/20 backdrop-blur-md">
        <div className="flex items-center">
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="mr-4 lg:hidden p-2 rounded-lg hover:bg-white/10 text-white">
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center shadow-lg shadow-white/5">
                <Book className="w-4 h-4 text-black" />
            </div>
            <h1 className="text-lg font-semibold tracking-wide">RAG Chatbot</h1>
          </div>
        </div>
        <div className="flex items-center space-x-4">
            <span className="text-sm hidden sm:block">{user?.full_name}</span>
            <button onClick={logout} className="text-gray-400 hover:text-white transition"><LogOut className="w-5 h-5" /></button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className={`w-72 overflow-y-auto transition-all duration-300 ${sidebarOpen ? '' : 'hidden lg:block'} flex-shrink-0 bg-black/20 backdrop-blur-xl border-r border-white/[0.06]`}>
          <div className="p-4 space-y-8">
            <div>
              <div className="flex items-center justify-between mb-4 px-2">
                <h2 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Môn học</h2>
                <button onClick={() => setShowNewSubjectModal(true)} className="text-gray-400 hover:text-white transition"><Plus className="w-4 h-4" /></button>
              </div>
              <div className="space-y-1">
                {subjects.map(subject => (
                    <button key={subject.id} onClick={() => setSelectedSubject(subject)} className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all duration-200 flex items-center ${selectedSubject?.id === subject.id ? 'bg-white/10 text-white font-medium' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}>
                    <span className={`w-2 h-2 rounded-full mr-3 ${selectedSubject?.id === subject.id ? 'bg-blue-500' : 'bg-gray-600'}`}></span>
                    {subject.name}
                    </button>
                ))}
              </div>
            </div>

            {selectedSubject && (
              <div>
                <div className="flex items-center justify-between mb-4 px-2">
                  <h2 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Hội thoại</h2>
                  <div className="flex space-x-2">
                    <button onClick={() => setShowUploadModal(true)} className="text-gray-400 hover:text-white transition"><Upload className="w-4 h-4" /></button>
                    <button onClick={() => setShowNewConversationModal(true)} className="text-gray-400 hover:text-white transition"><Plus className="w-4 h-4" /></button>
                  </div>
                </div>
                <div className="space-y-1">
                    {conversations.map(conv => (
                    <div key={conv.id} onClick={() => setSelectedConversation(conv)} className={`group w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all duration-200 flex items-center justify-between cursor-pointer ${selectedConversation?.id === conv.id ? 'bg-white/10 text-white font-medium' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}>
                        <span className="truncate flex-1">{conv.title}</span>
                        <button 
                          onClick={(e) => handleDeleteConversation(e, conv.id)} 
                          className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-opacity"
                          title="Xóa hội thoại"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                    </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        </aside>

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col relative">
          {selectedConversation ? (
            <>
              {/* --- Loading Indicator for Vector Store --- */}
              {vectorStatus !== 'ready' && vectorStatus !== 'error' && (
                <div className="absolute top-0 w-full bg-blue-500/10 backdrop-blur-sm border-b border-blue-500/20 px-6 py-2 z-20 flex items-center space-x-2 text-blue-200 text-xs">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  <span>Đang xử lý tài liệu và xây dựng chỉ mục... ({vectorStatus}). Bạn có thể chat sau khi hoàn tất.</span>
                </div>
              )}
              {vectorStatus === 'error' && (
                <div className="absolute top-0 w-full bg-red-500/10 backdrop-blur-sm border-b border-red-500/20 px-6 py-2 z-20 flex items-center space-x-2 text-red-200 text-xs">
                  <AlertCircle className="w-3 h-3" />
                  <span>Lỗi xử lý tài liệu. Vui lòng thử tải lại trang hoặc tạo hội thoại mới.</span>
                </div>
              )}

              <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                {messages.map((msg, idx) => (
                  <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] lg:max-w-[75%] px-6 py-4 rounded-2xl text-sm leading-relaxed shadow-lg backdrop-blur-sm ${msg.role === 'user' ? 'bg-white text-black font-medium rounded-br-none' : 'bg-[#2c2c2e]/90 text-gray-100 rounded-bl-none border border-white/5'}`}>
                      <ErrorBoundary>
                      {msg.role === 'user' ? (
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      ) : (
                        /* Manual CSS for Markdown since no Tailwind Typography */
                        <ReactMarkdown 
                          components={{
                            p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
                            ul: ({node, ...props}) => <ul className="list-disc pl-4 mb-2 space-y-1" {...props} />,
                            ol: ({node, ...props}) => <ol className="list-decimal pl-4 mb-2 space-y-1" {...props} />,
                            li: ({node, ...props}) => <li className="pl-1" {...props} />,
                            h1: ({node, ...props}) => <h1 className="text-xl font-bold mb-2 mt-4" {...props} />,
                            h2: ({node, ...props}) => <h2 className="text-lg font-bold mb-2 mt-3" {...props} />,
                            h3: ({node, ...props}) => <h3 className="text-base font-bold mb-1 mt-2" {...props} />,
                            strong: ({node, ...props}) => <strong className="font-bold text-white" {...props} />,
                            em: ({node, ...props}) => <em className="italic text-gray-300" {...props} />,
                            code: ({node, inline, className, children, ...props}) => {
                                return inline ? 
                                (<code className="bg-black/30 rounded px-1 py-0.5 text-pink-300 font-mono text-xs" {...props}>{children}</code>) :
                                (<pre className="bg-black/50 border border-white/10 rounded-lg p-3 my-2 overflow-x-auto"><code className="text-xs font-mono text-gray-200" {...props}>{children}</code></pre>)
                            }
                          }}
                        >
                          {msg.content || ''}
                        </ReactMarkdown>
                      )}
                      </ErrorBoundary>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              <div className="p-6">
                <div className={`${THEME.glass} p-2 rounded-2xl flex items-center space-x-3 relative`}>
                  <textarea 
                    value={inputMessage} 
                    onChange={(e) => setInputMessage(e.target.value)} 
                    onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }} 
                    placeholder={vectorStatus === 'ready' ? "Hỏi gì đó về tài liệu..." : "Đang xử lý tài liệu..."}
                    className="flex-1 bg-transparent border-none focus:ring-0 text-white placeholder-gray-500 px-4 py-3 resize-none max-h-32 disabled:opacity-50" 
                    rows="1" 
                    disabled={isStreaming || vectorStatus !== 'ready'} 
                  />
                  {isStreaming ? (
                    <button onClick={handleStop} className="p-3 rounded-xl bg-red-500/80 hover:bg-red-500 text-white transition-all shadow-lg hover:shadow-red-500/20">
                        <StopCircle className="w-5 h-5" />
                    </button>
                  ) : (
                    <button 
                        onClick={sendMessage} 
                        disabled={!inputMessage.trim() || vectorStatus !== 'ready'} 
                        className={`p-3 rounded-xl transition-all duration-300 ${(!inputMessage.trim() || vectorStatus !== 'ready') ? 'bg-white/5 text-gray-500' : 'bg-white text-black hover:scale-105'}`}
                    >
                        <Send className="w-5 h-5" />
                    </button>
                  )}
                </div>
                <div className="text-center mt-3">
                    <p className="text-[10px] text-gray-600">AI có thể mắc sai lầm. Hãy kiểm tra thông tin quan trọng.</p>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
              <h2 className="text-3xl font-bold text-white mb-3">RAG Intelligence</h2>
              <p className="text-gray-400">Chọn một hội thoại để bắt đầu.</p>
            </div>
          )}
        </main>
      </div>

      {/* Modals */}
      {showNewSubjectModal && (
        <Modal title="Môn học mới" onClose={() => setShowNewSubjectModal(false)}>
          <NewSubjectForm onSubmit={createSubject} onCancel={() => setShowNewSubjectModal(false)} />
        </Modal>
      )}
      {showNewConversationModal && (
        <Modal title="Hội thoại mới" onClose={() => setShowNewConversationModal(false)}>
          <NewConversationForm documents={documents} onSubmit={createConversation} onCancel={() => setShowNewConversationModal(false)} />
        </Modal>
      )}
      {showUploadModal && (
        <Modal title="Upload Tài liệu" onClose={() => setShowUploadModal(false)}>
          <UploadForm onSubmit={handleFileUpload} onCancel={() => setShowUploadModal(false)} />
        </Modal>
      )}
    </div>
  );
};

// --- SUB-COMPONENTS ---
const Modal = ({ title, children, onClose }) => (
  <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
    <div className={`${THEME.modal} rounded-2xl p-6 w-full max-w-md`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">{title}</h3>
        <button onClick={onClose} className="p-1 rounded-full hover:bg-white/10 text-gray-400 hover:text-white"><X className="w-5 h-5" /></button>
      </div>
      {children}
    </div>
  </div>
);

const NewSubjectForm = ({ onSubmit, onCancel }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  return (
    <div className="space-y-4">
      <input type="text" placeholder="Tên môn học" value={name} onChange={(e) => setName(e.target.value)} className={`w-full px-4 py-2.5 rounded-lg outline-none ${THEME.input}`} />
      <textarea placeholder="Mô tả" value={description} onChange={(e) => setDescription(e.target.value)} className={`w-full px-4 py-2.5 rounded-lg outline-none ${THEME.input}`} rows="3" />
      <div className="flex space-x-3 pt-4">
        <button onClick={() => name.trim() && onSubmit(name, description)} className={`flex-1 py-2.5 rounded-lg font-medium transition ${THEME.accent}`}>Tạo mới</button>
        <button onClick={onCancel} className={`flex-1 py-2.5 rounded-lg font-medium bg-white/5 hover:bg-white/10 text-white transition`}>Hủy</button>
      </div>
    </div>
  );
};

const NewConversationForm = ({ documents, onSubmit, onCancel }) => {
  const [title, setTitle] = useState('');
  const [selectedDocs, setSelectedDocs] = useState([]);
  const toggleDocument = (id) => setSelectedDocs(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);

  return (
    <div className="space-y-4">
      <input type="text" placeholder="Tiêu đề" value={title} onChange={(e) => setTitle(e.target.value)} className={`w-full px-4 py-2.5 rounded-lg outline-none ${THEME.input}`} />
      <div className="max-h-40 overflow-y-auto space-y-2 p-2 rounded-lg bg-black/20 border border-white/5">
        {documents.map(doc => (
          <label key={doc.id} className="flex items-center space-x-3 cursor-pointer p-2 rounded hover:bg-white/5 transition group">
            <input type="checkbox" checked={selectedDocs.includes(doc.id)} onChange={() => toggleDocument(doc.id)} className="rounded border-gray-600 bg-transparent text-white focus:ring-0" />
            <span className="text-sm text-gray-300">{doc.filename}</span>
          </label>
        ))}
      </div>
      <div className="flex space-x-3 pt-4">
        <button onClick={() => title.trim() && onSubmit(title, selectedDocs)} className={`flex-1 py-2.5 rounded-lg font-medium transition ${THEME.accent}`}>Bắt đầu</button>
        <button onClick={onCancel} className="flex-1 py-2.5 rounded-lg font-medium bg-white/5 hover:bg-white/10 text-white transition">Hủy</button>
      </div>
    </div>
  );
};

const UploadForm = ({ onSubmit, onCancel }) => {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const handleSubmit = async () => { if (file) { setIsUploading(true); await onSubmit(file); setIsUploading(false); } };

  return (
    <div className="space-y-6">
      <div className="border-2 border-dashed border-white/20 rounded-xl p-8 text-center hover:bg-white/5 cursor-pointer relative">
        <input type="file" onChange={(e) => setFile(e.target.files[0])} className="absolute inset-0 opacity-0 cursor-pointer" accept=".pdf,.txt,.doc,.docx" />
        <Upload className="w-10 h-10 text-gray-400 mx-auto mb-3" />
        <p className="text-white font-medium">{file ? file.name : "Click để chọn file"}</p>
      </div>
      <div className="flex space-x-3">
        <button onClick={handleSubmit} disabled={!file || isUploading} className={`flex-1 py-2.5 rounded-lg font-medium transition ${THEME.accent} flex items-center justify-center`}>
          {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Upload'}
        </button>
        <button onClick={onCancel} className="flex-1 py-2.5 rounded-lg font-medium bg-white/5 hover:bg-white/10 text-white transition">Hủy</button>
      </div>
    </div>
  );
};

const App = () => (
  <AuthProvider>
    <AuthContext.Consumer>
      {({ token }) => token ? <ChatApp /> : <LoginPage />}
    </AuthContext.Consumer>
  </AuthProvider>
);

export default App;