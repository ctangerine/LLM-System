import { ChatRequest, ChatResponse } from '@/types/chat';
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';


export class ChatService {
  static async getRooms(): Promise<any> {
    try {
      const response = await axios.get(`${API_BASE_URL}/`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = response.data;
      console.log('Chat rooms data:', data);

      if (data.new_conversation_id) {
        console.log('New conversation ID:', data.new_conversation_id);
        localStorage.setItem('conversation_id', data.new_conversation_id);
      } else {
        console.warn('new_conversation_id not found in response');
      }

      return data;
    } catch (error) {
      console.error('Error fetching chat rooms:', error);
      throw new Error('Failed to fetch chat rooms.');
    }
  }

  static async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      console.log('Sending message to API:', request);
      console.log('API endpoint:', `${API_BASE_URL}/api/chat`);
      
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      console.log('Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Response data:', data);
      return data;
    } catch (error) {
      console.error('Error sending message:', error);
      throw new Error('Failed to send message. Please try again.');
    }
  }

  static async getConversationHistory(conversationId: string): Promise<ChatResponse[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching conversation history:', error);
      throw new Error('Failed to fetch conversation history.');
    }
  }
}
