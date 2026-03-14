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
  Calendar,
  ArrowLeft
} from 'lucide-react';
import { Link } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Welcome suggestions
const SUGGESTIONS = [
  { icon: GraduationCap, text: "Quero estudar inglês na Irlanda", color: "bg-emerald-100 text-emerald-700 hover:bg-emerald-200" },
  { icon: DollarSign, text: "Qual o custo de um intercâmbio?", color: "bg-amber-100 text-amber-700 hover:bg-amber-200" },
  { icon: MapPin, text: "Me ajude a escolher um destino", color: "bg-blue-100 text-blue-700 hover:bg-blue-200" },
  { icon: FileCheck, text: "Quais documentos preciso?", color: "bg-purple-100 text-purple-700 hover:bg-purple-200" },
];

// Message component
const ChatMessage = ({ message, isUser }) => (
  <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}>
    <div className={`max-w-[85%] md:max-w-[70%] rounded-2xl px-4 py-3 ${
      isUser 
        ? 'bg-gradient-to-r from-sky-500 to-sky-600 text-white rounded-br-md' 
        : 'bg-white text-slate-800 rounded-bl-md shadow-sm border border-slate-100'
    }`}>
      {!isUser && (
        <div className="flex items-center gap-2 mb-2 pb-2 border-b border-slate-100">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-sky-500 to-violet-500 flex items-center justify-center">
            <Sparkles className="w-3 h-3 text-white" />
          </div>
          <span className="text-xs font-semibold text-sky-600">DestinoAI</span>
        </div>
      )}
      <p className="text-sm md:text-base whitespace-pre-wrap leading-relaxed">{message.content}</p>
      <p className={`text-xs mt-2 ${isUser ? 'text-sky-100' : 'text-slate-400'}`}>
        {new Date(message.timestamp).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
      </p>
    </div>
  </div>
);

// Typing indicator
const TypingIndicator = () => (
  <div className="flex justify-start animate-fade-in">
    <div className="bg-white rounded-2xl rounded-bl-md px-4 py-3 shadow-sm border border-slate-100">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-6 h-6 rounded-full bg-gradient-to-br from-sky-500 to-violet-500 flex items-center justify-center">
          <Sparkles className="w-3 h-3 text-white" />
        </div>
        <span className="text-xs font-semibold text-sky-600">DestinoAI</span>
      </div>
      <div className="flex gap-1">
        <span className="w-2 h-2 bg-sky-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
        <span className="w-2 h-2 bg-sky-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
        <span className="w-2 h-2 bg-sky-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
      </div>
    </div>
  </div>
);

export const DestinoAI = () => {
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
      const response = await axios.post(`${API}/destinoai/chat`, {
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
        await axios.delete(`${API}/destinoai/chat/${sessionId}`);
      } catch (error) {
        console.error('Error clearing session:', error);
      }
    }
    setMessages([]);
    setSessionId(null);
    setShowWelcome(true);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-900 via-sky-800 to-violet-900 flex flex-col">
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-md border-b border-white/20 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/" className="p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-all">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center shadow-lg">
              <Plane className="w-5 h-5 text-sky-600" />
            </div>
            <div>
              <h1 className="text-white font-bold text-lg flex items-center gap-2">
                DestinoAI
                <Sparkles className="w-4 h-4 text-amber-300" />
              </h1>
              <p className="text-sky-100 text-xs">Seu consultor de intercâmbio com IA</p>
            </div>
          </div>
          
          {messages.length > 0 && (
            <button
              onClick={startNewChat}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm transition-all"
              data-testid="new-chat-btn"
            >
              <RefreshCw className="w-4 h-4" />
              <span className="hidden sm:inline">Nova conversa</span>
            </button>
          )}
        </div>
      </header>

      {/* Chat Container */}
      <main className="flex-1 max-w-4xl w-full mx-auto flex flex-col p-4">
        <div className="flex-1 bg-slate-50 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
          
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            
            {/* Welcome Screen */}
            {showWelcome && messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center py-8">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-sky-500 to-violet-500 flex items-center justify-center mb-6 shadow-lg">
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
                      className={`flex items-center gap-3 p-3 rounded-xl ${suggestion.color} transition-all text-left group`}
                      data-testid={`suggestion-${index}`}
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
          <div className="border-t border-slate-200 p-4 bg-white">
            <form onSubmit={handleSubmit} className="flex gap-3">
              <div className="flex-1 relative">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Digite sua mensagem..."
                  disabled={isLoading}
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-sky-400 focus:ring-2 focus:ring-sky-100 outline-none transition-all text-slate-700 placeholder:text-slate-400 disabled:bg-slate-100"
                  data-testid="chat-input"
                />
                <MessageCircle className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-300" />
              </div>
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="px-5 py-3 bg-gradient-to-r from-sky-500 to-sky-600 hover:from-sky-600 hover:to-sky-700 text-white rounded-xl font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg shadow-sky-500/30"
                data-testid="send-btn"
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
};
