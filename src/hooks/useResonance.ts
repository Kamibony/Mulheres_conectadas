import { useState } from "react";
import { shareExperienceApi, type Resonance } from "../services/api";

type State = "idle" | "loading" | "success" | "error";

export const useResonance = () => {
  const [state, setState] = useState<State>("idle");
  const [resonances, setResonances] = useState<Resonance[]>([]);
  const [error, setError] = useState<string | null>(null);

  const share = async (text: string) => {
    setState("loading");
    setError(null);
    try {
      const result = await shareExperienceApi({ text });
      const data = result.data;

      if (data.error) {
        throw new Error(data.error);
      }

      setResonances(data.resonances || []);
      setState("success");
    } catch (err: unknown) {
      console.error("Error sharing experience:", err);
      // Ensure error message is user-friendly
      let errorMessage = "Não foi possível conectar. Por favor, tente novamente em instantes.";

      if (err instanceof Error) {
        if (err.message === "O texto é muito curto.") {
          errorMessage = "Por favor, escreva um pouco mais para encontrarmos histórias parecidas.";
        }
      }

      setError(errorMessage);
      setState("error");
    }
  };

  const reset = () => {
    setState("idle");
    setResonances([]);
    setError(null);
  };

  return { state, resonances, error, share, reset };
};
