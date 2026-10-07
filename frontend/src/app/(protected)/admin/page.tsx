'use client';

import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { FileText, Trash2, Upload } from 'lucide-react';
import { EmptyState } from '@/components/fx/blocks';
import { buttonClass } from '@/components/ui';
import { api, errorMessage } from '@/lib/api';
import { fill } from '@/lib/dictionary';
import { formatDate, useLocale, useT } from '@/lib/i18n';
import { useProfile } from '@/lib/profile';

type Stats = Record<'students' | 'conversations' | 'questions' | 'unanswered' | 'flagged' | 'helpful' | 'not_helpful' | 'documents', number>;
type Unanswered = { id: string; question: string | null; asked_at: string };
type FeedbackRow = { id: number; question: string | null; answer: string; comment: string | null; timestamp: string };
type Doc = { id: string; title: string; uploaded_at: string; is_ingested: boolean; chunk_count: number };
type Tab = 'unanswered' | 'feedback' | 'documents';

export default function AdminPage() {
  const t = useT();
  const locale = useLocale();
  const { profile } = useProfile();
  const [tab, setTab] = useState<Tab>('unanswered');
  const [stats, setStats] = useState<Stats | null>(null);
  const [unanswered, setUnanswered] = useState<Unanswered[] | null>(null);
  const [feedback, setFeedback] = useState<FeedbackRow[] | null>(null);
  const [docs, setDocs] = useState<Doc[] | null>(null);
  const [uploading, setUploading] = useState(false);

  const loadDocs = useCallback(() => api<Doc[]>('documents').then(setDocs).catch(() => setDocs([])), []);

  useEffect(() => {
    if (profile?.role !== 'admin') return;
    api<Stats>('admin/stats').then(setStats).catch(() => {});
    api<Unanswered[]>('admin/unanswered').then(setUnanswered).catch(() => setUnanswered([]));
    api<FeedbackRow[]>('admin/feedback?rating=0').then(setFeedback).catch(() => setFeedback([]));
    loadDocs();
  }, [profile, loadDocs]);

  if (profile && profile.role !== 'admin') {
    return <p className="mx-auto max-w-3xl px-4 py-16 text-ink-2">{t.admin.forbidden}</p>;
  }

  const upload = async (file: File) => {
    setUploading(true);
    const form = new FormData();
    form.set('file', file);
    try {
      await api('documents/upload', { form });
      loadDocs();
      // Indexing runs in the background; refresh once it has had time.
      setTimeout(loadDocs, 8000);
    } catch (err) {
      toast.error(errorMessage(err, t));
    } finally {
      setUploading(false);
    }
  };

  const removeDoc = async (doc: Doc) => {
    if (!window.confirm(fill(t.admin.deleteConfirm, { name: doc.title }))) return;
    await api(`documents/${doc.id}`, { method: 'DELETE' }).catch((err) => toast.error(errorMessage(err, t)));
    loadDocs();
  };

  const tabs: Tab[] = ['unanswered', 'feedback', 'documents'];

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:py-12">
      <h1 className="placard text-[clamp(2.2rem,5vw,3.2rem)]">{t.admin.title}</h1>

      {stats && (
        <dl className="mt-6 grid grid-cols-2 gap-x-6 gap-y-3 border-y border-line py-4 text-sm sm:grid-cols-4">
          {(Object.keys(t.admin.stats) as (keyof Stats)[]).map((key) => (
            <div key={key} className="flex items-baseline justify-between gap-2 sm:block">
              <dt className="text-ink-3">{t.admin.stats[key]}</dt>
              <dd className="font-semibold tabular-nums sm:mt-0.5 sm:text-lg">{stats[key]}</dd>
            </div>
          ))}
        </dl>
      )}

      <div role="tablist" aria-label={t.admin.title} className="mt-8 flex gap-1 border-b border-line">
        {tabs.map((key) => (
          <button
            key={key}
            role="tab"
            id={`tab-${key}`}
            aria-selected={tab === key}
            aria-controls={`panel-${key}`}
            onClick={() => setTab(key)}
            className={`-mb-px border-b-2 px-3 py-2.5 text-sm font-medium ${
              tab === key ? 'border-red text-ink' : 'border-transparent text-ink-3 hover:text-ink'
            }`}
          >
            {t.admin.tabs[key]}
          </button>
        ))}
      </div>

      <div role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`} className="pt-5">
        {tab === 'unanswered' && (
          <>
            <p className="text-sm text-ink-2">{t.admin.unansweredLead}</p>
            <List empty={unanswered?.length === 0} loading={unanswered === null}>
              {unanswered?.map((u) => (
                <li key={u.id} className="flex items-baseline justify-between gap-4 py-3">
                  <span>{u.question ?? '—'}</span>
                  <span className="shrink-0 text-xs text-ink-3">{formatDate(u.asked_at, locale)}</span>
                </li>
              ))}
            </List>
          </>
        )}

        {tab === 'feedback' && (
          <>
            <p className="text-sm text-ink-2">{t.admin.feedbackLead}</p>
            <List empty={feedback?.length === 0} loading={feedback === null}>
              {feedback?.map((f) => (
                <li key={f.id} className="py-4">
                  <p className="text-xs text-ink-3">{formatDate(f.timestamp, locale)}</p>
                  <p className="mt-1 font-medium">{f.question ?? '—'}</p>
                  <p className="mt-1 line-clamp-3 text-sm text-ink-2">{f.answer}</p>
                  {f.comment && <p className="mt-1 text-sm italic">« {f.comment} »</p>}
                </li>
              ))}
            </List>
          </>
        )}

        {tab === 'documents' && (
          <>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-ink-2">{t.admin.documentsLead}</p>
              <label className={`${buttonClass.secondary} cursor-pointer ${uploading ? 'pointer-events-none opacity-60' : ''}`}>
                <Upload className="h-4 w-4" />
                {uploading ? t.courses.uploading : t.admin.upload}
                <input
                  type="file"
                  accept=".pdf,.docx,.pptx,.txt,.md"
                  className="sr-only"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) upload(f);
                    e.target.value = '';
                  }}
                />
              </label>
            </div>
            <List empty={docs?.length === 0} loading={docs === null}>
              {docs?.map((d) => (
                <li key={d.id} className="flex items-center gap-3 py-3">
                  <FileText className="h-4 w-4 shrink-0 text-ink-3" aria-hidden />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-medium">{d.title}</span>
                    <span className="block text-xs text-ink-3">
                      {formatDate(d.uploaded_at, locale)} · {d.is_ingested ? fill(t.admin.ingested, { n: d.chunk_count }) : t.admin.pending}
                    </span>
                  </span>
                  <button type="button" onClick={() => removeDoc(d)} aria-label={t.common.delete} className="rounded p-1.5 text-ink-3 hover:bg-sunken hover:text-red-ink">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </li>
              ))}
            </List>
          </>
        )}
      </div>
    </div>
  );
}

function List({ empty, loading, children }: { empty: boolean; loading: boolean; children: React.ReactNode }) {
  const t = useT();
  if (loading) return <p className="mt-4 text-sm text-ink-3">{t.common.loading}</p>;
  if (empty) return <div className="mt-4"><EmptyState kind="inbox" title={t.admin.none} /></div>;
  return <ul className="mt-3 divide-y divide-line border-y border-line">{children}</ul>;
}
