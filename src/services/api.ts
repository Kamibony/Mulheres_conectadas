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
