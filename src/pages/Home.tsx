import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useResonance } from '../hooks/useResonance';
import { Hero } from '../components/Hero';
import { TextArea } from '../components/TextArea';
import { Button } from '../components/Button';
import { Spinner } from '../components/Spinner';
import { Card } from '../components/Card';
import { AlertCircle, ArrowRight } from 'lucide-react';

export const Home: React.FC = () => {
  const { loading: authLoading } = useAuth();
  const { share, state, resonances, error, reset } = useResonance();
  const [text, setText] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    await share(text);
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50 text-stone-800 font-sans selection:bg-rose-100 pb-20">
      <div className="max-w-md mx-auto px-4 pt-6">
        <header className="flex justify-center mb-6">
          <span className="font-serif text-rose-400 font-bold text-xl tracking-tight">Mulheres Conectadas</span>
        </header>

        <main>
          {state === 'idle' || state === 'loading' || state === 'error' ? (
            <div className="space-y-8 animate-in fade-in duration-500">
              <Hero />

              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="relative">
                  <TextArea
                    placeholder="Escreva aqui o que você está sentindo..."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    disabled={state === 'loading'}
                    autoFocus
                  />
                  {text.length > 0 && (
                    <span className="absolute bottom-3 right-3 text-xs text-stone-400">
                      {text.length} caracteres
                    </span>
                  )}
                </div>

                {error && (
                  <div className="bg-red-50 text-red-600 p-4 rounded-xl text-sm flex items-start gap-3 border border-red-100">
                    <AlertCircle className="shrink-0 mt-0.5" size={16} />
                    <p>{error}</p>
                  </div>
                )}

                <Button
                  type="submit"
                  disabled={!text.trim() || text.length < 10}
                  isLoading={state === 'loading'}
                >
                  <span className="flex items-center gap-2">
                    Encontrar histórias
                    <ArrowRight size={18} />
                  </span>
                </Button>
              </form>
            </div>
          ) : (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-700">
              <div className="text-center py-6">
                <h2 className="text-2xl font-serif text-stone-800 mb-2">Você não está sozinha</h2>
                <p className="text-stone-500 text-sm">Encontramos {resonances.length} histórias que ressoam com a sua.</p>
              </div>

              <div className="space-y-4">
                {resonances.map((resonance) => (
                  <Card key={resonance.id} text={resonance.text} />
                ))}
              </div>

              <div className="pt-8 pb-4">
                <Button variant="secondary" onClick={() => {
                  setText('');
                  reset();
                }}>
                  Escrever nova experiência
                </Button>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
