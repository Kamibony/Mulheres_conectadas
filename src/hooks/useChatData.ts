import { useState, useEffect } from 'react';
import { collection, doc, onSnapshot, query, orderBy, getDoc } from 'firebase/firestore';
import { db } from '../config/firebase';
import type { User } from 'firebase/auth';

export interface Message {
  id: string;
  text: string;
  senderId: string;
  timestamp: { seconds: number; nanoseconds: number } | null;
}

export interface ChatData {
  status: string;
  users: string[];
}

export const useChatData = (chatId: string, user: User | null | undefined) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatData, setChatData] = useState<ChatData | null>(null);
  const [identities, setIdentities] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!user) return;

    // Listen to chat document
    const unsubscribeChat = onSnapshot(doc(db, 'chats', chatId), async (docSnap) => {
      if (docSnap.exists()) {
        const data = docSnap.data() as ChatData;
        setChatData(data);

        if (data.status === 'revealed') {
          // Fetch identities if revealed
          const fetchIdentities = async () => {
            const newIdentities: Record<string, string> = {};
            for (const uid of data.users) {
              const identityDoc = await getDoc(doc(db, 'chats', chatId, 'identities', uid));
              if (identityDoc.exists()) {
                newIdentities[uid] = identityDoc.data().identity;
              }
            }
            setIdentities(newIdentities);
          };
          fetchIdentities();
        }
      }
    });

    // Listen to messages
    const q = query(collection(db, 'chats', chatId, 'messages'), orderBy('timestamp', 'asc'));
    const unsubscribeMessages = onSnapshot(q, (snapshot) => {
      const msgs = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      })) as Message[];
      setMessages(msgs);
    });

    return () => {
      unsubscribeChat();
      unsubscribeMessages();
    };
  }, [chatId, user]);

  return { messages, chatData, identities };
};
