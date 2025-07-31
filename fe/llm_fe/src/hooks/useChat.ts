// import { useState, useCallback, useEffect } from 'react';
// import { Message, StreamingState } from '@/types/chat';
// import { ChatService } from '@/services/chatService';
// import { Socket } from 'socket.io-client';

// export const useChat = (socket?: Socket | null) => {
//   const [messages, setMessages] = useState<Message[]>([]);
//   const [isLoading, setIsLoading] = useState(false);
//   const [error, setError] = useState<string | null>(null);
//   const [streamingState, setStreamingState] = useState<StreamingState>({
//     isProcessing: false,
//     currentToken: '',
//   });
//   const [currentStreamingMessage, setCurrentStreamingMessage] = useState<Message | null>(null);

//   // Socket event handlers
//   useEffect(() => {
//     if (!socket) return;

//     const handleProcessing = () => {
//       setStreamingState({
//         isProcessing: true,
//         currentToken: '',
//       });
//     };

//     const handleGenToken = (data: { data: string }) => {
//       setStreamingState(prev => ({
//         ...prev,
//         isProcessing: false,
//         currentToken: prev.currentToken + data.data,
//       }));
//     };

//     const handleCompleted = (data: { response: string }) => {
//       const assistantMessage: Message = {
//         id: Date.now().toString(),
//         content: data.response,
//         role: 'assistant',
//         timestamp: new Date(),
//         isComplete: true,
//       };

//       setMessages(prev => [...prev, assistantMessage]);
//       setStreamingState({
//         isProcessing: false,
//         currentToken: '',
//       });
//       setCurrentStreamingMessage(null);
//       setIsLoading(false);
//     };

//     const handleError = (data: { error: string }) => {
//       setStreamingState(prev => ({
//         ...prev,
//         isProcessing: false,
//         error: data.error,
//       }));
//       setError(data.error);
//       setIsLoading(false);
//     };

//     const handleStatus = (data: { status: string }) => {
//       console.log('Status event received:', data);
//     };

//     socket.on('processing', handleProcessing);
//     socket.on('gen_token', handleGenToken);
//     socket.on('completed', handleCompleted);
//     socket.on('error', handleError);
//     socket.on('status', handleStatus);

//     return () => {
//       socket.off('processing', handleProcessing);
//       socket.off('gen_token', handleGenToken);
//       socket.off('completed', handleCompleted);
//       socket.off('error', handleError);
//       socket.off('status', handleStatus);
//     };
//   }, [socket]);

//   const sendMessage = useCallback(async (content: string) => {
//     if (!content.trim()) return;

//     console.log('Sending message:', content);
//     console.log('Socket available:', !!socket);

//     const userMessage: Message = {
//       id: Date.now().toString(),
//       content,
//       role: 'user',
//       timestamp: new Date(),
//     };

//     setMessages(prev => [...prev, userMessage]);
//     setIsLoading(true);
//     setError(null);
//     setStreamingState({
//       isProcessing: false,
//       currentToken: '',
//     });

//     try {
//       const conversation = typeof window !== 'undefined' 
//         ? JSON.parse(localStorage.getItem('conversation') || '{}')
//         : {};
      
//       console.log('Conversation data:', conversation);
//       console.log('About to call ChatService.sendMessage with:', {
//         message: content,
//         conversation: conversation || '',
//       });
      
//       // Always make REST API call to /api/chat
//       // The streaming response will come through socket events
//       const response = await ChatService.sendMessage({
//         message: content,
//         conversation: conversation || '',
//       });

//       console.log('API response received:', response);

//       // If no socket is available, handle response directly
//       if (!socket) {
//         const assistantMessage: Message = {
//           id: (Date.now() + 1).toString(),
//           content: response.message,
//           role: 'assistant',
//           timestamp: new Date(response.timestamp),
//         };

//         setMessages(prev => [...prev, assistantMessage]);
//         setIsLoading(false);
//       }
//       // If socket is available, the response will be handled by socket events
//       // The REST API triggers the backend processing, socket provides streaming updates
      
//     } catch (err) {
//       setError(err instanceof Error ? err.message : 'An error occurred');
//       setIsLoading(false);
//     }
//   }, [socket]);

//   const clearMessages = useCallback(() => {
//     setMessages([]);
//     setError(null);
//     setStreamingState({
//       isProcessing: false,
//       currentToken: '',
//     });
//   }, []);

