// app/page.tsx

'use client';

import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import { useSocketContext } from '@/hooks/socketContext'; // Import hook từ Context
import { useChat } from '@/hooks/useChat';

import { Header } from '@/components/Header/Header';
import { ChatHistory } from '@/components/ChatHistory/ChatHistory';
import { ChatInput } from '@/components/ChatInput/ChatInput';
import { ErrorMessage } from '@/components/ErrorMessage/ErrorMessage';
import styles from './page.module.css';

export default function Home() {
  const [conversationId, setConversationId] = useState<string>('');
  const [isInitializing, setIsInitializing] = useState<boolean>(true);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const router = useRouter();

  // 1. Lấy instance socket duy nhất từ Context
  const { socket } = useSocketContext();

  // 2. Truyền socket và conversationId vào useChat
  // Mọi logic về chat (gửi/nhận) giờ đây nằm trong hook này
  const { 
    messages, 
    isLoading, 
    error, 
    sendMessage, 
    clearMessages, 
    streamingState 
  } = useChat(socket, conversationId);

  // Check authentication on component mount
  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/login');
        return;
      }
      setIsAuthenticated(true);
    };

    checkAuth();
  }, [router]);

  useEffect(() => {
    const initializeConversation = async () => {
      setIsInitializing(true);
      try {
        const storedId = localStorage.getItem('conversation_id');
        if (storedId) {
          console.log(`Found existing conversation ID in localStorage: ${storedId}`);
          setConversationId(storedId);
          return;
        }

        console.log('No conversation ID found. Creating a new one...');
        const response = await axios.get('http://localhost:8000/');
        const newId = response.data;

        if (newId) {
          console.log(`Created new conversation with ID: ${newId}`);
          setConversationId(newId);
          localStorage.setItem('conversation_id', newId);
        } else {
          throw new Error('API did not return a new conversation ID.');
        }
      } catch (e) {
        console.error('Failed to initialize conversation:', e);
      } finally {
        setIsInitializing(false);
      }
    };

    // Only initialize conversation if authenticated
    if (isAuthenticated) {
      initializeConversation();
    }
  }, [isAuthenticated]); 

  useEffect(() => {
    if (socket && conversationId) {
      console.log(`[Page] Socket and ID are ready. Emitting 'join_room' for ID: ${conversationId}`);
      socket.emit('join_room', { conversation_id: conversationId });
    }
  }, [socket, conversationId]); 

  const handleClearChat = () => {
    clearMessages();
    localStorage.removeItem('conversation_id');
    setConversationId(''); 
    // Tải lại trang để có một phiên làm việc hoàn toàn mới
    window.location.reload();
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('conversation_id');
    router.push('/login');
  };

  // Don't render anything if not authenticated
  if (!isAuthenticated) {
    return <div>Checking authentication...</div>;
  }

  if (isInitializing) {
    return <div>Initializing Conversation...</div>; // Hoặc một component loading đẹp hơn
  }

  return (
    <div className={styles.chatContainer}>
      <Header onClearChat={handleClearChat} onLogout={handleLogout} />
      
      {error && (
        <ErrorMessage message={error} onDismiss={() => { /* logic xóa lỗi */ }} />
      )}
      
      <ChatHistory 
        messages={messages} 
        isLoading={isLoading} 
        streamingState={streamingState}
      />
      
      <ChatInput 
        onSendMessage={sendMessage}
        isLoading={isLoading || streamingState.isProcessing || !!streamingState.currentToken}
      />
    </div>
  );
}