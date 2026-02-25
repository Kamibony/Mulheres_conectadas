import React from 'react';

export const Spinner: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center py-12 space-y-4">
      <div className="relative">
        <div className="w-12 h-12 rounded-full border-4 border-rose-100 animate-pulse"></div>
        <div className="absolute top-0 left-0 w-12 h-12 rounded-full border-4 border-t-rose-300 animate-spin"></div>
      </div>
      <p className="text-stone-400 text-sm animate-pulse">Buscando histórias que ressoam com a sua...</p>
    </div>
  );
};
