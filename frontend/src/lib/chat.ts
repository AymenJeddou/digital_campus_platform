import { request } from './api';
import type { Citation } from './types';

export interface StreamEvents {
  onSession?: (id: string) => void;
  onChunk?: (text: string) => void;
  onGrounded?: (grounded: boolean) => void;
  onCitations?: (citations: Citation[]) => void;
  onMessageId?: (id: string) => void;
}

/** POST /chat/stream and dispatch its Server-Sent Events. Resolves when the
 * stream ends; rejects with ApiError (HTTP) or AbortError (stopped). */
export async function streamChat(
  body: { message?: string; session_id?: string; course_id?: string; regenerate?: boolean },
  events: StreamEvents,
  signal: AbortSignal,
): Promise<void> {
  const res = await request('chat/stream', { json: body, signal });
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    // Events end with a blank line; sse-starlette writes CRLF.
    const parts = buffer.split(/\r\n\r\n|\n\n|\r\r/);
    buffer = parts.pop() ?? '';
    for (const part of parts) {
      const data = part
        .split(/\r\n|\n|\r/)
        .filter((line) => line.startsWith('data:'))
        .map((line) => line.slice(5).replace(/^ /, ''))
        .join('\n');
      if (!data || data === '[DONE]') continue;
      let event: Record<string, unknown>;
      try {
        event = JSON.parse(data);
      } catch {
        continue; // keep-alive / comment lines
      }
      if (typeof event.session_id === 'string') events.onSession?.(event.session_id);
      if (typeof event.chunk === 'string') events.onChunk?.(event.chunk);
      if (typeof event.grounded === 'boolean') events.onGrounded?.(event.grounded);
      if (Array.isArray(event.citations)) events.onCitations?.(event.citations as Citation[]);
      if (typeof event.message_id === 'string') events.onMessageId?.(event.message_id);
    }
  }
}
