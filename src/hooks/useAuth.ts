import { useState, useEffect } from 'react';
import { auth } from '../config/firebase';
import { signInAnonymously, onAuthStateChanged } from 'firebase/auth';
import type { User } from 'firebase/auth';

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // For local UI testing without actual Firebase keys:
    if (import.meta.env.VITE_FIREBASE_API_KEY === 'mock_key') {
      setUser({ uid: 'mock_user_123', isAnonymous: true } as User);
      setLoading(false);
      return;
    }

    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      if (!currentUser) {
        try {
          const result = await signInAnonymously(auth);
          setUser(result.user);
        } catch (error) {
          console.error("Anonymous auth error:", error);
        }
      } else {
        setUser(currentUser);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  return { user, loading };
};
