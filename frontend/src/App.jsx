import React, { useState, useEffect, useRef } from 'react';
import { Send, Plus, Menu, X, Book, FileText, LogOut, Sun, Moon, User, Upload, Loader2, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// API Configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';

// --- LUXURY DARK THEME CONSTANTS ---
const THEME = {
    bg: 'bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-800 via-gray-950 to-black',
    glass: 'bg-[#1c1c1e]/60 backdrop-blur-3xl border border-white/[0.08] shadow-2xl',
    glassHover: 'hover:bg-[#2c2c2e]/80',
    glassActive: 'bg-[#2c2c2e] border-white/20',
    textPrimary: 'text-white',
    textSecondary: 'text-gray-400',
    accent: 'bg-white text-black hover:bg-gray-200',
    input: 'bg-black/20 border border-white/10 text-white placeholder-gray-500 focus:border-white/30 focus:ring-1 focus:ring-white/30 transition-all',
    modal: 'bg-[#1c1c1e]/90 backdrop-blur-3xl border border-white/10 shadow-2xl text-white'
};

// --- MOCK DATA (Fallback if API fails) ---
const IS_TESTING = false; // Set false để chạy API thật
// --- END MOCK DATA ---

// Auth Context
const AuthContext = React.createContext(null);

const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(null);

  useEffect(() => {
    if (token) {
      fetchUserProfile();
    }
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
        logout(); // Token invalid
      }
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
    }
  };

  const login = async (email, password) => {
    try {
      // Sử dụng endpoint login/json như định nghĩa trong API
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
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  };

  const register = async (email, password, fullName) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: fullName })
      });
      return response.ok;
    } catch (error) {
      console.error('Registration failed:', error);
      return false;
    }
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

