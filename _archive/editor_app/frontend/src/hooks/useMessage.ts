import { useState, useCallback } from 'react';

export type MessageType = 'error' | 'success';

interface Message {
  type: MessageType;
  text: string;
}

export const useMessage = () => {
  const [message, setMessage] = useState<Message | null>(null);

  const showMessage = useCallback((type: MessageType, text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  }, []);

  const hideMessage = useCallback(() => {
    setMessage(null);
  }, []);

  return { message, showMessage, hideMessage };
};

