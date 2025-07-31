// contexts/SocketContext.tsx
'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import io, { Socket } from 'socket.io-client';

const SOCKET_URL = process.env.NEXT_PUBLIC_SOCKET_URL || 'http://localhost:9000';

// Định nghĩa kiểu cho Context
interface SocketContextType {
  socket: Socket | null;
}

// Tạo Context với giá trị mặc định
const SocketContext = createContext<SocketContextType>({ socket: null });

// Custom hook để sử dụng Context một cách tiện lợi
export const useSocketContext = () => {
  return useContext(SocketContext);
};

// Provider component
export const SocketProvider = ({ children }: { children: React.ReactNode }) => {
  const [socket, setSocket] = useState<Socket | null>(null);

  useEffect(() => {
    // Chỉ tạo socket MỘT LẦN khi ứng dụng được mount
    const newSocket = io(SOCKET_URL, {
      reconnection: true,
      transports: ['websocket'], // Ưu tiên websocket
    });

    // Listener debug "bắt tất cả" sự kiện
    newSocket.onAny((eventName, ...args) => {
      console.log(`[SOCKET CONTEXT] Event Received: '${eventName}'`, args);
    });

    setSocket(newSocket);

    // Dọn dẹp khi ứng dụng đóng hoàn toàn (unmount)
    return () => {
      newSocket.close();
    };
  }, []); // <-- Mảng dependency rỗng đảm bảo nó chỉ chạy một lần duy nhất!

  return (
    <SocketContext.Provider value={{ socket }}>
      {children}
    </SocketContext.Provider>
  );
};