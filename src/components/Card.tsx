import React from 'react';
import { HeartHandshake } from 'lucide-react';

interface CardProps {
  text: string;
}

export const Card: React.FC<CardProps> = ({ text }) => {
  return (
    <div className="bg-white/80 backdrop-blur-sm p-6 rounded-2xl shadow-sm border border-rose-100 mb-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-start gap-4">
        <div className="bg-rose-50 p-2 rounded-xl text-rose-300">
          <HeartHandshake size={20} />
        </div>
        <p className="text-stone-600 leading-relaxed flex-1">{text}</p>
      </div>
    </div>
  );
};
