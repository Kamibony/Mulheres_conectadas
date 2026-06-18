import React from 'react';
import { Sparkles } from 'lucide-react';

export const Hero: React.FC = () => {
  return (
    <div className="text-center py-8 px-4 space-y-4">
      <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/50 rounded-full text-xs font-medium text-blue-500 mb-2 border border-blue-200">
        <Sparkles size={12} />
        <span>Espaço Seguro de Apoio e Comunhão</span>
      </div>
      <h1 className="text-3xl font-serif text-stone-800 font-medium">
        Compartilhe seu fardo
      </h1>
      <p className="text-stone-500 max-w-sm mx-auto leading-relaxed">
        Faça seu pedido de oração e encontre apoio em outros membros da nossa comunidade que podem orar com você.
      </p>
    </div>
  );
};
