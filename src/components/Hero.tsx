import React from 'react';
import { Sparkles } from 'lucide-react';

export const Hero: React.FC = () => {
  return (
    <div className="text-center py-8 px-4 space-y-4">
      <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/50 rounded-full text-xs font-medium text-rose-400 mb-2 border border-rose-100">
        <Sparkles size={12} />
        <span>Espaço Seguro e Anônimo</span>
      </div>
      <h1 className="text-3xl font-serif text-stone-800 font-medium">
        Como você está se sentindo hoje?
      </h1>
      <p className="text-stone-500 max-w-sm mx-auto leading-relaxed">
        Compartilhe seus sentimentos sobre a menopausa e encontre conforto nas histórias de outras mulheres que passam pelo mesmo.
      </p>
    </div>
  );
};
