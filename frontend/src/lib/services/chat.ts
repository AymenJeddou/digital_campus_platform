import api from '../api';

// A single source reference returned by the backend
export interface Citation {
  document: string;
  page: number;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  /** Present on freshly-received assistant messages; not stored in message history from the API */
  citations?: Citation[];
  created_at: string;
}

export interface ChatSession {
  id: string;
  student_id: string;
  created_at: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  citations: Citation[];
}

export const chatService = {
  sendMessage: async (data: ChatRequest) => {
    const response = await api.post<ChatResponse>('/chat', data);
    return response.data;
  },

  getSessions: async () => {
    const response = await api.get<ChatSession[]>('/chat/sessions');
    return response.data;
  },

  getMessages: async (sessionId: string) => {
    const response = await api.get<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`);
    return response.data;
  },
};
