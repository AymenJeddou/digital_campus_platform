'use client';

import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { toast } from 'sonner';
import {
  ArrowUp, BookOpenText, Check, Copy, History, Pencil, Plus, RotateCcw, ShieldAlert, Square, ThumbsDown, ThumbsUp, Trash2, X,
} from 'lucide-react';
import { Answer } from '@/components/Answer';
import { Placard } from '@/components/Placard';
import { buttonClass } from '@/components/ui';
import { ApiError, api } from '@/lib/api';
import { streamChat } from '@/lib/chat';
import { fill } from '@/lib/dictionary';
import { formatDate, useLocale, useT } from '@/lib/i18n';
import { LINES, PENDING_QUESTION_KEY, type ChatMessage, type ChatSession, type Line } from '@/lib/types';

const STREAMING_ID = 'streaming';

function Chat() {
  const t = useT();
  const locale = useLocale();
  const router = useRouter();
  const params = useSearchParams();

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(params.get('session'));
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [line, setLine] = useState<Line>(params.get('course') ? 'learning' : 'orientation');
  const [course, setCourse] = useState(
    params.get('course') ? { id: params.get('course')!, name: params.get('name') ?? '' } : null,
  );
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const historyRef = useRef<HTMLDialogElement>(null);
  const pinnedToBottom = useRef(true);

  const loadSessions = useCallback(() => {
    api<ChatSession[]>('chat/sessions').then(setSessions).catch(() => {});
  }, []);

  const setUrl = useCallback(
    (id: string | null) => {
      const q = new URLSearchParams();
      if (id) q.set('session', id);
      if (course) {
        q.set('course', course.id);
        q.set('name', course.name);
      }
      router.replace(q.size ? `/chat?${q}` : '/chat', { scroll: false });
    },
    [router, course],
  );

  const openSession = useCallback(
    async (id: string) => {
      abortRef.current?.abort();
      historyRef.current?.close();
      setSessionId(id);
      setUrl(id);
      try {
        setMessages(await api<ChatMessage[]>(`chat/sessions/${id}/messages`));
        pinnedToBottom.current = true;
      } catch {
        toast.error(t.common.error);
      }
    },
    [setUrl, t],
  );

  const newChat = () => {
    abortRef.current?.abort();
    historyRef.current?.close();
    setSessionId(null);
    setMessages([]);
    setUrl(null);
    inputRef.current?.focus();
  };

  const patchStreaming = (fields: Partial<ChatMessage> | ((m: ChatMessage) => Partial<ChatMessage>)) =>
    setMessages((list) =>
      list.map((m) => (m.id === STREAMING_ID ? { ...m, ...(typeof fields === 'function' ? fields(m) : fields) } : m)),
    );

  const send = useCallback(
    async (text: string, regenerate = false) => {
      const question = text.trim();
      if (busy || (!question && !regenerate)) return;
      const now = new Date().toISOString();
      const draft: ChatMessage = {
        id: STREAMING_ID, session_id: sessionId ?? '', role: 'assistant', content: '', citations: [], grounded: null,
        created_at: now, rating: null, streaming: true,
      };
      setMessages((list) => {
        if (regenerate) {
          const lastAssistant = list.map((m) => m.role).lastIndexOf('assistant');
          return [...list.slice(0, lastAssistant), draft];
        }
        return [...list, { ...draft, id: `user-${now}`, role: 'user', content: question, streaming: false }, draft];
      });
      if (!regenerate) setInput('');
      setBusy(true);
      pinnedToBottom.current = true;
      const controller = new AbortController();
      abortRef.current = controller;

      try {
        await streamChat(
          {
            ...(regenerate ? { regenerate: true } : { message: question }),
            session_id: sessionId ?? undefined,
            course_id: course?.id,
          },
          {
            onSession: (id) => {
              if (!sessionId) {
                setSessionId(id); // no reload: the stream is filling this conversation
                setUrl(id);
              }
            },
            onChunk: (chunk) => patchStreaming((m) => ({ content: m.content + chunk })),
            onGrounded: (grounded) => patchStreaming({ grounded }),
            onCitations: (citations) => patchStreaming({ citations }),
            onMessageId: (id) => patchStreaming({ id, streaming: false }),
          },
          controller.signal,
        );
        patchStreaming({ streaming: false });
      } catch (err) {
        if ((err as Error).name === 'AbortError') {
          patchStreaming((m) => ({ streaming: false, content: m.content || t.chat.stopped }));
        } else {
          setMessages((list) => list.filter((m) => m.id !== STREAMING_ID && m.content !== question));
          if (!regenerate) setInput(question);
          const status = err instanceof ApiError ? err.status : 0;
          toast.error(status === 429 ? t.chat.rateLimited : status === 422 ? t.chat.tooLong : status === 0 ? t.common.offline : t.common.error);
        }
      } finally {
        setBusy(false);
        abortRef.current = null;
        loadSessions();
      }
    },
    [busy, sessionId, course, setUrl, loadSessions, t],
  );

  // First load: history, the conversation in the URL, and a question carried
  // over from the landing page.
  const started = useRef(false);
  useEffect(() => {
    if (started.current) return;
    started.current = true;
    loadSessions();
    if (sessionId) {
      api<ChatMessage[]>(`chat/sessions/${sessionId}/messages`).then(setMessages).catch(() => toast.error(t.common.error));
    }
    let pending: string | null = null;
    try {
      pending = sessionStorage.getItem(PENDING_QUESTION_KEY);
      sessionStorage.removeItem(PENDING_QUESTION_KEY);
    } catch {}
    if (pending && !sessionId) queueMicrotask(() => send(pending));
    // Mount-only: later changes are driven by the user's actions.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (el && pinnedToBottom.current) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const rate = async (message: ChatMessage, rating: 0 | 1) => {
    setMessages((list) => list.map((m) => (m.id === message.id ? { ...m, rating } : m)));
    try {
      await api('chat/feedback', { json: { chat_message_id: message.id, rating } });
      toast.success(t.chat.thanks);
    } catch {
      setMessages((list) => list.map((m) => (m.id === message.id ? { ...m, rating: message.rating } : m)));
      toast.error(t.common.error);
    }
  };

  const rename = async (s: ChatSession) => {
    const title = window.prompt(t.chat.renamePrompt, s.title ?? '')?.trim();
    if (!title) return;
    await api(`chat/sessions/${s.id}`, { method: 'PATCH', json: { title: title.slice(0, 120) } }).catch(() => toast.error(t.common.error));
    loadSessions();
  };

  const remove = async (s: ChatSession) => {
    if (!window.confirm(t.chat.deleteConfirm)) return;
    try {
      await api(`chat/sessions/${s.id}`, { method: 'DELETE' });
      if (s.id === sessionId) newChat();
      loadSessions();
    } catch {
      toast.error(t.common.error);
    }
  };

  const lastAssistantId = [...messages].reverse().find((m) => m.role === 'assistant')?.id;

  const historyList = (
    <ul className="space-y-0.5">
      {sessions.length === 0 && <li className="px-2 py-3 text-sm text-ink-3">{t.chat.noHistory}</li>}
      {sessions.map((s) => (
        <li key={s.id} className="group relative">
          <button
            type="button"
            onClick={() => openSession(s.id)}
            aria-current={s.id === sessionId ? 'true' : undefined}
            className={`block w-full rounded-md py-2 ps-3 pe-16 text-start text-sm ${
              s.id === sessionId ? 'bg-sunken font-medium text-ink' : 'text-ink-2 hover:bg-sunken'
            }`}
          >
            <span className="block truncate">{s.title || t.chat.untitled}</span>
            <span className="block text-xs text-ink-3">{formatDate(s.updated_at ?? s.created_at, locale)}</span>
          </button>
          <span className="absolute inset-y-0 end-1 flex items-center gap-0.5 opacity-100 lg:opacity-0 lg:group-hover:opacity-100 lg:group-focus-within:opacity-100">
            <button type="button" onClick={() => rename(s)} aria-label={t.chat.rename} className="rounded p-1.5 text-ink-3 hover:bg-surface hover:text-ink">
              <Pencil className="h-3.5 w-3.5" />
            </button>
            <button type="button" onClick={() => remove(s)} aria-label={t.common.delete} className="rounded p-1.5 text-ink-3 hover:bg-surface hover:text-red-ink">
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </span>
        </li>
      ))}
    </ul>
  );

  return (
    <div className="flex h-[calc(100dvh-61px-3.5rem-env(safe-area-inset-bottom))] min-h-0 lg:h-dvh">
      {/* History (desktop) */}
      <aside className="hidden w-64 shrink-0 flex-col border-e border-line xl:flex">
        <div className="p-3">
          <button type="button" onClick={newChat} className={`${buttonClass.secondary} w-full`}>
            <Plus className="h-4 w-4" />
            {t.chat.newChat}
          </button>
        </div>
        <p className="px-4 pb-1 text-xs font-medium text-ink-3">{t.chat.history}</p>
        <div className="flex-1 overflow-y-auto px-2 pb-4">{historyList}</div>
      </aside>

      <section className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center justify-between gap-2 border-b border-line px-4 py-2.5">
          <h1 className="truncate font-semibold">
            {sessions.find((s) => s.id === sessionId)?.title || t.chat.title}
          </h1>
          <div className="flex shrink-0 items-center gap-1 xl:hidden">
            <button type="button" onClick={() => historyRef.current?.showModal()} className={buttonClass.ghost}>
              <History className="h-4 w-4" />
              <span className="hidden sm:inline">{t.chat.history}</span>
            </button>
            <button type="button" onClick={newChat} aria-label={t.chat.newChat} className={buttonClass.ghost}>
              <Plus className="h-4 w-4" />
            </button>
          </div>
        </div>

        {course && (
          <div className="flex items-center justify-between gap-3 border-b border-line bg-amber-wash px-4 py-2 text-sm">
            <p className="min-w-0 truncate">
              <BookOpenText className="me-1.5 inline h-4 w-4 align-[-3px]" aria-hidden />
              {t.chat.scope} <strong>{course.name}</strong> <span className="text-ink-2">· {t.chat.scopeHint}</span>
            </p>
            <button
              type="button"
              onClick={() => {
                setCourse(null);
                router.replace(sessionId ? `/chat?session=${sessionId}` : '/chat', { scroll: false });
              }}
              aria-label={t.chat.scopeClear}
              title={t.chat.scopeClear}
              className="rounded p-1 text-ink-2 hover:bg-surface"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        <div
          ref={scrollRef}
          onScroll={(e) => {
            const el = e.currentTarget;
            pinnedToBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
          }}
          className="flex-1 overflow-y-auto"
          aria-live="polite"
          aria-busy={busy}
        >
          <div className="mx-auto max-w-3xl px-4 py-6">
            {messages.length === 0 ? (
              <EmptyState line={line} setLine={setLine} onPick={(q) => send(q)} hasCourse={!!course} />
            ) : (
              <ol className="space-y-7">
                {messages.map((m) =>
                  m.role === 'user' ? (
                    <li key={m.id} className="flex justify-end">
                      <p className="max-w-[85%] rounded-lg rounded-ee-sm bg-ink px-4 py-2.5 text-[15px] whitespace-pre-wrap text-surface">
                        {m.content}
                      </p>
                    </li>
                  ) : (
                    <li key={m.id}>
                      {m.streaming && !m.content ? (
                        <span role="status" className="inline-flex items-center gap-2 text-sm text-ink-3">
                          <span aria-hidden className="h-2 w-2 animate-pulse rounded-full bg-red" />
                          {t.common.loading}
                        </span>
                      ) : (
                        <>
                          <Answer text={m.content} citations={m.citations ?? []} streaming={m.streaming} />
                          {m.grounded === false && !m.streaming && (
                            <p className="mt-3 flex items-start gap-2 rounded-md bg-amber-wash px-3 py-2 text-sm text-ink">
                              <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber" aria-hidden />
                              {t.chat.unverified}
                            </p>
                          )}
                          {!m.streaming && m.id !== STREAMING_ID && (
                            <MessageActions
                              message={m}
                              canRegenerate={m.id === lastAssistantId && !busy && !!sessionId}
                              onRegenerate={() => send('', true)}
                              onRate={(r) => rate(m, r)}
                            />
                          )}
                        </>
                      )}
                    </li>
                  ),
                )}
              </ol>
            )}
          </div>
        </div>

        <Composer
          inputRef={inputRef}
          value={input}
          onChange={setInput}
          busy={busy}
          onSend={() => send(input)}
          onStop={() => abortRef.current?.abort()}
          placeholder={course ? fill(t.chat.placeholderCourse, { course: course.name }) : t.chat.placeholder}
        />
      </section>

      <dialog
        ref={historyRef}
        onClick={(e) => e.target === historyRef.current && historyRef.current?.close()}
        className="m-0 ms-auto h-dvh max-h-dvh w-[min(22rem,90vw)] border-s border-line bg-surface p-0 text-ink backdrop:bg-black/40"
      >
        <div className="flex items-center justify-between border-b border-line px-4 py-3">
          <p className="font-semibold">{t.chat.history}</p>
          <button type="button" onClick={() => historyRef.current?.close()} aria-label={t.common.close} className="rounded p-1.5 hover:bg-sunken">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="p-2">{historyList}</div>
      </dialog>
    </div>
  );
}

function EmptyState({
  line, setLine, onPick, hasCourse,
}: { line: Line; setLine: (l: Line) => void; onPick: (q: string) => void; hasCourse: boolean }) {
  const t = useT();
  const lines = hasCourse ? LINES : LINES.filter((l) => l !== 'learning');
  return (
    <div className="pt-4 sm:pt-10">
      <h2 className="placard text-[clamp(2rem,5vw,3rem)]">{t.chat.emptyTitle}</h2>
      <p className="mt-2 text-ink-2">{t.chat.emptySub}</p>
      <div role="group" aria-label={t.landing.boardLabel} className={`mt-6 grid grid-cols-2 gap-3 ${hasCourse ? 'sm:grid-cols-4' : 'sm:grid-cols-3'}`}>
        {lines.map((l) => (
          <Placard key={l} fr={t.lines[l].fr} ar={t.lines[l].ar} size="sm" pressed={line === l} onClick={() => setLine(l)} />
        ))}
      </div>
      <ul className="mt-5 space-y-2">
        {t.starters[line].map((q) => (
          <li key={q}>
            <button
              type="button"
              onClick={() => onPick(q)}
              className="w-full rounded-md border border-line bg-surface px-4 py-3 text-start text-[15px] hover:border-ink"
            >
              {q}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function MessageActions({
  message, canRegenerate, onRegenerate, onRate,
}: { message: ChatMessage; canRegenerate: boolean; onRegenerate: () => void; onRate: (r: 0 | 1) => void }) {
  const t = useT();
  const [copied, setCopied] = useState(false);
  const icon = 'h-4 w-4';
  const btn = 'inline-flex h-8 w-8 items-center justify-center rounded-md text-ink-3 hover:bg-sunken hover:text-ink';
  return (
    <div className="mt-2 flex items-center gap-0.5">
      <button
        type="button"
        aria-label={copied ? t.chat.copied : t.chat.copy}
        title={copied ? t.chat.copied : t.chat.copy}
        className={btn}
        onClick={() => {
          navigator.clipboard?.writeText(message.content).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
          });
        }}
      >
        {copied ? <Check className={icon} /> : <Copy className={icon} />}
      </button>
      {canRegenerate && (
        <button type="button" aria-label={t.chat.regenerate} title={t.chat.regenerate} className={btn} onClick={onRegenerate}>
          <RotateCcw className={icon} />
        </button>
      )}
      <button
        type="button"
        aria-label={t.chat.helpful}
        aria-pressed={message.rating === 1}
        title={t.chat.helpful}
        className={`${btn} ${message.rating === 1 ? 'text-ok' : ''}`}
        onClick={() => onRate(1)}
      >
        <ThumbsUp className={icon} />
      </button>
      <button
        type="button"
        aria-label={t.chat.notHelpful}
        aria-pressed={message.rating === 0}
        title={t.chat.notHelpful}
        className={`${btn} ${message.rating === 0 ? 'text-red-ink' : ''}`}
        onClick={() => onRate(0)}
      >
        <ThumbsDown className={icon} />
      </button>
    </div>
  );
}

function Composer({
  inputRef, value, onChange, busy, onSend, onStop, placeholder,
}: {
  inputRef: React.RefObject<HTMLTextAreaElement | null>;
  value: string;
  onChange: (v: string) => void;
  busy: boolean;
  onSend: () => void;
  onStop: () => void;
  placeholder: string;
}) {
  const t = useT();
  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value, inputRef]);

  return (
    <div className="border-t border-line bg-ground px-4 pt-3 pb-3">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSend();
        }}
        className="mx-auto flex max-w-3xl items-end gap-2 rounded-lg border-2 border-ink bg-surface p-1.5 ps-3"
      >
        <label htmlFor="composer" className="sr-only">
          {placeholder}
        </label>
        <textarea
          id="composer"
          ref={inputRef}
          rows={1}
          value={value}
          maxLength={4000}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault();
              if (!busy) onSend();
            }
          }}
          placeholder={placeholder}
          aria-describedby="composer-hint"
          className="max-h-[200px] min-h-10 flex-1 resize-none bg-transparent py-2 text-[15px] leading-6 text-ink outline-none placeholder:text-ink-3"
        />
        {busy ? (
          <button type="button" onClick={onStop} aria-label={t.chat.stop} title={t.chat.stop} className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-ink text-surface">
            <Square className="h-3.5 w-3.5 fill-current" />
          </button>
        ) : (
          <button
            type="submit"
            disabled={!value.trim()}
            aria-label={t.chat.send}
            title={t.chat.send}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-red text-on-red disabled:opacity-40"
          >
            <ArrowUp className="h-[18px] w-[18px]" />
          </button>
        )}
      </form>
      <p id="composer-hint" className="mx-auto mt-1.5 max-w-3xl text-center text-[11px] text-ink-3">
        <span className="hidden sm:inline">{t.chat.keyboardHint} · </span>
        {t.chat.disclaimer}
      </p>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense>
      <Chat />
    </Suspense>
  );
}
