'use client';

import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { X } from 'lucide-react';
import { api } from '@/lib/api';
import { useT } from '@/lib/i18n';
import type { Citation } from '@/lib/types';

const CITE_RE = /\[([^\]\n]+?),\s*p\.\s*(\d+)\]/g;

/** Number each distinct (document, page) in the order the answer cites it. */
export function numberCitations(text: string, citations: Citation[]) {
  const order: Citation[] = [];
  const index = new Map<string, number>();
  const add = (document: string, page: number) => {
    const key = `${document}::${page}`;
    if (!index.has(key)) {
      order.push({ document, page });
      index.set(key, order.length);
    }
    return index.get(key)!;
  };
  for (const match of text.matchAll(CITE_RE)) add(match[1].trim(), Number(match[2]));
  for (const c of citations) add(c.document, c.page);
  return { order, index };
}

/** Markdown answer whose inline [Document, p.X] markers become numbered
 * superscripts, followed by the sources printed as ticket stubs. */
export function Answer({ text, citations, streaming }: { text: string; citations: Citation[]; streaming?: boolean }) {
  const t = useT();
  const [open, setOpen] = useState<Citation | null>(null);
  const { order, index } = numberCitations(text, citations);
  const markdown = text.replace(CITE_RE, (_, doc: string, page: string) => {
    const n = index.get(`${doc.trim()}::${Number(page)}`);
    return `[${n}](#cite-${n})`;
  });

  return (
    <div>
      <div className="prose-answer text-[15px] text-ink">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            a: ({ href, children }) => {
              const cite = href?.match(/^#cite-(\d+)$/);
              if (!cite) {
                return (
                  <a href={href} target="_blank" rel="noopener noreferrer">
                    {children}
                  </a>
                );
              }
              const source = order[Number(cite[1]) - 1];
              return (
                <button
                  type="button"
                  onClick={() => source && setOpen(source)}
                  title={source ? `${source.document} — ${t.common.page}${source.page}` : undefined}
                  className="mx-0.5 inline-flex h-[1.15rem] min-w-[1.15rem] -translate-y-1 items-center justify-center rounded-[3px] bg-ink px-1 align-baseline text-[11px] font-semibold text-surface hover:bg-red"
                >
                  {cite[1]}
                </button>
              );
            },
          }}
        >
          {markdown}
        </ReactMarkdown>
        {streaming && <span aria-hidden className="ms-0.5 inline-block h-4 w-[2px] translate-y-0.5 animate-pulse bg-red" />}
      </div>

      {!streaming && order.length > 0 && (
        <div className="mt-4">
          <p className="sr-only">{t.chat.sources}</p>
          <ul className="flex flex-wrap gap-2">
            {order.map((source, i) => (
              <li key={`${source.document}-${source.page}`} className="print-in" style={{ animationDelay: `${i * 70}ms` }}>
                <TicketStub n={i + 1} source={source} onOpen={() => setOpen(source)} />
              </li>
            ))}
          </ul>
        </div>
      )}
      {open && <SourceDialog source={open} onClose={() => setOpen(null)} />}
    </div>
  );
}

export function TicketStub({ n, source, onOpen }: { n: number; source: Citation; onOpen?: () => void }) {
  const t = useT();
  return (
    <button
      type="button"
      onClick={onOpen}
      className="stub group inline-flex max-w-[18rem] items-stretch overflow-hidden rounded-[4px] border border-line-strong bg-surface text-start text-xs hover:border-ink"
    >
      <span className="flex items-center bg-ink ps-3 pe-2 font-semibold text-surface tabular-nums group-hover:bg-red">{n}</span>
      <span className="flex min-w-0 flex-col justify-center border-s border-dashed border-line-strong px-2.5 py-1.5">
        <span className="truncate font-medium text-ink">{source.document}</span>
        <span className="text-ink-3 tabular-nums">
          {t.common.page} {source.page}
        </span>
      </span>
    </button>
  );
}

/** The passage behind a citation, in a native <dialog> (focus trap and Esc
 * come with the element). */
function SourceDialog({ source, onClose }: { source: Citation; onClose: () => void }) {
  const t = useT();
  const ref = useRef<HTMLDialogElement>(null);
  const [passages, setPassages] = useState<{ text: string }[] | null>(null);

  useEffect(() => {
    ref.current?.showModal();
    const params = new URLSearchParams({ document: source.document, page: String(source.page) });
    api<{ passages: { text: string }[] }>(`sources?${params}`)
      .then((r) => setPassages(r.passages))
      .catch(() => setPassages([]));
  }, [source]);

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onClick={(e) => e.target === ref.current && ref.current?.close()}
      className="m-auto w-[min(40rem,calc(100vw-2rem))] max-h-[min(80dvh,44rem)] rounded-lg border border-line bg-surface p-0 text-ink shadow-[0_24px_60px_-20px_rgb(0_0_0/0.45)] backdrop:bg-black/45"
    >
      <div className="sticky top-0 flex items-start justify-between gap-4 border-b border-line bg-surface px-5 py-4">
        <div className="min-w-0">
          <p className="text-xs text-ink-3">{t.chat.sourceTitle}</p>
          <h2 className="mt-0.5 font-semibold">
            {source.document} <span className="font-normal text-ink-3">· {t.common.page} {source.page}</span>
          </h2>
        </div>
        <button type="button" onClick={() => ref.current?.close()} aria-label={t.common.close} className="rounded-md p-1.5 text-ink-2 hover:bg-sunken">
          <X className="h-5 w-5" />
        </button>
      </div>
      <div className="space-y-4 px-5 py-4 text-[15px] leading-relaxed">
        {passages === null && <p className="text-ink-3">{t.common.loading}</p>}
        {passages?.length === 0 && <p className="text-ink-3">{t.chat.sourceEmpty}</p>}
        {passages?.map((p, i) => (
          <blockquote key={i} className="prose-answer whitespace-pre-line border-s border-line-strong ps-4 text-ink-2">
            {p.text}
          </blockquote>
        ))}
      </div>
    </dialog>
  );
}
