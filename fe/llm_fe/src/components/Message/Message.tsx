import React from 'react';
import { Message as MessageType } from '@/types/chat';
import styles from './Message.module.css';
import ReactMarkdown from 'react-markdown';

interface MessageProps {
  message: MessageType;
}

export const Message: React.FC<MessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`${styles.messageContainer} ${isUser ? styles.userMessage : styles.assistantMessage}`}>
      <div className={styles.messageAvatar}>
        {isUser ? (
          <div className={styles.userAvatar}>U</div>
        ) : (
          <div className={styles.assistantAvatar}>AI</div>
        )}
      </div>
      <div className={styles.messageContent}>
        <div className={styles.messageText}>
          <ReactMarkdown>
            {message.content}
          </ReactMarkdown>
        </div>
        <div className={styles.messageTime}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
};
