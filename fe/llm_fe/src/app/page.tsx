'use client';

import React, { useEffect } from 'react';
import { Header } from '@/components/Header/Header';
import { ChatHistory } from '@/components/ChatHistory/ChatHistory';
import { ChatInput } from '@/components/ChatInput/ChatInput';
import { ErrorMessage } from '@/components/ErrorMessage/ErrorMessage';
import { useChat } from '@/hooks/useChat';
import styles from './page.module.css';
import { ChatService } from '@/services/chatService';

export default function Home() {
  const { messages, isLoading, error, sendMessage, clearMessages } = useChat();

  useEffect(() => {
    ChatService.getRooms()
      .then(rooms => {
        console.log('Available chat rooms:', rooms);
      })
      .catch(err => {
        console.error('Failed to fetch chat rooms:', err);
      });
  }, []);

  const handleClearError = () => {
    // Error will automatically clear on next successful message
  };

  return (
    <div className={styles.chatContainer}>
      <Header onClearChat={clearMessages} />
      
      {error && (
        <ErrorMessage 
          message={error} 
          onDismiss={handleClearError}
        />
      )}
      
      <ChatHistory 
        messages={messages} 
        isLoading={isLoading} 
      />
      
      <ChatInput 
        onSendMessage={sendMessage}
        isLoading={isLoading}
      />
    </div>
  );
}