//   return {
//     messages,
//     isLoading,
//     error,
//     sendMessage,
//     clearMessages,
//     streamingState,
//   };
// };



// hooks/useChat.ts

import { useState, useCallback, useEffect } from 'react';
import { Socket } from 'socket.io-client';
import { Message, StreamingState } from '@/types/chat'; // Giả sử bạn có file types này
import { ChatService } from '@/services/chatService';

export const useChat = (socket: Socket | null, conversationId: string) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streamingState, setStreamingState] = useState<StreamingState>({
    isProcessing: false,
    currentToken: '',
  });

  // ========== ĐĂNG KÝ CÁC EVENT LISTENER CỦA SOCKET ==========
  useEffect(() => {
    // Chỉ thực hiện khi socket đã sẵn sàng
    if (!socket) {
      return;
    }

    console.log(`[useChat] Attaching listeners to socket id: ${socket.id}`);

    // Handler khi backend bắt đầu xử lý
    const handleProcessing = () => {
      console.log('[HANDLER] Received event: processing');
      setStreamingState({ isProcessing: true, currentToken: '' });
    };

    // Handler khi nhận được một token mới
    const handleGenToken = (payload: { data: string }) => {
      console.log('[HANDLER] Received event: gen_token with payload:', payload);
      // Đảm bảo payload có cấu trúc đúng
      if (typeof payload.data === 'string') {
        setStreamingState(prev => ({
          ...prev,
          isProcessing: false, // Không còn processing nữa vì đã có token
          currentToken: prev.currentToken + payload.data,
        }));
      }
    };

    // Handler khi luồng trả về hoàn tất
    const handleCompleted = (payload: { response: string }) => {
      console.log('[HANDLER] Received event: completed with payload:', payload);
      // Khi hoàn thành, ta không cần dựa vào currentToken nữa, vì backend đã gửi về câu trả lời hoàn chỉnh
      const assistantMessage: Message = {
        id: Date.now().toString(),
        content: payload.response, // Lấy response cuối cùng từ backend
        role: 'assistant',
        timestamp: new Date(),
      };
      
      // Thêm tin nhắn hoàn chỉnh vào danh sách và reset trạng thái streaming
      setMessages(prev => [...prev, assistantMessage]);
      setStreamingState({ isProcessing: false, currentToken: '' });
      setIsLoading(false); // Kết thúc loading
    };

    // Handler khi có lỗi từ backend
    const handleError = (payload: { error: string }) => {
      console.error('[HANDLER] Received event: error with payload:', payload);
      setError(payload.error || 'An unknown error occurred.');
      setStreamingState({ isProcessing: false, currentToken: '' });
      setIsLoading(false);
    };

    // Đăng ký các listeners
    socket.on('processing', handleProcessing);
    socket.on('gen_token', handleGenToken);
    socket.on('completed', handleCompleted);
    socket.on('error', handleError);

    // Hàm dọn dẹp: Hủy đăng ký các listeners khi component unmount hoặc socket thay đổi
    return () => {
      console.log(`[useChat] Cleaning up listeners for socket id: ${socket.id}`);
      socket.off('processing', handleProcessing);
      socket.off('gen_token', handleGenToken);
      socket.off('completed', handleCompleted);
      socket.off('error', handleError);
    };
  }, [socket]); // Chỉ re-run effect nếu instance socket thay đổi

  // ========== HÀM GỬI TIN NHẮN ==========
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    // Reset các state trước khi gửi
    setIsLoading(true);
    setError(null);
    setStreamingState({ isProcessing: false, currentToken: '' });

    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      role: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);

    try {
      // Gửi request tới API Server để kích hoạt Celery task
      await ChatService.sendMessage({
        message: content,
        conversation: conversationId,
      });
      // Không cần làm gì với response ở đây, vì mọi cập nhật sẽ đến qua Socket.IO
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message.';
      console.error(errorMessage);
      setError(errorMessage);
      setIsLoading(false); // Dừng loading nếu API call thất bại
    }
  }, [conversationId, isLoading]);

  // ========== HÀM XÓA TIN NHẮN ==========
  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
    setStreamingState({ isProcessing: false, currentToken: '' });
    // Có thể thêm logic gọi API để xóa conversation trên server ở đây
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
    streamingState,
  };
};