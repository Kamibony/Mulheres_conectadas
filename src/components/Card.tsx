import React from 'react';
import { HeartHandshake, MessageCircle } from 'lucide-react';
import { Button } from './Button';

interface CardProps {
  id?: string;
  text: string;
  onChat?: (id: string) => void;
  isChatLoading?: boolean;
}

export const Card: React.FC<CardProps> = ({ id, text, onChat, isChatLoading }) => {
  return (
    <div className="bg-white/80 backdrop-blur-sm p-6 rounded-2xl shadow-sm border border-rose-100 mb-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-start gap-4 flex-col sm:flex-row">
        <div className="flex items-start gap-4 flex-1">
          <div className="bg-rose-50 p-2 rounded-xl text-rose-300 shrink-0">
            <HeartHandshake size={20} />
          </div>
          <p className="text-stone-600 leading-relaxed flex-1">{text}</p>
        </div>
        {id && onChat && (
          <div className="w-full sm:w-auto mt-4 sm:mt-0">
            <Button
              variant="secondary"
              className="text-sm py-2 px-4 whitespace-nowrap"
              onClick={() => onChat(id)}
              isLoading={isChatLoading}
            >
              <span className="flex items-center gap-2">
                <MessageCircle size={16} />
                Iniciar Chat
              </span>
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};