// Login Component
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
          setError('');
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
      <div className={`${THEME.glass} rounded-[2rem] p-10 w-full max-w-[400px] transition-all duration-500`}>
        <div className="text-center mb-10">
            <div className="w-12 h-12 bg-white rounded-xl mx-auto mb-6 flex items-center justify-center shadow-[0_0_20px_rgba(255,255,255,0.2)]">
                <Book className="w-6 h-6 text-black" />
            </div>
          <h1 className="text-2xl font-semibold tracking-tight">RAG Intelligence</h1>
          <p className={`mt-2 text-sm ${THEME.textSecondary}`}>Nền tảng học tập thông minh</p>
        </div>

        <div className="space-y-5">
          {!isLogin && (
            <div>
              <input type="text" placeholder="Họ và tên" value={fullName} onChange={(e) => setFullName(e.target.value)} className={`w-full px-5 py-3 rounded-xl outline-none ${THEME.input}`} />
            </div>
          )}
          <div>
            <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleSubmit()} className={`w-full px-5 py-3 rounded-xl outline-none ${THEME.input}`} />
          </div>
          <div>
            <input type="password" placeholder="Mật khẩu" value={password} onChange={(e) => setPassword(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleSubmit()} className={`w-full px-5 py-3 rounded-xl outline-none ${THEME.input}`} />
          </div>

          {error && <p className="text-red-400 text-xs text-center">{error}</p>}

          <button onClick={handleSubmit} disabled={isLoading} className={`w-full py-3.5 rounded-xl font-semibold text-sm tracking-wide transition-all shadow-lg hover:shadow-white/10 active:scale-[0.98] ${THEME.accent} flex items-center justify-center`}>
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : (isLogin ? 'Sign In' : 'Create Account')}
          </button>
        </div>

        <div className="mt-8 text-center">
          <button onClick={() => setIsLogin(!isLogin)} className={`text-sm font-medium transition ${THEME.textSecondary} hover:text-white`}>
            {isLogin ? 'Chưa có tài khoản? Đăng ký ngay' : 'Đã có tài khoản? Đăng nhập'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Main Chat Application
const ChatApp = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  
  // Modals & Upload
  const [showNewSubjectModal, setShowNewSubjectModal] = useState(false);
  const [showNewConversationModal, setShowNewConversationModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [documents, setDocuments] = useState([]);
  
  const messagesEndRef = useRef(null);
  const { token, user, logout } = React.useContext(AuthContext);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (token) fetchSubjects();
  }, [token]);

  useEffect(() => {
    if (selectedSubject) {
      fetchConversations(selectedSubject.id);
      fetchDocuments(selectedSubject.id);
    }
  }, [selectedSubject]);

  useEffect(() => {
    if (selectedConversation) {
      fetchMessages(selectedConversation.id);
    }
  }, [selectedConversation]);

  // Generic API Helper
  const apiCall = async (endpoint, options = {}) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'API call failed');
    }
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
      setConversations([...conversations, data]);
      setSelectedConversation(data);
      setShowNewConversationModal(false);
    } catch (error) { alert('Failed to create conversation'); }
  };

  const handleFileUpload = async (file) => {
    if (!selectedSubject) return;
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/subjects/${selectedSubject.id}/documents`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          // Don't set Content-Type, let browser set multipart/form-data boundary
        },
        body: formData
      });
      
      if (response.ok) {
        await fetchDocuments(selectedSubject.id); // Refresh list
        setShowUploadModal(false);
      } else {
        alert('Upload failed');
      }
    } catch (error) {
      console.error(error);
      alert('Upload error');
    }
  };

  // --- STREAMING CHAT LOGIC ---
  const sendMessage = async () => {
    if (!inputMessage.trim() || !selectedConversation || isStreaming) return;

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
        })
      });

      if (!response.ok) throw new Error('Chat failed');

      // Create a placeholder for assistant message
      const assistantMsg = { role: 'assistant', content: '', created_at: new Date().toISOString() };
      setMessages(prev => [...prev, assistantMsg]);

      // Read the stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') break;
            
            setMessages(prev => {
              const newMsgs = [...prev];
              const lastMsgIndex = newMsgs.length - 1;
              const lastMsg = { ...newMsgs[lastMsgIndex] };
              
              if (lastMsg.role === 'assistant') {
                lastMsg.content += data;
                newMsgs[lastMsgIndex] = lastMsg;
              }
              
              return newMsgs;
            });
          }
        }
      }

    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Lỗi kết nối server.', created_at: new Date().toISOString() }]);
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className={`h-screen flex flex-col ${THEME.bg} text-white font-sans selection:bg-white/20`}>
      {/* Header */}
      <header className={`h-16 flex items-center justify-between px-6 z-10 border-b border-white/[0.06] bg-black/20 backdrop-blur-md`}>
        <div className="flex items-center">
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="mr-4 lg:hidden p-2 rounded-lg hover:bg-white/10 text-white">
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center shadow-lg shadow-white/5">
                <Book className="w-4 h-4 text-black" />
            </div>
            <h1 className="text-lg font-semibold tracking-wide">RAG Chatbot <span className="text-xs font-normal text-gray-500 ml-2 border border-white/10 px-2 py-0.5 rounded-full">PRO</span></h1>
          </div>
        </div>
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-3">
            <div className="text-right hidden sm:block">
                <div className="text-sm font-medium text-white">{user?.full_name || user?.email}</div>
                <div className="text-xs text-gray-500">Premium Plan</div>
            </div>
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-gray-700 to-gray-600 border border-white/10 flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
            </div>
          </div>
          <button onClick={logout} className="text-gray-400 hover:text-white transition">
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className={`w-72 overflow-y-auto transition-all duration-300 ${sidebarOpen ? '' : 'hidden lg:block'} flex-shrink-0 bg-black/20 backdrop-blur-xl border-r border-white/[0.06]`}>
          <div className="p-4 space-y-8">
            {/* Subjects */}
            <div>
              <div className="flex items-center justify-between mb-4 px-2">
                <h2 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Môn học</h2>
                <button onClick={() => setShowNewSubjectModal(true)} className="text-gray-400 hover:text-white transition">
                  <Plus className="w-4 h-4" />
                </button>
              </div>
              <div className="space-y-1">
                {subjects.map(subject => (
                    <button key={subject.id} onClick={() => setSelectedSubject(subject)} className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all duration-200 flex items-center ${selectedSubject?.id === subject.id ? 'bg-white/10 text-white font-medium shadow-sm ring-1 ring-white/5' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}>
                    <span className={`w-2 h-2 rounded-full mr-3 ${selectedSubject?.id === subject.id ? 'bg-blue-500' : 'bg-gray-600'}`}></span>
                    {subject.name}
                    </button>
                ))}
                {subjects.length === 0 && <p className="text-xs text-gray-600 px-3">Chưa có môn học</p>}
              </div>
            </div>

            {/* Conversations */}
            {selectedSubject && (
              <div>
                <div className="flex items-center justify-between mb-4 px-2">
                  <h2 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Hội thoại</h2>
                  <div className="flex space-x-2">
                    <button title="Upload Document" onClick={() => setShowUploadModal(true)} className="text-gray-400 hover:text-white transition">
                      <Upload className="w-4 h-4" />
                    </button>
                    <button title="New Chat" onClick={() => setShowNewConversationModal(true)} className="text-gray-400 hover:text-white transition">
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div className="space-y-1">
                    {conversations.map(conv => (
                    <button key={conv.id} onClick={() => setSelectedConversation(conv)} className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${selectedConversation?.id === conv.id ? 'bg-white/10 text-white font-medium shadow-sm ring-1 ring-white/5' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}>
                        {conv.title}
                    </button>
                    ))}
                     {conversations.length === 0 && <p className="text-xs text-gray-600 px-3">Chưa có hội thoại</p>}
                </div>
              </div>
            )}
          </div>
        </aside>

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col relative">
          {selectedConversation ? (
            <>
              <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                {messages.map((msg, idx) => (
                  <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] lg:max-w-[65%] px-6 py-4 rounded-2xl text-sm leading-relaxed shadow-lg backdrop-blur-sm ${msg.role === 'user' ? 'bg-white text-black font-medium rounded-br-none' : 'bg-[#2c2c2e]/90 text-gray-100 rounded-bl-none border border-white/5'}`}>
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              <div className="p-6">
                <div className={`${THEME.glass} p-2 rounded-2xl flex items-center space-x-3 relative`}>
                  <textarea value={inputMessage} onChange={(e) => setInputMessage(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }} placeholder="Ask anything..." className="flex-1 bg-transparent border-none focus:ring-0 text-white placeholder-gray-500 px-4 py-3 resize-none max-h-32" rows="1" disabled={isStreaming} />
                  <button onClick={sendMessage} disabled={!inputMessage.trim() || isStreaming} className={`p-3 rounded-xl transition-all duration-300 ${!inputMessage.trim() ? 'bg-white/5 text-gray-500' : 'bg-white text-black hover:scale-105 shadow-[0_0_15px_rgba(255,255,255,0.3)]'}`}>
                    {isStreaming ? <Loader2 className="w-5 h-5 animate-spin text-black" /> : <Send className="w-5 h-5" />}
                  </button>
                </div>
                <div className="text-center mt-3">
                    <p className="text-[10px] text-gray-600">AI có thể mắc sai lầm. Hãy kiểm tra thông tin quan trọng.</p>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
              <div className="w-20 h-20 bg-gradient-to-br from-gray-800 to-black rounded-3xl flex items-center justify-center shadow-2xl border border-white/5 mb-6 rotate-3">
                <Book className="w-10 h-10 text-white/80" />
              </div>
              <h2 className="text-3xl font-bold text-white mb-3 tracking-tight">RAG Intelligence</h2>
              <p className="text-gray-400 max-w-md">Chọn một môn học và hội thoại để bắt đầu.</p>
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
    <div className={`${THEME.modal} rounded-2xl p-6 w-full max-w-md animate-in fade-in zoom-in duration-200`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">{title}</h3>
        <button onClick={onClose} className="p-1 rounded-full hover:bg-white/10 transition text-gray-400 hover:text-white">
          <X className="w-5 h-5" />
        </button>
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
      <div>
        <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wide">Tên môn học</label>
        <input type="text" value={name} onChange={(e) => setName(e.target.value)} className={`w-full px-4 py-2.5 rounded-lg outline-none ${THEME.input}`} />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wide">Mô tả</label>
        <textarea value={description} onChange={(e) => setDescription(e.target.value)} className={`w-full px-4 py-2.5 rounded-lg outline-none ${THEME.input}`} rows="3" />
      </div>
      <div className="flex space-x-3 pt-4">
        <button onClick={() => name.trim() && onSubmit(name, description)} className={`flex-1 py-2.5 rounded-lg font-medium transition ${THEME.accent}`}>Tạo mới</button>
        <button onClick={onCancel} className="flex-1 py-2.5 rounded-lg font-medium bg-white/5 hover:bg-white/10 text-white transition">Hủy</button>
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
      <div>
        <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wide">Tiêu đề</label>
        <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} className={`w-full px-4 py-2.5 rounded-lg outline-none ${THEME.input}`} />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wide">Chọn tài liệu tham khảo</label>
        <div className="max-h-40 overflow-y-auto space-y-2 p-2 rounded-lg bg-black/20 border border-white/5">
          {documents.map(doc => (
            <label key={doc.id} className="flex items-center space-x-3 cursor-pointer p-2 rounded hover:bg-white/5 transition group">
              <input type="checkbox" checked={selectedDocs.includes(doc.id)} onChange={() => toggleDocument(doc.id)} className="rounded border-gray-600 bg-transparent text-white focus:ring-0 checked:bg-white checked:border-white" />
              <FileText className="w-4 h-4 text-gray-500 group-hover:text-white transition" />
              <span className="text-sm text-gray-300 group-hover:text-white transition">{doc.filename}</span>
            </label>
          ))}
          {!documents.length && <p className="text-xs text-gray-600 italic px-2">Chưa có tài liệu. Hãy upload trước.</p>}
        </div>
      </div>
      <div className="flex space-x-3 pt-4">
        <button onClick={() => title.trim() && onSubmit(title, selectedDocs)} className={`flex-1 py-2.5 rounded-lg font-medium transition ${THEME.accent}`}>Bắt đầu chat</button>
        <button onClick={onCancel} className="flex-1 py-2.5 rounded-lg font-medium bg-white/5 hover:bg-white/10 text-white transition">Hủy</button>
      </div>
    </div>
  );
};

const UploadForm = ({ onSubmit, onCancel }) => {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleSubmit = async () => {
    if (file) {
      setIsUploading(true);
      await onSubmit(file);
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="border-2 border-dashed border-white/20 rounded-xl p-8 text-center hover:bg-white/5 transition cursor-pointer relative">
        <input type="file" onChange={(e) => setFile(e.target.files[0])} className="absolute inset-0 opacity-0 cursor-pointer" accept=".pdf,.txt,.doc,.docx" />
        <Upload className="w-10 h-10 text-gray-400 mx-auto mb-3" />
        {file ? (
          <p className="text-white font-medium">{file.name}</p>
        ) : (
          <>
            <p className="text-sm text-gray-300 font-medium">Click để chọn file</p>
            <p className="text-xs text-gray-500 mt-1">PDF, TXT, DOCX</p>
          </>
        )}
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