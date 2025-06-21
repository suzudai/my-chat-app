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
  provider?: string;
  disabled?: boolean;
}

export interface DocumentInfo {
  file_name: string;
  file_type: string;
  source_path: string;
}

export interface ApiResponse {
  success: boolean;
  message: string;
}