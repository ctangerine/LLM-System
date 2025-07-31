export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  isStreaming?: boolean;
  isComplete?: boolean;
}

export interface ChatResponse {
  message: string;
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  conversation?: string;
}

export interface StreamingState {
  isProcessing: boolean;
  currentToken: string;
  error?: string;
}
