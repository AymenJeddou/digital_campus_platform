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
  /** Streaming groundedness signal: false means the sources may not fully support the answer. */
  grounded?: boolean;
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
  /** When set, the assistant also searches this course's materials (scoped to the student). */
  course_id?: string;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  citations: Citation[];
}

export interface StreamHandlers {
  onSession?: (sessionId: string) => void;
  onChunk?: (text: string) => void;
  onCitations?: (citations: Citation[]) => void;
  onGrounded?: (grounded: boolean) => void;
  onDone?: () => void;
  onError?: (err: unknown) => void;
}

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://localhost:8000';

export const chatService = {
  sendMessage: async (data: ChatRequest) => {
    const response = await api.post<ChatResponse>('/chat', data);
    return response.data;
  },

  /**
   * Stream an answer token-by-token from POST /chat/stream (Server-Sent Events).
   * EventSource can't send an Authorization header or a POST body, so we read
   * the response body stream directly. The backend emits `data:` lines carrying
   * JSON ({session_id} | {chunk} | {grounded} | {citations}) then a "[DONE]".
   * Returns an AbortController so the caller can cancel an in-flight stream.
   */
  streamMessage: (data: ChatRequest, handlers: StreamHandlers) => {
    const controller = new AbortController();
    (async () => {
      try {
        const token =
          typeof window !== 'undefined' ? localStorage.getItem('token') : null;
        const res = await fetch(`${apiBaseUrl}/chat/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify(data),
          signal: controller.signal,
        });
        if (!res.ok || !res.body) throw new Error(`Stream failed (${res.status})`);

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          // SSE events are separated by a blank line. sse-starlette uses CRLF
          // ("\r\n\r\n"), so splitting on "\n\n" alone never finds a boundary
          // and the stream never renders — match CRLF, CR, and LF forms.
          const events = buffer.split(/\r\n\r\n|\r\r|\n\n/);
          buffer = events.pop() ?? '';
          for (const evt of events) {
            const line = evt
              .split(/\r\n|\r|\n/)
              .find((l) => l.startsWith('data:'));
            if (!line) continue;
            const payload = line.slice(5).trim();
            if (payload === '[DONE]') {
              handlers.onDone?.();
              continue;
            }
            try {
              const obj = JSON.parse(payload);
              if (obj.session_id) handlers.onSession?.(obj.session_id);
              if (typeof obj.chunk === 'string') handlers.onChunk?.(obj.chunk);
              if (Array.isArray(obj.citations)) handlers.onCitations?.(obj.citations);
              if (typeof obj.grounded === 'boolean') handlers.onGrounded?.(obj.grounded);
            } catch {
              /* ignore malformed keep-alive lines */
            }
          }
        }
        handlers.onDone?.();
      } catch (err) {
        if ((err as Error)?.name !== 'AbortError') handlers.onError?.(err);
      }
    })();
    return controller;
  },

  getSessions: async () => {
    const response = await api.get<ChatSession[]>('/chat/sessions');
    return response.data;
  },

  getMessages: async (sessionId: string) => {
    const response = await api.get<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`);
    return response.data;
  },

  sendFeedback: async (data: { chat_message_id: string; rating: number; comment?: string }) => {
    const response = await api.post('/chat/feedback', data);
    return response.data;
  },
};
