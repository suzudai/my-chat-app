export interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  streaming?: boolean;
  error?: boolean;
}

export interface Model {
  id: string;
  name: string;
}