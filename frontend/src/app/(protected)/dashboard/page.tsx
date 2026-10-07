'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowLeft, ArrowRight, BookOpenText, CalendarDays, MessageSquareText, Plus } from 'lucide-react';
import { buttonClass } from '@/components/ui';
import { api } from '@/lib/api';
import { fill } from '@/lib/dictionary';
import { formatDate, useLocale, useT } from '@/lib/i18n';
import { useProfile } from '@/lib/profile';
import { PENDING_QUESTION_KEY, type ChatSession, type EnrolledCourse, type Notification } from '@/lib/types';

export default function DashboardPage() {
  const t = useT();
  const locale = useLocale();
  const router = useRouter();
  const { profile } = useProfile();
  const [sessions, setSessions] = useState<ChatSession[] | null>(null);
  const [courses, setCourses] = useState<EnrolledCourse[] | null>(null);
  const [upcoming, setUpcoming] = useState<Notification[]>([]);
  const [question, setQuestion] = useState('');
  const Arrow = locale === 'ar' ? ArrowLeft : ArrowRight;

  useEffect(() => {
    api<ChatSession[]>('chat/sessions').then(setSessions).catch(() => setSessions([]));
    api<EnrolledCourse[]>('courses/mine').then(setCourses).catch(() => setCourses([]));
    api<Notification[]>('notifications').then(setUpcoming).catch(() => {});
  }, []);

  const firstName = profile?.full_name?.split(' ')[0];
  const profileIncomplete = profile && (!profile.program || !profile.academic_year) && profile.student_status === 'enrolled';

  const ask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    try {
      sessionStorage.setItem(PENDING_QUESTION_KEY, question.trim());
    } catch {}
    router.push('/chat');
  };

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:py-12">
      <h1 className="placard text-[clamp(2.2rem,5vw,3.4rem)]">
        {firstName ? fill(t.dashboard.hello, { name: firstName }) : t.dashboard.helloAnon}
      </h1>
      <p className="mt-2 text-ink-2">{t.dashboard.lead}</p>

      <form onSubmit={ask} className="mt-6 flex max-w-3xl gap-2 rounded-lg border-2 border-ink bg-surface p-1.5 ps-3">
        <label htmlFor="dash-ask" className="sr-only">
          {t.dashboard.ask}
        </label>
        <input
          id="dash-ask"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={t.chat.placeholder}
          maxLength={4000}
          className="min-h-10 flex-1 bg-transparent text-[15px] outline-none placeholder:text-ink-3"
        />
        <button type="submit" disabled={!question.trim()} aria-label={t.dashboard.ask} className={`${buttonClass.primary} min-h-10 px-3 sm:px-4`}>
          <span className="max-sm:hidden">{t.dashboard.ask}</span>
          <Arrow className="h-4 w-4" />
        </button>
      </form>

      {profileIncomplete && (
        <p className="mt-4 flex max-w-3xl flex-wrap items-center gap-x-3 gap-y-1 rounded-md bg-amber-wash px-4 py-3 text-sm">
          {t.dashboard.completeProfile}
          <Link href="/profile" className="font-semibold underline underline-offset-2">
            {t.dashboard.completeAction}
          </Link>
        </p>
      )}

      <div className="mt-12 grid gap-12 lg:grid-cols-[1.4fr_1fr]">
        <section aria-labelledby="recent">
          <h2 id="recent" className="text-lg font-semibold">{t.dashboard.recent}</h2>
          <ul className="mt-3 divide-y divide-line border-y border-line">
            {sessions === null && <li className="py-4 text-sm text-ink-3">{t.common.loading}</li>}
            {sessions?.length === 0 && <li className="py-4 text-sm text-ink-3">{t.dashboard.noRecent}</li>}
            {sessions?.slice(0, 6).map((s) => (
              <li key={s.id}>
                <Link href={`/chat?session=${s.id}`} className="flex items-center gap-3 py-3 hover:text-red-ink">
                  <MessageSquareText className="h-4 w-4 shrink-0 text-ink-3" aria-hidden />
                  <span className="min-w-0 flex-1 truncate">{s.title || t.chat.untitled}</span>
                  <span className="shrink-0 text-xs text-ink-3">{formatDate(s.updated_at ?? s.created_at, locale)}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <div className="space-y-12">
          {upcoming.length > 0 && (
            <section aria-labelledby="upcoming">
              <h2 id="upcoming" className="text-lg font-semibold">{t.dashboard.upcoming}</h2>
              <ul className="mt-3 space-y-3">
                {upcoming.slice(0, 4).map((n) => (
                  <li key={n.id} className="flex gap-3 text-sm">
                    <CalendarDays className={`mt-0.5 h-4 w-4 shrink-0 ${n.kind === 'deadline' ? 'text-red' : 'text-amber'}`} aria-hidden />
                    <span>
                      <span className="font-medium">{n.title}</span>
                      <span className="block text-ink-3">
                        {formatDate(n.date, locale, n.kind === 'deadline')} · {n.detail}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section aria-labelledby="mycourses">
            <div className="flex items-center justify-between">
              <h2 id="mycourses" className="text-lg font-semibold">{t.dashboard.courses}</h2>
              <Link href="/courses" className={`${buttonClass.ghost} -me-3`}>
                <Plus className="h-4 w-4" />
                {t.dashboard.addCourse}
              </Link>
            </div>
            {courses?.length === 0 && <p className="mt-3 text-sm text-ink-3">{t.dashboard.noCourses}</p>}
            <ul className="mt-3 space-y-2">
              {courses?.map((c) => (
                <li key={c.id}>
                  <Link
                    href={`/chat?course=${c.id}&name=${encodeURIComponent(c.name)}`}
                    className="flex items-center gap-3 rounded-md border border-line bg-surface px-3 py-2.5 hover:border-ink"
                  >
                    <BookOpenText className="h-4 w-4 shrink-0 text-ink-3" aria-hidden />
                    <span className="min-w-0 flex-1 truncate text-sm font-medium">{c.name}</span>
                    <span className="shrink-0 text-xs text-ink-3">{fill(t.dashboard.materials, { n: c.material_count })}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}
