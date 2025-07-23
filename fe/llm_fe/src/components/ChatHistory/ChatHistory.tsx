import React, { useEffect, useRef } from 'react';
import { Message as MessageType } from '@/types/chat';
import { Message } from '@/components/Message/Message';
import styles from './ChatHistory.module.css';

interface ChatHistoryProps {
  messages: MessageType[];
  isLoading: boolean;
}

export const ChatHistory: React.FC<ChatHistoryProps> = ({ messages, isLoading }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  return (
    <div className={styles.chatHistory} ref={scrollRef}>
      <div className={styles.messagesContainer}>
        {messages.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>✨</div>
            <h2 className={styles.emptyTitle}>Welcome to Chatbot System</h2>
            <p className={styles.emptyDescription}>
              Start a conversation by typing your message below. I'm here to help you with anything you need!
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <Message key={message.id} message={message} />
          ))
        )}
        
        {isLoading && (
          <div className={styles.loadingContainer}>
            <div className={styles.loadingAvatar}>
              <div className={styles.assistantAvatar}>AI</div>
            </div>
            <div className={styles.loadingMessage}>
              <div className={styles.typingIndicator}>
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
