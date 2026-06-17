import { useState } from 'react';
import { Home } from './pages/Home';
import { Chat } from './pages/Chat/Chat';
import { startChatApi } from './services/api';

function App() {
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [isStartingChat, setIsStartingChat] = useState(false);
  const [startingChatId, setStartingChatId] = useState<string | null>(null);
  const [chatError, setChatError] = useState<string | null>(null);

  const handleStartChat = async (targetPostId: string) => {
    setIsStartingChat(true);
    setStartingChatId(targetPostId);
    setChatError(null);
    try {
      const response = await startChatApi({ target_post_id: targetPostId });
      if (response.data.success && response.data.chatId) {
        setCurrentChatId(response.data.chatId);
      } else {
        console.error("Failed to start chat", response.data.error);
        setChatError("Erro ao iniciar o chat. Tente novamente.");
      }
    } catch (error) {
      console.error("Error starting chat:", error);
      setChatError("Erro de conexão. Tente novamente.");
    } finally {
      setIsStartingChat(false);
      setStartingChatId(null);
    }
  };

  if (currentChatId) {
    return <Chat chatId={currentChatId} onBack={() => setCurrentChatId(null)} />;
  }

  return (
    <Home
      onStartChat={handleStartChat}
      isStartingChat={isStartingChat}
      startingChatId={startingChatId}
      chatError={chatError}
    />
  );
}

export default App;
