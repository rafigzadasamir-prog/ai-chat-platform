export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface Conversation {
  id: number;
  title: string;
  created_at: string;
}

export interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface DocumentInfo {
  document_name: string;
  chunk_count: number;
}

export interface Usage {
  message_count: number;
  estimated_tokens: number;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}
