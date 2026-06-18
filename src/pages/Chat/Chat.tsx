import React, { useEffect, useState, useRef } from 'react';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';
import { db } from '../../config/firebase';
import { useAuth } from '../../hooks/useAuth';
import { useChatData } from '../../hooks/useChatData';
import { Button } from '../../components/Button';
import { requestRevealApi } from '../../services/api';
import { ArrowLeft, Send, AlertCircle, X } from 'lucide-react';
import { Spinner } from '../../components/Spinner';

interface ChatProps {
  chatId: string;
  onBack: () => void;
}

export const Chat: React.FC<ChatProps> = ({ chatId, onBack }) => {
  const { user } = useAuth();
  const { messages, chatData, identities } = useChatData(chatId, user);
  const [newMessage, setNewMessage] = useState('');
  const [isRevealing, setIsRevealing] = useState(false);
  const [identityInput, setIdentityInput] = useState('');
  const [showIdentityPrompt, setShowIdentityPrompt] = useState(false);
  const [revealError, setRevealError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !user) return;

    const text = newMessage.trim();
    setNewMessage('');

    await addDoc(collection(db, 'chats', chatId, 'messages'), {
      text,
      senderId: user.uid,
      timestamp: serverTimestamp()
    });
  };

  const handleRequestReveal = async () => {
    if (!identityInput.trim()) return;

    setIsRevealing(true);
    setRevealError(null);
    try {
      await requestRevealApi({ chatId, identity: identityInput.trim() });
      setShowIdentityPrompt(false);
      setIdentityInput(''); // Optionally clear on success
    } catch (error) {
      console.error("Error requesting reveal:", error);
      setRevealError("Erro ao solicitar revelação.");
    } finally {
      setIsRevealing(false);
    }
  };

  if (!chatData || !user) {
    return <div className="min-h-screen flex items-center justify-center bg-stone-50"><Spinner /></div>;
  }

  const isUserA = chatData.users[0] === user.uid;
  const otherLabel = isUserA ? 'User B' : 'User A';

  const myPendingStatus = `reveal_pending_${isUserA ? 'a' : 'b'}`;
  const otherPendingStatus = `reveal_pending_${isUserA ? 'b' : 'a'}`;

  return (
    <div className="flex flex-col h-screen bg-stone-50 text-stone-800 relative">
      {error && (
        <div className="absolute top-16 left-1/2 -translate-x-1/2 z-50 animate-in fade-in slide-in-from-top-4 duration-300 w-full max-w-sm px-4">
          <div className="bg-red-50 text-red-600 p-4 rounded-xl text-sm flex items-start gap-3 border border-red-100 shadow-sm">
            <AlertCircle className="shrink-0 mt-0.5" size={16} />
            <p className="flex-1">{error}</p>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600 transition-colors">
              <X size={16} />
            </button>
          </div>
        </div>
      )}

      <header className="bg-white border-b border-stone-200 p-4 flex items-center justify-between shrink-0">
        <button onClick={onBack} className="text-stone-500 hover:text-stone-800 transition-colors">
          <ArrowLeft size={24} />
        </button>
        <div className="font-medium text-lg">
          Chat com {chatData.status === 'revealed' ? identities[chatData.users.find(u => u !== user.uid) || ''] || otherLabel : otherLabel}
        </div>
        <div className="w-6" /> {/* Spacer for centering */}
      </header>

      {/* Identity Reveal Banner */}
      <div className="bg-stone-100 border-b border-stone-200 p-3 text-center text-sm flex flex-col items-center gap-2 shrink-0">
        {chatData.status === 'anonymous' && !showIdentityPrompt && (
          <Button variant="secondary" className="py-1 px-4 text-xs w-auto" onClick={() => setShowIdentityPrompt(true)}>
            Solicitar Identidade Real
          </Button>
        )}
        {showIdentityPrompt && (
          <div className="flex flex-col gap-2 w-full max-w-md">
            <div className="flex gap-2 items-center w-full">
              <input
                type="text"
                placeholder="Seu Instagram ou WhatsApp"
                className="flex-1 p-2 rounded-xl border border-stone-200 text-sm"
                value={identityInput}
                onChange={(e) => setIdentityInput(e.target.value)}
              />
              <Button className="py-2 px-4 w-auto text-sm" isLoading={isRevealing} onClick={handleRequestReveal}>
                Enviar
              </Button>
              <button onClick={() => { setShowIdentityPrompt(false); setRevealError(null); }} className="text-stone-400 p-2">Cancelar</button>
            </div>
            {revealError && (
              <div className="bg-red-50 text-red-600 p-3 rounded-xl text-xs flex items-start gap-2 border border-red-100 mt-1">
                <AlertCircle className="shrink-0 mt-0.5" size={14} />
                <p className="text-left">{revealError}</p>
              </div>
            )}
          </div>
        )}
        {chatData.status === myPendingStatus && (
          <span className="text-stone-500">Você solicitou a revelação da identidade. Aguardando o outro membro.</span>
        )}
        {chatData.status === otherPendingStatus && !showIdentityPrompt && (
          <div className="flex items-center gap-4 flex-col sm:flex-row">
            <span className="text-blue-600 font-medium">O outro membro quer revelar a identidade!</span>
            <Button variant="primary" className="py-1 px-4 text-xs w-auto" onClick={() => setShowIdentityPrompt(true)}>
              Aceitar e Revelar
            </Button>
          </div>
        )}
        {chatData.status === 'revealed' && (
          <div className="text-green-600 font-medium bg-green-50 px-4 py-2 rounded-xl border border-green-100">
            Identidades reveladas! Você é {identities[user.uid]} e o outro membro é {identities[chatData.users.find(u => u !== user.uid) || '']}.
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(msg => {
          const isMine = msg.senderId === user.uid;
          return (
            <div key={msg.id} className={`flex flex-col ${isMine ? 'items-end' : 'items-start'}`}>
              <div className="text-xs text-stone-400 mb-1 ml-1 mr-1">
                {isMine ? 'Você' : otherLabel}
              </div>
              <div className={`px-4 py-2 rounded-2xl max-w-[80%] ${isMine ? 'bg-blue-400 text-white rounded-tr-sm' : 'bg-white border border-stone-200 rounded-tl-sm'}`}>
                {msg.text}
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSendMessage} className="bg-white border-t border-stone-200 p-4 flex gap-2 shrink-0">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Digite sua mensagem..."
          className="flex-1 bg-stone-50 border border-stone-200 rounded-full px-4 py-2 outline-none focus:border-blue-300 focus:ring-1 focus:ring-blue-300 transition-all"
        />
        <Button type="submit" disabled={!newMessage.trim()} className="w-12 h-12 p-0 rounded-full flex items-center justify-center shrink-0">
          <Send size={18} className="-ml-0.5" />
        </Button>
      </form>
    </div>
  );
};
