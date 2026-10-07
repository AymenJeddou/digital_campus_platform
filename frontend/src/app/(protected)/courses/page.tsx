'use client';

import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { toast } from 'sonner';
import { BookOpenText, FileText, Link2, MessageSquareText, Plus, RefreshCw, Trash2, Upload, X } from 'lucide-react';
import { buttonClass, inputClass } from '@/components/ui';
import { ApiError, api, errorMessage } from '@/lib/api';
import { fill } from '@/lib/dictionary';
import { formatDate, useLocale, useT } from '@/lib/i18n';
import type { ClassroomStatus, CourseDetail, CourseMaterial, EnrolledCourse } from '@/lib/types';

function Courses() {
  const t = useT();
  const locale = useLocale();
  const router = useRouter();
  const params = useSearchParams();
  const [courses, setCourses] = useState<EnrolledCourse[] | null>(null);
  const [name, setName] = useState('');
  const [adding, setAdding] = useState(false);
  const [classroom, setClassroom] = useState<ClassroomStatus | null>(null);
  const [selected, setSelected] = useState<CourseDetail | null>(null);
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(() => {
    api<EnrolledCourse[]>('courses/mine').then(setCourses).catch(() => setCourses([]));
  }, []);

  const poll = useCallback(
    async function tick() {
      const st = await api<ClassroomStatus>('courses/classroom/status').catch(() => null);
      if (!st) return;
      setClassroom(st);
      if (st.sync_status === 'running') {
        pollRef.current = setTimeout(tick, 2500);
        return;
      }
      load();
    },
    [load],
  );

  useEffect(() => {
    load();
    poll();
    return () => {
      if (pollRef.current) clearTimeout(pollRef.current);
    };
  }, [load, poll]);

  // Back from Google's consent screen: finish the connection with this
  // session (the backend checks the authorization was started by us).
  const handled = useRef(false);
  useEffect(() => {
    const code = params.get('classroom_code');
    const state = params.get('classroom_state');
    const failed = params.get('classroom') === 'error';
    if (handled.current || (!code && !failed)) return;
    handled.current = true;
    router.replace('/courses', { scroll: false });
    if (failed || !code || !state) {
      toast.error(t.courses.connectFailed);
      return;
    }
    api<ClassroomStatus>('courses/classroom/connect', { json: { code, state } })
      .then((st) => {
        setClassroom(st);
        toast.success(t.courses.connected);
      })
      .catch(() => toast.error(t.courses.connectFailed));
  }, [params, router, t]);

  const addCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setAdding(true);
    try {
      await api('courses', { json: { name: name.trim() } });
      setName('');
      toast.success(t.courses.added);
      load();
    } catch (err) {
      toast.error(err instanceof ApiError && err.status === 409 ? err.detail : errorMessage(err, t));
    } finally {
      setAdding(false);
    }
  };

  const removeCourse = async (c: EnrolledCourse) => {
    if (!window.confirm(fill(t.courses.removeConfirm, { name: c.name }))) return;
    try {
      await api(`courses/enroll/${c.id}`, { method: 'DELETE' });
      load();
    } catch (err) {
      toast.error(errorMessage(err, t));
    }
  };

  const connect = async () => {
    try {
      const { authorization_url } = await api<{ authorization_url: string }>('courses/classroom/authorize', { method: 'POST' });
      window.location.href = authorization_url;
    } catch (err) {
      toast.error(err instanceof ApiError && err.status === 503 ? t.courses.notConfigured : errorMessage(err, t));
    }
  };

  const sync = async () => {
    try {
      const res = await api<{ status: string }>('courses/classroom/sync', { method: 'POST' });
      setClassroom((c) => (c ? { ...c, sync_status: res.status as ClassroomStatus['sync_status'] } : c));
      poll();
    } catch (err) {
      toast.error(errorMessage(err, t));
    }
  };

  const disconnect = async () => {
    if (!window.confirm(t.courses.disconnectConfirm)) return;
    await api('courses/classroom', { method: 'DELETE' }).catch(() => {});
    poll();
    setClassroom({ connected: false } as ClassroomStatus);
  };

  const open = async (id: string) => {
    try {
      setSelected(await api<CourseDetail>(`courses/${id}`));
    } catch (err) {
      toast.error(errorMessage(err, t));
    }
  };

  const syncing = classroom?.sync_status === 'running';

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:py-12">
      <h1 className="placard text-[clamp(2.2rem,5vw,3.2rem)]">{t.courses.title}</h1>
      <p className="mt-2 max-w-[60ch] text-ink-2">{t.courses.lead}</p>

      <form onSubmit={addCourse} className="mt-8 flex max-w-2xl gap-2">
        <label htmlFor="course-name" className="sr-only">
          {t.courses.addPlaceholder}
        </label>
        <input
          id="course-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={t.courses.addPlaceholder}
          maxLength={160}
          className={inputClass}
        />
        <button type="submit" disabled={adding || !name.trim()} className={buttonClass.primary}>
          <Plus className="h-4 w-4" />
          {t.courses.add}
        </button>
      </form>

      <section className="mt-6 flex max-w-2xl flex-wrap items-center justify-between gap-3 rounded-lg border border-line bg-surface px-4 py-3">
        <div className="flex min-w-0 items-center gap-3">
          <Link2 className="h-5 w-5 shrink-0 text-ink-3" aria-hidden />
          <div className="min-w-0 text-sm">
            <p className="font-medium">{t.courses.classroom}</p>
            <p className="text-ink-3" role="status">
              {syncing
                ? fill(t.courses.syncing, { n: classroom?.sync_materials_synced ?? 0 })
                : classroom?.sync_status === 'error' && classroom.sync_error
                  ? fill(t.courses.syncFailed, { error: classroom.sync_error })
                  : classroom?.connected
                    ? `${t.courses.classroomOn}${classroom.last_synced_at ? ` · ${fill(t.courses.lastSync, { date: formatDate(classroom.last_synced_at, locale) })}` : ''}${
                        classroom.sync_status === 'success' && classroom.sync_materials_failed
                          ? ` · ${fill(t.courses.syncSkipped, { n: classroom.sync_materials_failed })}`
                          : ''
                      }`
                    : t.courses.classroomOff}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {classroom?.connected ? (
            <>
              <button type="button" onClick={sync} disabled={syncing} className={buttonClass.secondary}>
                <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
                {t.courses.sync}
              </button>
              <button type="button" onClick={disconnect} className={buttonClass.ghost}>
                {t.courses.disconnect}
              </button>
            </>
          ) : (
            <button type="button" onClick={connect} className={buttonClass.secondary}>
              {t.courses.connect}
            </button>
          )}
        </div>
      </section>

      <section className="mt-10">
        {courses === null && <p className="text-sm text-ink-3">{t.common.loading}</p>}
        {courses?.length === 0 && <p className="max-w-[50ch] text-ink-3">{t.courses.empty}</p>}
        {!!courses?.length && (
        <ul className="divide-y divide-line border-y border-line">
          {courses.map((c) => (
            <li key={c.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 py-3">
              <button type="button" onClick={() => open(c.id)} className="flex min-w-0 flex-1 items-center gap-3 text-start">
                <BookOpenText className="h-5 w-5 shrink-0 text-ink-3" aria-hidden />
                <span className="min-w-0">
                  <span className="block truncate font-medium hover:text-red-ink">{c.name}</span>
                  <span className="block text-xs text-ink-3">
                    {fill(t.dashboard.materials, { n: c.material_count })} ·{' '}
                    {c.source === 'google_classroom' ? t.courses.sourceClassroom : t.courses.sourceManual}
                  </span>
                </span>
              </button>
              <div className="flex items-center gap-1">
                <Link href={`/chat?course=${c.id}&name=${encodeURIComponent(c.name)}`} className={buttonClass.ghost}>
                  <MessageSquareText className="h-4 w-4" />
                  {t.courses.ask}
                </Link>
                <button type="button" onClick={() => removeCourse(c)} aria-label={t.courses.remove} title={t.courses.remove} className={`${buttonClass.ghost} w-10 px-0 hover:text-red-ink`}>
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
        )}
      </section>

      {selected && (
        <CourseSheet
          detail={selected}
          onClose={() => setSelected(null)}
          onChanged={async () => {
            setSelected(await api<CourseDetail>(`courses/${selected.id}`));
            load();
          }}
        />
      )}
    </div>
  );
}

function CourseSheet({ detail, onClose, onChanged }: { detail: CourseDetail; onClose: () => void; onChanged: () => void }) {
  const t = useT();
  const locale = useLocale();
  const ref = useRef<HTMLDialogElement>(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    ref.current?.showModal();
  }, []);

  const upload = async (file: File) => {
    setBusy(true);
    const form = new FormData();
    form.set('file', file);
    try {
      await api(`courses/${detail.id}/materials/upload`, { form });
      toast.success(t.courses.uploaded);
      onChanged();
    } catch (err) {
      toast.error(errorMessage(err, t));
    } finally {
      setBusy(false);
    }
  };

  const addText = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api(`courses/${detail.id}/materials`, { json: { title: title.trim(), content: content.trim() } });
      setTitle('');
      setContent('');
      onChanged();
    } catch (err) {
      toast.error(errorMessage(err, t));
    } finally {
      setBusy(false);
    }
  };

  const remove = async (m: CourseMaterial) => {
    if (!window.confirm(fill(t.courses.removeMaterialConfirm, { name: m.title }))) return;
    await api(`courses/${detail.id}/materials/${m.id}`, { method: 'DELETE' }).catch((err) => toast.error(errorMessage(err, t)));
    onChanged();
  };

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onClick={(e) => e.target === ref.current && ref.current?.close()}
      className="m-0 ms-auto h-dvh max-h-dvh w-[min(30rem,100vw)] border-s border-line bg-ground p-0 text-ink backdrop:bg-black/40"
    >
      <div className="sticky top-0 z-10 flex items-start justify-between gap-3 border-b border-line bg-ground px-5 py-4">
        <div className="min-w-0">
          <h2 className="placard truncate text-2xl">{detail.name}</h2>
          <Link href={`/chat?course=${detail.id}&name=${encodeURIComponent(detail.name)}`} className="mt-1 inline-flex items-center gap-1.5 text-sm font-medium text-red-ink underline-offset-2 hover:underline">
            <MessageSquareText className="h-4 w-4" />
            {t.courses.ask}
          </Link>
        </div>
        <button type="button" onClick={() => ref.current?.close()} aria-label={t.common.close} className="rounded p-1.5 hover:bg-sunken">
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="space-y-8 px-5 py-5">
        <section>
          <h3 className="text-sm font-semibold">{t.courses.materials}</h3>
          {detail.materials.length === 0 && <p className="mt-2 text-sm text-ink-3">{t.courses.noMaterials}</p>}
          <ul className="mt-2 divide-y divide-line">
            {detail.materials.map((m) => (
              <li key={m.id} className="flex items-start gap-3 py-2.5">
                <FileText className="mt-0.5 h-4 w-4 shrink-0 text-ink-3" aria-hidden />
                <div className="min-w-0 flex-1 text-sm">
                  <p className="truncate font-medium">{m.title}</p>
                  <p className={m.status === 'error' ? 'text-red-ink' : 'text-ink-3'}>
                    {t.courses.status[m.status]}
                    {m.status === 'ingested' && ` · ${fill(t.courses.chunks, { n: m.chunk_count })}`}
                    {m.due_at && ` · ${fill(t.courses.due, { date: formatDate(m.due_at, locale, true) })}`}
                    {m.status === 'error' && m.error_message && ` · ${m.error_message}`}
                  </p>
                </div>
                <button type="button" onClick={() => remove(m)} aria-label={t.courses.removeMaterial} className="rounded p-1.5 text-ink-3 hover:bg-sunken hover:text-red-ink">
                  <Trash2 className="h-4 w-4" />
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <label className={`flex cursor-pointer flex-col items-center gap-1 rounded-lg border-2 border-dashed border-line-strong bg-surface px-4 py-6 text-center hover:border-ink ${busy ? 'pointer-events-none opacity-60' : ''}`}>
            <Upload className="h-5 w-5 text-ink-2" aria-hidden />
            <span className="font-medium">{busy ? t.courses.uploading : t.courses.upload}</span>
            <span className="text-xs text-ink-3">{t.courses.uploadHint}</span>
            <input
              type="file"
              accept=".pdf,.docx,.pptx,.txt,.md"
              className="sr-only"
              disabled={busy}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) upload(f);
                e.target.value = '';
              }}
            />
          </label>
        </section>

        <form onSubmit={addText} className="space-y-2">
          <h3 className="text-sm font-semibold">{t.courses.pasteTitle}</h3>
          <input aria-label={t.courses.materialTitle} placeholder={t.courses.materialTitle} value={title} onChange={(e) => setTitle(e.target.value)} maxLength={200} className={inputClass} />
          <textarea
            aria-label={t.courses.materialContent}
            placeholder={t.courses.materialContent}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={5}
            className={`${inputClass} resize-y`}
          />
          <button type="submit" disabled={busy || !title.trim() || !content.trim()} className={buttonClass.secondary}>
            <Plus className="h-4 w-4" />
            {t.courses.addText}
          </button>
        </form>
      </div>
    </dialog>
  );
}

export default function CoursesPage() {
  return (
    <Suspense>
      <Courses />
    </Suspense>
  );
}
