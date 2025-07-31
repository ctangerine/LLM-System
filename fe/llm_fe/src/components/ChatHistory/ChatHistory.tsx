import React, { useEffect, useRef } from 'react';
import { Message as MessageType, StreamingState } from '@/types/chat';
import { Message } from '@/components/Message/Message';
import styles from './ChatHistory.module.css';

interface ChatHistoryProps {
  messages: MessageType[];
  isLoading: boolean;
  streamingState?: StreamingState;
}

export const ChatHistory: React.FC<ChatHistoryProps> = ({ 
  messages, 
  isLoading, 
  streamingState 
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading, streamingState]);

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
        
        {/* Show streaming state when processing or receiving tokens */}
        {streamingState && (streamingState.isProcessing || streamingState.currentToken) && (
          <div className={styles.loadingContainer}>
            <div className={styles.loadingAvatar}>
              <div className={styles.assistantAvatar}>AI</div>
            </div>
            <div className={styles.streamingMessage}>
              {streamingState.isProcessing ? (
                <div className={styles.processingState}>
                  <div className={styles.typingIndicator}>
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <span className={styles.processingText}>Processing your request...</span>
                </div>
              ) : streamingState.currentToken ? (
                <div className={styles.tokenStream}>
                  {streamingState.currentToken}
                  <span className={styles.cursor}>|</span>
                </div>
              ) : null}
            </div>
          </div>
        )}

        {/* Show error state */}
        {streamingState?.error && (
          <div className={styles.loadingContainer}>
            <div className={styles.loadingAvatar}>
              <div className={styles.assistantAvatar}>⚠️</div>
            </div>
            <div className={styles.errorMessage}>
              <span className={styles.errorText}>Error: {streamingState.error}</span>
            </div>
          </div>
        )}
        
        {/* Fallback loading state for backward compatibility */}
        {isLoading && !streamingState && (
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
