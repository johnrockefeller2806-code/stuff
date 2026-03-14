import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { 
  Send, 
  Plane, 
  GraduationCap, 
  Globe2, 
  Sparkles, 
  MessageCircle,
  RefreshCw,
  MapPin,
  DollarSign,
  FileCheck,
  Calendar
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Welcome suggestions
const SUGGESTIONS = [
  { icon: GraduationCap, text: "Quero estudar inglês na Irlanda", color: "bg-emerald-100 text-emerald-700" },
  { icon: DollarSign, text: "Qual o custo de um intercâmbio?", color: "bg-amber-100 text-amber-700" },
  { icon: MapPin, text: "Me ajude a escolher um destino", color: "bg-blue-100 text-blue-700" },
  { icon: FileCheck, text: "Quais documentos preciso?", color: "bg-purple-100 text-purple-700" },
];

// Message component
const ChatMessage = ({ message, isUser }) => (
  <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-slide-up`}>
    <div className={`max-w-[85%] md:max-w-[70%] rounded-2xl px-4 py-3 ${
      isUser 
        ? 'message-user text-white rounded-br-md' 
        : 'message-assistant text-slate-800 rounded-bl-md shadow-sm'
    }`}>
      {!isUser && (
        <div className="flex items-center gap-2 mb-2 pb-2 border-b border-slate-100">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
            <Sparkles className="w-3 h-3 text-white" />
          </div>
          <span className="text-xs font-semibold text-primary-600">DestinoAI</span>
        </div>
      )}
      <p className="text-sm md:text-base whitespace-pre-wrap leading-relaxed">{message.content}</p>
      <p className={`text-xs mt-2 ${isUser ? 'text-primary-100' : 'text-slate-400'}`}>
        {new Date(message.timestamp).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
      </p>
    </div>
  </div>
);

// Typing indicator
const TypingIndicator = () => (
  <div className="flex justify-start animate-fade-in">
    <div className="message-assistant rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
          <Sparkles className="w-3 h-3 text-white" />
        </div>
        <span className="text-xs font-semibold text-primary-600">DestinoAI</span>
      </div>
      <div className="typing-indicator flex gap-1">
        <span className="w-2 h-2 bg-primary-400 rounded-full"></span>
        <span className="w-2 h-2 bg-primary-400 rounded-full"></span>
        <span className="w-2 h-2 bg-primary-400 rounded-full"></span>
      </div>
    </div>
  </div>
);

// Main App
function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Send message
  const sendMessage = async (text) => {
    if (!text.trim() || isLoading) return;

    setShowWelcome(false);
    const userMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/chat`, {
        session_id: sessionId,
        message: text
      });

      if (!sessionId) {
        setSessionId(response.data.session_id);
      }

      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        timestamp: response.data.timestamp
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Desculpe, tive um problema ao processar sua mensagem. Por favor, tente novamente.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  // Handle submit
  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  // Handle suggestion click
  const handleSuggestion = (text) => {
    sendMessage(text);
  };

  // New chat
  const startNewChat = async () => {
    if (sessionId) {
      try {
        await axios.delete(`${API}/chat/${sessionId}`);
      } catch (error) {
        console.error('Error clearing session:', error);
      }
    }
    setMessages([]);
    setSessionId(null);
    setShowWelcome(true);
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-md border-b border-white/20 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center shadow-lg">
              <Plane className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <h1 className="text-white font-bold text-lg flex items-center gap-2">
                DestinoAI
                <Sparkles className="w-4 h-4 text-amber-300" />
              </h1>
              <p className="text-primary-100 text-xs">Seu consultor de intercâmbio com IA</p>
            </div>
          </div>
          
          {messages.length > 0 && (
            <button
              onClick={startNewChat}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm transition-all"
            >
              <RefreshCw className="w-4 h-4" />
              <span className="hidden sm:inline">Nova conversa</span>
            </button>
          )}
        </div>
      </header>

      {/* Chat Container */}
      <main className="flex-1 max-w-4xl w-full mx-auto flex flex-col">
        <div className="flex-1 chat-container m-4 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
          
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 chat-messages">
            
            {/* Welcome Screen */}
            {showWelcome && messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center py-8 animate-fade-in">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center mb-6 shadow-lg">
                  <Globe2 className="w-10 h-10 text-white" />
                </div>
                
                <h2 className="text-2xl md:text-3xl font-serif font-bold text-slate-800 mb-2 text-center">
                  Olá! Eu sou o DestinoAI 👋
                </h2>
                <p className="text-slate-500 text-center max-w-md mb-8">
                  Seu consultor especialista em intercâmbio. Vou te ajudar a planejar toda a sua jornada de estudos no exterior!
                </p>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg px-4">
                  {SUGGESTIONS.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestion(suggestion.text)}
                      className={`flex items-center gap-3 p-3 rounded-xl ${suggestion.color} hover:scale-105 transition-transform text-left group`}
                    >
                      <suggestion.icon className="w-5 h-5 flex-shrink-0" />
                      <span className="text-sm font-medium">{suggestion.text}</span>
                    </button>
                  ))}
                </div>
                
                <div className="mt-8 flex items-center gap-4 text-xs text-slate-400">
                  <div className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    <span>Planejamento completo</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <DollarSign className="w-3 h-3" />
                    <span>Cálculo de custos</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <FileCheck className="w-3 h-3" />
                    <span>Checklist de docs</span>
                  </div>
                </div>
              </div>
            )}

            {/* Messages */}
            {messages.map((message, index) => (
              <ChatMessage 
                key={index} 
                message={message} 
                isUser={message.role === 'user'} 
              />
            ))}
            
            {/* Typing Indicator */}
            {isLoading && <TypingIndicator />}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-slate-100 p-4 bg-slate-50">
            <form onSubmit={handleSubmit} className="flex gap-3">
              <div className="flex-1 relative">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Digite sua mensagem..."
                  disabled={isLoading}
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-primary-400 focus:ring-2 focus:ring-primary-100 outline-none transition-all text-slate-700 placeholder:text-slate-400 disabled:bg-slate-100"
                />
                <MessageCircle className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-300" />
              </div>
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="px-5 py-3 bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 text-white rounded-xl font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg shadow-primary-500/30"
              >
                <Send className="w-5 h-5" />
                <span className="hidden sm:inline">Enviar</span>
              </button>
            </form>
            <p className="text-center text-xs text-slate-400 mt-3">
              Powered by DestinoAI • GPT-4o • Emergent
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
