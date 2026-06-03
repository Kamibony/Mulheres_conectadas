import { httpsCallable } from "firebase/functions";
import { functions } from "../config/firebase";

export interface Resonance {
  id: string;
  text: string;
}

export interface ShareExperienceResponse {
  success?: boolean;
  myPostId?: string;
  resonances?: Resonance[];
  error?: string;
}

export interface ShareExperienceRequest {
  text: string;
}

export const shareExperienceApi = httpsCallable<ShareExperienceRequest, ShareExperienceResponse>(
  functions,
  "share_experience"
);


export interface StartChatRequest {
  target_post_id: string;
}

export interface StartChatResponse {
  success?: boolean;
  chatId?: string;
  error?: string;
}

export const startChatApi = httpsCallable<StartChatRequest, StartChatResponse>(
  functions,
  "start_chat"
);

export interface RequestRevealRequest {
  chatId: string;
  identity: string;
}

export interface RequestRevealResponse {
  success?: boolean;
  status?: string;
  error?: string;
}

export const requestRevealApi = httpsCallable<RequestRevealRequest, RequestRevealResponse>(
  functions,
  "request_reveal"
);
