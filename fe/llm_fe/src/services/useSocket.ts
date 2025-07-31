import { useEffect, useState } from 'react';
import io, { Socket } from 'socket.io-client';


const SOCKETIO_URL = process.env.NEXT_PUBLIC_SOCKET_URL || 'http://localhost:9000/';

export const useSocket = (conversationId: string) => {
  const [socket, setSocket] = useState<Socket | null>(null);

  useEffect(() => {
    if (!conversationId) {
      return;
    }

    const newSocket = io(SOCKETIO_URL, {
      reconnection: true,
      reconnectionAttempts: 5,
      autoConnect: false,
    });

    setSocket(newSocket);

    newSocket.connect();

    newSocket.on('connect', () => {
      console.log('Connected to Socket.IO server');
      
      // Join specific conversation room
      const conversationId = 'your-conversation-id'; // Get this from your app state
      newSocket.emit('join_room', { conversation_id: conversationId });
  });

    return () => {
      console.log('Disconnecting socket...');
      newSocket.disconnect();
    };
  }, [conversationId]); 

  return socket;
};