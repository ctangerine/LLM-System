import React from 'react';
import styles from './ErrorMessage.module.css';

interface ErrorMessageProps {
  message: string;
  onDismiss?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onDismiss }) => {
  return (
    <div className={styles.errorContainer}>
      <div className={styles.errorMessage}>
        <div className={styles.errorIcon}>⚠️</div>
        <div className={styles.errorContent}>
          <span className={styles.errorText}>{message}</span>
        </div>
        {onDismiss && (
          <button 
            className={styles.dismissButton}
            onClick={onDismiss}
            title="Dismiss error"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path
                d="M18 6L6 18M6 6l12 12"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};
