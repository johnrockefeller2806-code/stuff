import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { ScrollArea } from '../components/ui/scroll-area';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Badge } from '../components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';
import { toast } from 'sonner';
import { 
  Send, 
  Smile, 
  Users, 
  Circle, 
  MoreVertical, 
  Trash2, 
  Ban,
  MessageCircle,
  Wifi,
  WifiOff,
  Shield,
  X
} from 'lucide-react';
import EmojiPicker from 'emoji-picker-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const WS_URL = API_URL.replace('https://', 'wss://').replace('http://', 'ws://');

const LOGO_URL = "https://customer-assets.emergentagent.com/job_dublin-study/artifacts/o9gnc0xi_WhatsApp%20Image%202026-01-11%20at%2023.59.07.jpeg";

export const Chat = () => {
  const { user, token, isAdmin } = useAuth();
  const { language } = useLanguage();
  
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [showOnlineUsers, setShowOnlineUsers] = useState(false);
  const [typingUsers, setTypingUsers] = useState([]);
  const [banDialogOpen, setBanDialogOpen] = useState(false);
  const [userToBan, setUserToBan] = useState(null);
  const [banReason, setBanReason] = useState('');
  
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const inputRef = useRef(null);

  // Scroll to bottom when new messages arrive
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Load initial messages
  const loadMessages = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/chat/messages?limit=50`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data);
      }
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  }, []);

  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    if (!token || wsRef.current?.readyState === WebSocket.OPEN) return;
    
    setIsConnecting(true);
    const ws = new WebSocket(`${WS_URL}/api/chat/ws?token=${token}`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setIsConnecting(false);
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'connected':
          setOnlineUsers(data.online_users || []);
          break;
        
        case 'message':
          setMessages(prev => [...prev, data.message]);
          // Show notification if window not focused
          if (document.hidden && data.message.user_id !== user?.id) {
            new Notification(`${data.message.user_name}`, {
              body: data.message.content.substring(0, 100),
              icon: LOGO_URL
            });
          }
          break;
        
        case 'user_joined':
          setOnlineUsers(prev => {
            if (prev.some(u => u.user_id === data.user.user_id)) return prev;
            return [...prev, data.user];
          });
          break;
        
        case 'user_left':
          setOnlineUsers(prev => prev.filter(u => u.user_id !== data.user_id));
          break;
        
        case 'message_deleted':
          setMessages(prev => prev.map(msg => 
            msg.id === data.message_id 
              ? { ...msg, content: '[Mensagem removida pelo moderador]', deleted: true }
              : msg
          ));
          break;
        
        case 'typing':
          if (data.user_id !== user?.id) {
            setTypingUsers(prev => {
              if (prev.includes(data.user_name)) return prev;
              return [...prev, data.user_name];
            });
            setTimeout(() => {
              setTypingUsers(prev => prev.filter(name => name !== data.user_name));
            }, 3000);
          }
          break;
        
        case 'banned':
          toast.error(language === 'pt' 
            ? `Você foi banido do chat. Motivo: ${data.reason}` 
            : `You were banned from chat. Reason: ${data.reason}`
          );
          ws.close();
          break;
        
        case 'system':
          setMessages(prev => [...prev, {
            id: `system-${Date.now()}`,
            content: data.content,
            message_type: 'system',
            created_at: data.created_at
          }]);
          break;
        
        case 'error':
          toast.error(data.message);
          break;
        
        default:
          break;
      }
    };
    
    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      setIsConnected(false);
      setIsConnecting(false);
      wsRef.current = null;
      
      // Reconnect after 3 seconds unless banned
      if (event.code !== 4002) {
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, 3000);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnecting(false);
    };
    
    wsRef.current = ws;
  }, [token, user?.id, language]);

  // Initialize chat
  useEffect(() => {
    if (token) {
      loadMessages();
      connectWebSocket();
      
      // Request notification permission
      if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
      }
    }
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [token, loadMessages, connectWebSocket]);

  // Send message
  const sendMessage = (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    
    wsRef.current.send(JSON.stringify({
      type: 'message',
      content: newMessage.trim()
    }));
    
    setNewMessage('');
    setShowEmojiPicker(false);
  };

  // Send typing indicator
  const handleTyping = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      
      wsRef.current.send(JSON.stringify({ type: 'typing' }));
      
      typingTimeoutRef.current = setTimeout(() => {
        typingTimeoutRef.current = null;
      }, 2000);
    }
  };

  // Delete message (admin only)
  const deleteMessage = async (messageId) => {
    try {
      const response = await fetch(
        `${API_URL}/api/chat/messages/${messageId}?token=${token}`,
        { method: 'DELETE' }
      );
      
      if (response.ok) {
        toast.success(language === 'pt' ? 'Mensagem removida' : 'Message deleted');
      } else {
        toast.error(language === 'pt' ? 'Erro ao remover mensagem' : 'Error deleting message');
      }
    } catch (error) {
      console.error('Error deleting message:', error);
      toast.error(language === 'pt' ? 'Erro ao remover mensagem' : 'Error deleting message');
    }
  };

  // Ban user (admin only)
  const banUser = async () => {
    if (!userToBan || !banReason.trim()) return;
    
    try {
      const response = await fetch(`${API_URL}/api/chat/ban?token=${token}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userToBan.user_id,
          reason: banReason,
          duration_hours: 24
        })
      });
      
      if (response.ok) {
        toast.success(language === 'pt' ? 'Usuário banido por 24h' : 'User banned for 24h');
        setBanDialogOpen(false);
        setUserToBan(null);
        setBanReason('');
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Error banning user');
      }
    } catch (error) {
      console.error('Error banning user:', error);
      toast.error(language === 'pt' ? 'Erro ao banir usuário' : 'Error banning user');
    }
  };

  // Add emoji to message
  const onEmojiClick = (emojiData) => {
    setNewMessage(prev => prev + emojiData.emoji);
    inputRef.current?.focus();
  };

  // Get user initials for avatar
  const getInitials = (name) => {
    return name?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || '?';
  };

  // Format time
  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString(language === 'pt' ? 'pt-BR' : 'en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="p-8 text-center">
            <MessageCircle className="h-16 w-16 text-slate-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-slate-900 mb-2">
              {language === 'pt' ? 'Faça login para acessar o chat' : 'Login to access chat'}
            </h2>
            <p className="text-slate-500">
              {language === 'pt' 
                ? 'Você precisa estar logado para participar da comunidade.'
                : 'You need to be logged in to join the community.'}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col" data-testid="chat-page">
      {/* Header - Mobile Optimized */}
      <div className="bg-gradient-to-br from-emerald-900 to-emerald-800 text-white py-4 md:py-6 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 md:px-12 lg:px-24">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 md:p-3 bg-white/10 rounded-xl">
                <MessageCircle className="h-6 w-6 md:h-8 md:w-8" />
              </div>
              <div>
                <h1 className="font-serif text-xl md:text-2xl lg:text-3xl font-bold">
                  {language === 'pt' ? 'Comunidade STUFF' : 'STUFF Community'}
                </h1>
                <p className="text-emerald-200 text-xs md:text-sm hidden sm:block">
                  {language === 'pt' 
                    ? 'Chat para estudantes tirarem dúvidas'
                    : 'Chat for students to ask questions'}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2 md:gap-3">
              {/* Connection status */}
              <div className="flex items-center gap-1 md:gap-2 text-sm">
                {isConnected ? (
                  <Wifi className="h-4 w-4 text-emerald-300" />
                ) : isConnecting ? (
                  <div className="h-4 w-4 border-2 border-emerald-300 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <WifiOff className="h-4 w-4 text-red-300" />
                )}
              </div>
              
              {/* Online users button - Always visible on mobile */}
              <Button
                variant="outline"
                size="sm"
                className="border-white/30 text-white hover:bg-white/10 gap-1 md:gap-2 px-2 md:px-3"
                onClick={() => setShowOnlineUsers(!showOnlineUsers)}
                data-testid="online-users-toggle"
              >
                <Users className="h-4 w-4" />
                <span>{onlineUsers.length}</span>
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 max-w-7xl mx-auto px-2 md:px-6 lg:px-24 py-2 md:py-4 w-full">
        <div className="flex gap-2 md:gap-4 h-[calc(100vh-140px)] md:h-[calc(100vh-180px)]">
          {/* Chat Area */}
          <Card className="flex-1 flex flex-col min-w-0">
            {/* Messages */}
            <ScrollArea className="flex-1 p-2 md:p-4">
              <div className="space-y-3 md:space-y-4">
                {messages.length === 0 ? (
                  <div className="text-center py-12 text-slate-400">
                    <MessageCircle className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>{language === 'pt' ? 'Nenhuma mensagem ainda' : 'No messages yet'}</p>
                    <p className="text-sm">
                      {language === 'pt' ? 'Seja o primeiro a dizer olá!' : 'Be the first to say hello!'}
                    </p>
                  </div>
                ) : (
                  messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex gap-3 ${msg.message_type === 'system' ? 'justify-center' : ''}`}
                      data-testid={`message-${msg.id}`}
                    >
                      {msg.message_type === 'system' ? (
                        <div className="text-xs text-slate-400 bg-slate-100 px-3 py-1 rounded-full">
                          {msg.content}
                        </div>
                      ) : (
                        <>
                          <Avatar className="h-10 w-10 flex-shrink-0 border-2 border-white shadow-sm">
                            <AvatarImage src={msg.user_avatar} alt={msg.user_name} />
                            <AvatarFallback className={msg.is_admin ? 'bg-amber-100 text-amber-700 font-medium' : 'bg-emerald-100 text-emerald-700 font-medium'}>
                              {getInitials(msg.user_name)}
                            </AvatarFallback>
                          </Avatar>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-sm text-slate-900">
                                {msg.user_name}
                              </span>
                              {msg.is_admin && (
                                <Badge variant="outline" className="text-xs border-amber-300 text-amber-600">
                                  <Shield className="h-3 w-3 mr-1" />
                                  Admin
                                </Badge>
                              )}
                              <span className="text-xs text-slate-400">
                                {formatTime(msg.created_at)}
                              </span>
                            </div>
                            
                            <p className={`text-sm ${msg.deleted ? 'text-slate-400 italic' : 'text-slate-700'}`}>
                              {msg.content}
                            </p>
                          </div>
                          
                          {/* Admin actions */}
                          {isAdmin && !msg.deleted && msg.user_id !== user.id && (
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8 opacity-0 group-hover:opacity-100">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem 
                                  onClick={() => deleteMessage(msg.id)}
                                  className="text-red-600"
                                >
                                  <Trash2 className="h-4 w-4 mr-2" />
                                  {language === 'pt' ? 'Remover mensagem' : 'Delete message'}
                                </DropdownMenuItem>
                                <DropdownMenuItem 
                                  onClick={() => {
                                    setUserToBan({ user_id: msg.user_id, user_name: msg.user_name });
                                    setBanDialogOpen(true);
                                  }}
                                  className="text-red-600"
                                >
                                  <Ban className="h-4 w-4 mr-2" />
                                  {language === 'pt' ? 'Banir usuário' : 'Ban user'}
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          )}
                        </>
                      )}
                    </div>
                  ))
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>
            
            {/* Typing indicator */}
            {typingUsers.length > 0 && (
              <div className="px-4 py-2 text-xs text-slate-400">
                {typingUsers.join(', ')} {language === 'pt' ? 'está digitando...' : 'is typing...'}
              </div>
            )}
            
            {/* Message input */}
            <div className="p-4 border-t">
              <form onSubmit={sendMessage} className="flex gap-2">
                <div className="relative flex-1">
                  <Input
                    ref={inputRef}
                    value={newMessage}
                    onChange={(e) => {
                      setNewMessage(e.target.value);
                      handleTyping();
                    }}
                    placeholder={language === 'pt' ? 'Digite sua mensagem...' : 'Type your message...'}
                    className="pr-10"
                    disabled={!isConnected}
                    maxLength={1000}
                    data-testid="chat-input"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8"
                    onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                    data-testid="emoji-button"
                  >
                    <Smile className="h-4 w-4 text-slate-400" />
                  </Button>
                  
                  {/* Emoji picker */}
                  {showEmojiPicker && (
                    <div className="absolute bottom-full right-0 mb-2 z-50">
                      <div className="relative">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="absolute -top-2 -right-2 h-6 w-6 bg-white rounded-full shadow z-10"
                          onClick={() => setShowEmojiPicker(false)}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                        <EmojiPicker 
                          onEmojiClick={onEmojiClick}
                          width={300}
                          height={350}
                          searchPlaceHolder={language === 'pt' ? 'Buscar emoji...' : 'Search emoji...'}
                        />
                      </div>
                    </div>
                  )}
                </div>
                
                <Button 
                  type="submit" 
                  disabled={!isConnected || !newMessage.trim()}
                  className="bg-emerald-600 hover:bg-emerald-500"
                  data-testid="send-button"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </form>
            </div>
          </Card>

          {/* Online Users Sidebar (visible on desktop or when toggled) */}
          <Card className={`w-64 flex-shrink-0 ${showOnlineUsers ? 'block' : 'hidden lg:block'}`}>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Users className="h-4 w-4" />
                {language === 'pt' ? 'Online' : 'Online'} ({onlineUsers.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <ScrollArea className="h-[calc(100vh-400px)] min-h-[300px]">
                <div className="space-y-2">
                  {onlineUsers.map((onlineUser) => (
                    <div 
                      key={onlineUser.user_id}
                      className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 group"
                    >
                      <div className="relative">
                        <Avatar className="h-10 w-10 border-2 border-white shadow-sm">
                          <AvatarImage src={onlineUser.user_avatar} alt={onlineUser.user_name} />
                          <AvatarFallback className={onlineUser.role === 'admin' ? 'bg-amber-100 text-amber-700 text-sm font-medium' : 'bg-emerald-100 text-emerald-700 text-sm font-medium'}>
                            {getInitials(onlineUser.user_name)}
                          </AvatarFallback>
                        </Avatar>
                        <Circle className="absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 fill-emerald-500 text-emerald-500 border-2 border-white rounded-full" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 truncate">
                          {onlineUser.user_name}
                        </p>
                        {onlineUser.role === 'admin' && (
                          <p className="text-xs text-amber-600">Admin</p>
                        )}
                      </div>
                      
                      {/* Admin can ban users from sidebar */}
                      {isAdmin && onlineUser.user_id !== user.id && onlineUser.role !== 'admin' && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 opacity-0 group-hover:opacity-100"
                          onClick={() => {
                            setUserToBan(onlineUser);
                            setBanDialogOpen(true);
                          }}
                        >
                          <Ban className="h-3 w-3 text-slate-400" />
                        </Button>
                      )}
                    </div>
                  ))}
                  
                  {onlineUsers.length === 0 && (
                    <p className="text-sm text-slate-400 text-center py-4">
                      {language === 'pt' ? 'Ninguém online' : 'No one online'}
                    </p>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Ban Dialog */}
      <AlertDialog open={banDialogOpen} onOpenChange={setBanDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {language === 'pt' ? 'Banir usuário' : 'Ban user'}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {language === 'pt' 
                ? `Você está prestes a banir ${userToBan?.user_name} do chat por 24 horas.`
                : `You are about to ban ${userToBan?.user_name} from chat for 24 hours.`}
            </AlertDialogDescription>
          </AlertDialogHeader>
          
          <div className="py-4">
            <Input
              placeholder={language === 'pt' ? 'Motivo do banimento...' : 'Reason for ban...'}
              value={banReason}
              onChange={(e) => setBanReason(e.target.value)}
              data-testid="ban-reason-input"
            />
          </div>
          
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => {
              setUserToBan(null);
              setBanReason('');
            }}>
              {language === 'pt' ? 'Cancelar' : 'Cancel'}
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={banUser}
              disabled={!banReason.trim()}
              className="bg-red-600 hover:bg-red-500"
            >
              {language === 'pt' ? 'Banir' : 'Ban'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
