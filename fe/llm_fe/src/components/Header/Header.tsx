import React from 'react';
import styles from './Header.module.css';

interface HeaderProps {
  onClearChat?: () => void;
  onLogout?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onClearChat, onLogout }) => {
  return (
    <header className={styles.header}>
      <div className={styles.headerContent}>
        <div className={styles.logoSection}>
          <div className={styles.logo}>
            <div className={styles.logoIcon}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 2L15.09 8.26L22 9L17 14L18.18 21L12 17.77L5.82 21L7 14L2 9L8.91 8.26L12 2Z"
                  fill="url(#gradient1)"
                />
                <defs>
                  <linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#667eea" />
                    <stop offset="100%" stopColor="#00d4aa" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <h1 className={styles.title}>Chatbot System</h1>
          </div>
        </div>
        
        <div className={styles.actions}>
          {onClearChat && (
            <button 
              className={styles.clearButton}
              onClick={onClearChat}
              title="Clear conversation"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path
                  d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              Clear Chat
            </button>
          )}
          
          {onLogout && (
            <button 
              className={styles.logoutButton}
              onClick={onLogout}
              title="Logout"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path
                  d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              Logout
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
