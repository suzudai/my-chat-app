export interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  streaming?: boolean;
  error?: boolean;
  role?: 'user' | 'assistant';
  content?: string;
  sources?: Source[];
}

export interface Model {
  id: string;
  name: string;
  provider?: string;
  disabled?: boolean;
}

export interface DocumentInfo {
  file_name: string;
  file_type: string;
  source_path: string;
}

export interface ChatHistorySession {
  thread_id: string;
  title: string;
  created_at: Date;
  last_message_at: Date;
  message_count?: number;
  updated_at?: string;
}

export interface ApiResponse {
  success: boolean;
  message: string;
}

export interface ChatResponse {
  reply: string;
  updated_title?: string;
  thread_id?: string;
  sources?: Source[];
}

export interface BackendChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface BackendChatSession {
  thread_id: string;
  title: string;
  updated_at: string;
  message_count: number;
  last_message_at: string;
}

export interface CreateSessionResponse {
  thread_id: string;
  title: string;
  message: string;
}

export interface Source {
  file_name: string;
  content: string;
  source_path?: string;
}