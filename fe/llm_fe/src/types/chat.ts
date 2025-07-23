export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export interface ChatResponse {
  message: string;
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}
