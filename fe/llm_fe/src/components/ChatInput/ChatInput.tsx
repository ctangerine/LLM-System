import React, { useState, KeyboardEvent } from 'react';
import styles from './ChatInput.module.css';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, isLoading }) => {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    
    // Auto-resize textarea
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px';
  };

  return (
    <div className={styles.chatInputContainer}>
      <div className={styles.inputWrapper}>
        <div className={styles.inputBox}>
          {/* <div className={styles.inputIcon}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"
                fill="url(#gradient2)"
              />
              <defs>
                <linearGradient id="gradient2" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#667eea" />
                  <stop offset="100%" stopColor="#00d4aa" />
                </linearGradient>
              </defs>
            </svg>
          </div> */}
          
          <textarea
            className={styles.textInput}
            placeholder="Type your message here..."
            value={message}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            rows={1}
          />
          
          <button
            className={`${styles.sendButton} ${message.trim() && !isLoading ? styles.active : ''}`}
            onClick={handleSend}
            disabled={!message.trim() || isLoading}
            type="button"
          >
            {isLoading ? (
              <div className={styles.loadingSpinner}>
                <svg width="20" height="20" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="3" fill="currentColor" opacity="0.3">
                    <animate attributeName="r" values="3;3;5;3;3" dur="1s" repeatCount="indefinite" />
                    <animate attributeName="opacity" values="0.3;0.3;1;0.3;0.3" dur="1s" repeatCount="indefinite" />
                  </circle>
                </svg>
              </div>
            ) : (
              <svg 
                width="20" 
                height="20" 
                viewBox="0 0 24 24" 
                fill="none"
                className={styles.sendIcon}
              >
                <path
                  d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"
                  fill="currentColor"
                />
              </svg>
            )}
          </button>
        </div>
        
        <div className={styles.inputFooter}>
          <div className={styles.hint}>
            <span className={styles.hintIcon}>⏎</span>
            <span>Press Enter to send • Shift + Enter for new line</span>
          </div>
        </div>
      </div>
    </div>
  );
};
