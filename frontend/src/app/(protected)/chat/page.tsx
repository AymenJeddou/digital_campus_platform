'use client';

import { useEffect, useState, useRef } from 'react';
import { chatService, ChatSession, ChatMessage, Citation } from '@/lib/services/chat';
import { Send, Bot, User, Plus, MessageSquare, Sparkles, Trash2, FileText, Loader2, Paperclip } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';

// ─────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────

function deduplicateCitations(citations: Citation[]): {
  unique: Citation[];
  indexMap: number[];
} {
  const seen = new Map<string, number>();
  const unique: Citation[] = [];
  const indexMap: number[] = [];

  for (const c of citations) {
    const key = `${c.document}::${c.page}`;
    if (!seen.has(key)) {
      unique.push(c);
      seen.set(key, unique.length);
    }
    indexMap.push(seen.get(key)!);
  }

  return { unique, indexMap };
}

function parseInlineRefs(text: string, citations: Citation[]): React.ReactNode[] {
  const { indexMap } = deduplicateCitations(citations);
  const lookup = new Map<string, number>();
  citations.forEach((c, i) => {
    const key = `${c.document}::${c.page}`;
    if (!lookup.has(key)) lookup.set(key, indexMap[i]);
  });

  const regex = /\[([^\]]+?),\s*p\.(\d+)\]/g;
  const nodes: React.ReactNode[] = [];
  let cursor = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
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
        className="inline-flex items-center justify-center h-[16px] min-w-[16px] px-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-[10px] font-bold mx-0.5 cursor-default select-none align-super leading-none"
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
    <div className="flex gap-4 max-w-[85%]">
      <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 mt-1">
        <Sparkles className="h-4 w-4 text-white" />
      </div>
      <div className="bg-white dark:bg-[#1a233a] border border-border rounded-2xl px-5 py-4 flex gap-1.5 items-center">
        <span className="h-2 w-2 bg-slate-300 dark:bg-slate-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="h-2 w-2 bg-slate-300 dark:bg-slate-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="h-2 w-2 bg-slate-300 dark:bg-slate-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  );
}

function CitationCards({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null;
  const { unique } = deduplicateCitations(citations);

  return (
    <div className="mt-6">
      <span className="text-[13px] font-bold text-slate-900 dark:text-white mb-3 block">Sources</span>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {unique.map((c, i) => (
          <div
            key={`${c.document}::${c.page}::${i}`}
            title={`${c.document} — Page ${c.page}`}
            className="flex items-center justify-between p-3 rounded-xl bg-card border border-border hover:border-primary/50 transition-colors cursor-pointer group"
          >
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="h-8 w-8 rounded-lg bg-background flex items-center justify-center flex-shrink-0">
                <FileText className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="min-w-0">
                <p className="text-[13px] font-semibold text-foreground truncate group-hover:text-primary transition-colors">
                  {c.document}
                </p>
                <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                  PDF
                </p>
              </div>
            </div>
            <div className="flex-shrink-0 ml-3 h-6 min-w-[24px] px-2 rounded bg-background text-foreground text-[11px] font-bold flex items-center justify-center">
              {i + 1}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AssistantBubble({ content, citations = [] }: { content: string; citations?: Citation[] }) {
  const inlineNodes = citations.length > 0 ? parseInlineRefs(content, citations) : [content];

  return (
    <div className="w-full">
      <div className="whitespace-pre-wrap leading-relaxed text-sm text-slate-700 dark:text-slate-300 mb-4">
        {inlineNodes}
      </div>
      <CitationCards citations={citations} />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────

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

  return (
    <div className="flex flex-col h-full bg-background max-w-5xl mx-auto rounded-xl">
      {/* Header */}
      <div className="flex items-center justify-between pb-6 border-b border-border">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground">AI Assistant</h1>
          <p className="text-sm text-muted-foreground mt-1">Your academic companion</p>
        </div>
        <button
          onClick={handleNewSession}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium border border-border rounded-lg hover:bg-secondary/50 transition-colors bg-background"
        >
          New Chat <Plus className="h-4 w-4" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-8 space-y-6 scrollbar-hide" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <p className="text-muted-foreground text-sm font-medium">Send a message to start the conversation.</p>
          </div>
        ) : (
          messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 mt-1">
                  <Sparkles className="h-4 w-4 text-white" />
                </div>
              )}
              
              <div className={`max-w-[85%] ${msg.role === 'user' ? 'order-1' : 'order-2'}`}>
                {msg.role === 'user' ? (
                  <div className="bg-primary text-primary-foreground rounded-2xl rounded-tr-sm px-5 py-4 text-sm shadow-sm">
                    {msg.content}
                  </div>
                ) : (
                  <div className="bg-card border border-border rounded-2xl p-5 shadow-sm">
                    <AssistantBubble content={msg.content} citations={msg.citations} />
                  </div>
                )}
                <p className={`text-[10px] font-medium text-muted-foreground mt-2 ${msg.role === 'user' ? 'text-right pr-2' : 'pl-2'}`}>
                  {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>

              {msg.role === 'user' && (
                <div className="h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0 mt-1 order-2">
                  <span className="text-white text-[11px] font-bold tracking-wider">SR</span>
                </div>
              )}
            </motion.div>
          ))
        )}
        {isLoading && <TypingIndicator />}
      </div>

      {/* Input Area */}
      <div className="pt-4 pb-2">
        <p className="text-center text-[11px] text-muted-foreground mb-3">
          AI-generated content may be inaccurate. Please verify important information.
        </p>
        <form onSubmit={handleSend} className="relative flex items-center bg-card border border-border rounded-xl shadow-sm focus-within:ring-1 focus-within:ring-primary focus-within:border-primary transition-all p-1.5">
          <button
            type="button"
            className="p-3 text-muted-foreground hover:text-foreground transition-colors"
          >
            <Paperclip className="h-5 w-5" />
          </button>
          
          <input
            ref={inputRef}
            type="text"
            placeholder="Ask a question or type a command..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            className="flex-1 bg-transparent border-none focus:ring-0 text-sm placeholder:text-muted-foreground px-2 py-3 outline-none text-foreground"
          />
          
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="h-10 w-12 flex items-center justify-center rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground disabled:opacity-50 disabled:cursor-not-allowed transition-colors ml-2 mr-1"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
