'use client';

import { useEffect, useState, useRef } from 'react';
import { chatService, ChatSession, ChatMessage, Citation } from '@/lib/services/chat';
import { Send, Bot, User, Plus, MessageSquare, Sparkles, Trash2, FileText } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';

// ─────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────

/**
 * Deduplicate citations by document+page, keeping insertion order.
 * Returns { unique, indexMap } where indexMap[i] is the 1-based display
 * number for citations[i].
 */
function deduplicateCitations(citations: Citation[]): {
  unique: Citation[];
  indexMap: number[];
} {
  const seen = new Map<string, number>(); // key -> 1-based number
  const unique: Citation[] = [];
  const indexMap: number[] = [];

  for (const c of citations) {
    const key = `${c.document}::${c.page}`;
    if (!seen.has(key)) {
      unique.push(c);
      seen.set(key, unique.length); // 1-based
    }
    indexMap.push(seen.get(key)!);
  }

  return { unique, indexMap };
}

/**
 * Parse the answer text and replace inline [doc, p.X] markers with
 * React nodes (text + superscript ref numbers).
 *
 * The backend embeds markers like:  …see the syllabus [Introduction, p.4]…
 * We resolve each marker to its 1-based number from the citation list.
 */
function parseInlineRefs(text: string, citations: Citation[]): React.ReactNode[] {
  // Build a quick lookup: "doc::page" -> display number
  const { indexMap } = deduplicateCitations(citations);
  const lookup = new Map<string, number>();
  citations.forEach((c, i) => {
    const key = `${c.document}::${c.page}`;
    if (!lookup.has(key)) lookup.set(key, indexMap[i]);
  });

  // Match [anything, p.digits]
  const regex = /\[([^\]]+?),\s*p\.(\d+)\]/g;
  const nodes: React.ReactNode[] = [];
  let cursor = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    // Plain text before the marker
    if (match.index > cursor) {
      nodes.push(text.slice(cursor, match.index));
    }

    const doc = match[1].trim();
    const page = parseInt(match[2], 10);
    const num = lookup.get(`${doc}::${page}`);

    nodes.push(
      <sup
        key={`ref-${match.index}`}
        title={`${doc} — p.${page}`}
        className="inline-flex items-center justify-center h-[14px] min-w-[14px] px-0.5 rounded bg-indigo-100 text-indigo-700 text-[9px] font-bold mx-0.5 cursor-default select-none align-super leading-none"
      >
        {num ?? '?'}
      </sup>
    );

    cursor = match.index + match[0].length;
  }

  if (cursor < text.length) nodes.push(text.slice(cursor));
  return nodes.length ? nodes : [text];
}

// ─────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="h-7 w-7 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0 mt-0.5">
        <Bot className="h-3.5 w-3.5 text-indigo-600" />
      </div>
      <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 flex gap-1.5 items-center shadow-sm">
        <span className="h-1.5 w-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="h-1.5 w-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="h-1.5 w-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  );
}

/**
 * Renders numbered citation chips below the assistant bubble.
 */
