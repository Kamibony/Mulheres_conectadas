import { useState, useEffect } from 'react';
import { AlertCircle, X } from 'lucide-react';
import { Home } from './pages/Home';
import { Chat } from './pages/Chat/Chat';
import { startChatApi } from './services/api';

function App() {
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [isStartingChat, setIsStartingChat] = useState(false);
  const [startingChatId, setStartingChatId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const handleStartChat = async (targetPostId: string) => {
    setIsStartingChat(true);
    setStartingChatId(targetPostId);
    try {
      const response = await startChatApi({ target_post_id: targetPostId });
      if (response.data.success && response.data.chatId) {
        setCurrentChatId(response.data.chatId);
      } else {
        console.error("Failed to start chat", response.data.error);
        setError("Erro ao iniciar o chat. Tente novamente.");
      }
    } catch (err) {
      console.error("Error starting chat:", err);
      setError("Erro de conexão. Tente novamente.");
    } finally {
      setIsStartingChat(false);
      setStartingChatId(null);
    }
  };

  if (currentChatId) {
    return <Chat chatId={currentChatId} onBack={() => setCurrentChatId(null)} />;
  }

  return (
    <>
      {error && (
        <div className="fixed top-4 right-4 z-50 animate-in fade-in slide-in-from-top-4 duration-300">
          <div className="bg-red-50 text-red-600 p-4 rounded-xl text-sm flex items-start gap-3 border border-red-100 shadow-sm max-w-sm">
            <AlertCircle className="shrink-0 mt-0.5" size={16} />
            <p className="flex-1">{error}</p>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600 transition-colors">
              <X size={16} />
            </button>
          </div>
        </div>
      )}
      <Home
        onStartChat={handleStartChat}
        isStartingChat={isStartingChat}
        startingChatId={startingChatId}
      />
    </>
  );
}

export default App;