function CitationChips({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null;

  const { unique } = deduplicateCitations(citations);

  return (
    <div className="mt-2.5 pt-2.5 border-t border-gray-100 flex flex-wrap gap-1.5">
      <span className="w-full text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-0.5 flex items-center gap-1">
        <FileText className="h-3 w-3" />
        Sources
      </span>
      {unique.map((c, i) => (
        <div
          key={`${c.document}::${c.page}::${i}`}
          title={`${c.document} — Page ${c.page}`}
          className="group inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-gray-50 border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 transition-all duration-150 cursor-default"
        >
          {/* Number badge */}
          <span className="flex-shrink-0 flex items-center justify-center h-4 min-w-[16px] px-1 rounded bg-indigo-100 text-indigo-700 text-[9px] font-bold group-hover:bg-indigo-200 transition-colors">
            {i + 1}
          </span>
          {/* Document name */}
          <span className="text-[11px] font-medium text-gray-700 group-hover:text-indigo-800 truncate max-w-[140px] transition-colors">
            {c.document}
          </span>
          {/* Page */}
          <span className="flex-shrink-0 text-[10px] text-gray-400 font-medium group-hover:text-indigo-500 transition-colors">
            p.{c.page}
          </span>
        </div>
      ))}
    </div>
  );
}

/**
 * The full assistant message bubble: parsed text + citation chips.
 */
function AssistantBubble({ content, citations = [] }: { content: string; citations?: Citation[] }) {
  const inlineNodes = citations.length > 0 ? parseInlineRefs(content, citations) : [content];

  return (
    <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 max-w-[75%] text-sm leading-relaxed text-gray-800 shadow-sm">
      <p className="whitespace-pre-wrap">{inlineNodes}</p>
      <CitationChips citations={citations} />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────

const SUGGESTED_PROMPTS = [
  'Help me understand a complex topic',
  'Create a study plan for my exams',
  'Recommend courses for my goals',
  'Explain a concept step by step',
];

export default function ChatPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { loadSessions(); }, []);

  useEffect(() => {
    if (currentSessionId) loadMessages(currentSessionId);
    else setMessages([]);
  }, [currentSessionId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const loadSessions = async () => {
    try {
      const data = await chatService.getSessions();
      setSessions(data);
    } catch {
      toast.error('Failed to load sessions');
    }
  };

  const loadMessages = async (sessionId: string) => {
    try {
      const data = await chatService.getMessages(sessionId);
      setMessages(data);
    } catch {
      toast.error('Failed to load messages');
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;
    setInput('');
    setIsLoading(true);

    const tempUser: ChatMessage = {
      id: Date.now().toString(),
      session_id: currentSessionId || '',
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((p) => [...p, tempUser]);

    try {
      const res = await chatService.sendMessage({
        message: text,
        session_id: currentSessionId || undefined,
      });

      if (!currentSessionId) {
        setCurrentSessionId(res.session_id);
        loadSessions();
      }

      // Attach citations to the assistant message so they can be rendered
      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        session_id: res.session_id,
        role: 'assistant',
        content: res.answer,
        citations: res.citations ?? [],
        created_at: new Date().toISOString(),
      };

      setMessages((p) => [...p, assistantMsg]);
    } catch {
      toast.error('Failed to send message');
      setMessages((p) => p.filter((m) => m.id !== tempUser.id));
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleNewSession = () => {
    setCurrentSessionId(null);
    setMessages([]);
    inputRef.current?.focus();
  };

  const handlePromptClick = (prompt: string) => {
    setInput(prompt);
    inputRef.current?.focus();
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">

      {/* ── Session sidebar ─────────────────────────────── */}
      <div className="w-64 border-r border-gray-100 bg-gray-50 flex flex-col flex-shrink-0">
        <div className="p-3 border-b border-gray-100">
          <button
            id="new-chat-btn"
            onClick={handleNewSession}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 text-sm font-semibold text-gray-700 bg-white border border-gray-200 rounded-lg hover:border-indigo-300 hover:text-indigo-700 transition-all duration-150"
          >
            <Plus className="h-4 w-4" />
            New Conversation
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {sessions.length === 0 ? (
            <p className="text-xs text-gray-400 text-center py-8 px-3">No conversations yet.</p>
          ) : (
            <>
              <p className="px-3 py-2 text-[10px] font-semibold text-gray-400 uppercase tracking-widest">
                History
              </p>
              {sessions.map((session) => {
                const isActive = currentSessionId === session.id;
                return (
                  <button
                    key={session.id}
                    onClick={() => setCurrentSessionId(session.id)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg flex items-center gap-2.5 transition-all duration-150 text-xs font-medium ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    <MessageSquare className={`h-3.5 w-3.5 flex-shrink-0 ${isActive ? 'text-indigo-500' : 'text-gray-400'}`} />
                    <span className="truncate">
                      {new Date(session.created_at).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                      })}{' '}
                      Chat
                    </span>
                  </button>
                );
              })}
            </>
          )}
        </div>
      </div>

      {/* ── Main chat area ──────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-white flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center">
              <Sparkles className="h-4 w-4 text-indigo-600" />
            </div>
            <div>
              <p className="text-sm font-bold text-gray-900">Campus AI Assistant</p>
              <div className="flex items-center gap-1.5 mt-px">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                <span className="text-[10px] text-gray-400 font-medium">Online</span>
              </div>
            </div>
          </div>
          {currentSessionId && (
            <button
              onClick={handleNewSession}
              className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
              title="Start new conversation"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6" ref={scrollRef}>
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center gap-6">
              <div className="text-center space-y-2">
                <div className="h-14 w-14 rounded-2xl bg-indigo-50 flex items-center justify-center mx-auto">
                  <Bot className="h-7 w-7 text-indigo-500" />
                </div>
                <p className="text-base font-bold text-gray-800">How can I help you?</p>
                <p className="text-sm text-gray-400 max-w-sm">
                  I can help with course planning, concept explanations, study strategies, and more.
                </p>
              </div>
              <div className="grid grid-cols-2 gap-2 w-full max-w-md">
                {SUGGESTED_PROMPTS.map((p) => (
                  <button
                    key={p}
                    onClick={() => handlePromptClick(p)}
                    className="text-left px-3 py-2.5 rounded-lg border border-gray-200 bg-white text-xs text-gray-600 font-medium hover:border-indigo-300 hover:text-indigo-700 hover:bg-indigo-50 transition-all duration-150"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-5 max-w-3xl mx-auto">
              <AnimatePresence initial={false}>
                {messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.18 }}
                    className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {/* Bot avatar */}
                    {msg.role === 'assistant' && (
                      <div className="h-7 w-7 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Bot className="h-3.5 w-3.5 text-indigo-600" />
                      </div>
                    )}

                    {/* Bubble */}
                    {msg.role === 'assistant' ? (
                      <AssistantBubble content={msg.content} citations={msg.citations} />
                    ) : (
                      <div className="rounded-2xl rounded-tr-sm px-4 py-3 max-w-[75%] text-sm leading-relaxed bg-indigo-600 text-white shadow-sm">
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    )}

                    {/* User avatar */}
                    {msg.role === 'user' && (
                      <div className="h-7 w-7 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <User className="h-3.5 w-3.5 text-gray-500" />
                      </div>
                    )}
                  </motion.div>
                ))}

                {isLoading && (
                  <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                    <TypingIndicator />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}
        </div>

        {/* Input bar */}
        <div className="px-6 py-4 border-t border-gray-100 bg-white flex-shrink-0">
          <form onSubmit={handleSend} className="max-w-3xl mx-auto flex items-center gap-3">
            <input
              id="chat-input"
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Message the AI Assistant…"
              disabled={isLoading}
              className="flex-1 px-4 py-3 text-sm text-gray-900 font-medium bg-gray-50 border border-gray-200 rounded-xl placeholder-gray-400 focus:outline-none focus:border-indigo-400 focus:bg-white focus:ring-2 focus:ring-indigo-500/10 transition-all duration-150 disabled:opacity-60"
            />
            <button
              id="send-message-btn"
              type="submit"
              disabled={isLoading || !input.trim()}
              className="flex-shrink-0 flex items-center justify-center h-10 w-10 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl transition-colors duration-150 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Send className="h-4 w-4" />
              <span className="sr-only">Send</span>
            </button>
          </form>
          <p className="text-center text-[10px] text-gray-300 mt-2">
            AI responses may not always be accurate. Verify important information.
          </p>
        </div>
      </div>
    </div>
  );
}
