'use client';

// Layout blocks rebuilt from the 21st.dev picks: Calendar With Event List,
// Empty State Kit and the animated-paths panel of Split Login.

import { useState } from 'react';
import { BookOpenText, CalendarDays, ChevronLeft, ChevronRight, FileText, Inbox, MessageSquareText, SearchX } from 'lucide-react';
import { formatDate, useLocale, useT } from '@/lib/i18n';
import type { Notification } from '@/lib/types';

const sameDay = (a: Date, b: Date) =>
  a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();

/** Month grid with a dot on days that have something, and the list of
 * that month's events (or the selected day's) underneath. */
export function EventCalendar({ events }: { events: Notification[] }) {
  const t = useT();
  const locale = useLocale();
  const tag = locale === 'ar' ? 'ar-TN' : 'fr-FR';
  const today = new Date();
  const [month, setMonth] = useState(new Date(today.getFullYear(), today.getMonth(), 1));
  const [selected, setSelected] = useState<Date | null>(null);

  const first = new Date(month);
  const offset = (first.getDay() + 6) % 7; // weeks start on Monday
  const days = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate();
  const cells = [...Array(offset).fill(null), ...Array.from({ length: days }, (_, i) => new Date(month.getFullYear(), month.getMonth(), i + 1))];
  const dated = events.map((e) => ({ ...e, d: new Date(e.date) }));
  const visible = dated
    .filter((e) => (selected ? sameDay(e.d, selected) : e.d.getMonth() === month.getMonth() && e.d.getFullYear() === month.getFullYear()))
    .sort((a, b) => +a.d - +b.d);
  const weekdays = Array.from({ length: 7 }, (_, i) => new Date(2024, 0, 1 + i).toLocaleDateString(tag, { weekday: 'narrow' }));
  const shift = (n: number) => {
    setSelected(null);
    setMonth(new Date(month.getFullYear(), month.getMonth() + n, 1));
  };

  return (
    <div className="rounded-lg border border-line bg-surface p-4">
      <div className="flex items-center justify-between">
        <p className="font-semibold capitalize">{month.toLocaleDateString(tag, { month: 'long', year: 'numeric' })}</p>
        <div className="flex gap-0.5">
          <button type="button" onClick={() => shift(-1)} aria-label={t.calendar.previous} className="rounded p-1.5 text-ink-2 hover:bg-sunken">
            <ChevronLeft className="h-4 w-4 rtl:-scale-x-100" />
          </button>
          <button type="button" onClick={() => shift(1)} aria-label={t.calendar.next} className="rounded p-1.5 text-ink-2 hover:bg-sunken">
            <ChevronRight className="h-4 w-4 rtl:-scale-x-100" />
          </button>
        </div>
      </div>
      <div className="mt-3 grid grid-cols-7 gap-y-1 text-center text-xs">
        {weekdays.map((w, i) => (
          <span key={i} className="pb-1 text-ink-3">
            {w}
          </span>
        ))}
        {cells.map((day, i) =>
          day ? (
            <button
              key={i}
              type="button"
              onClick={() => setSelected(selected && sameDay(selected, day) ? null : day)}
              aria-pressed={!!selected && sameDay(selected, day)}
              className={`relative mx-auto flex h-8 w-8 items-center justify-center rounded-md tabular-nums ${
                selected && sameDay(selected, day) ? 'bg-ink text-surface' : sameDay(day, today) ? 'font-semibold text-red-ink' : 'text-ink-2 hover:bg-sunken'
              }`}
            >
              {day.getDate()}
              {dated.some((e) => sameDay(e.d, day)) && (
                <span aria-hidden className={`absolute bottom-1 h-1 w-1 rounded-full ${dated.some((e) => sameDay(e.d, day) && e.kind === 'deadline') ? 'bg-red' : 'bg-amber'}`} />
              )}
            </button>
          ) : (
            <span key={i} />
          ),
        )}
      </div>
      <ul className="mt-3 space-y-2 border-t border-line pt-3">
        {visible.length === 0 && <li className="text-sm text-ink-3">{t.calendar.empty}</li>}
        {visible.map((e) => (
          <li key={e.id} className="flex gap-3 text-sm">
            <span className={`mt-1 h-8 w-1 shrink-0 rounded-full ${e.kind === 'deadline' ? 'bg-red' : 'bg-amber'}`} aria-hidden />
            <span className="min-w-0">
              <span className="block truncate font-medium">{e.title}</span>
              <span className="block text-xs text-ink-3">
                {formatDate(e.date, locale, e.kind === 'deadline')} · {e.detail}
              </span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

const EMPTY_ICONS = { chats: MessageSquareText, courses: BookOpenText, materials: FileText, results: SearchX, inbox: Inbox, calendar: CalendarDays };

/** Illustrated empty state: a stacked-card icon, a title, a line of help and
 * an optional action. */
export function EmptyState({
  kind,
  title,
  body,
  action,
}: {
  kind: keyof typeof EMPTY_ICONS;
  title: string;
  body?: string;
  action?: React.ReactNode;
}) {
  const Icon = EMPTY_ICONS[kind];
  return (
    <div className="flex flex-col items-center rounded-lg border border-dashed border-line-strong px-6 py-10 text-center">
      <span className="empty-stack" aria-hidden>
        <span />
        <span />
        <span className="empty-front">
          <Icon className="h-6 w-6" />
        </span>
      </span>
      <p className="mt-5 font-semibold">{title}</p>
      {body && <p className="mt-1 max-w-[42ch] text-sm text-ink-2">{body}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

/** Slowly drifting route lines for the sign-in panel. */
export function AnimatedPaths({ className = '' }: { className?: string }) {
  const paths = Array.from({ length: 18 }, (_, i) => {
    const o = i * 9;
    return `M${-380 + o} ${-189 - o}C${-380 + o} ${-189 - o} ${-312 + o} ${216 - o} ${152 + o} ${343 - o}C${616 + o} ${470 - o} ${684 + o} ${875 - o} ${684 + o} ${875 - o}`;
  });
  return (
    <svg viewBox="0 0 696 316" aria-hidden className={`animated-paths ${className}`} fill="none" preserveAspectRatio="xMidYMid slice">
      {paths.map((d, i) => (
        <path key={i} d={d} stroke="currentColor" strokeWidth={0.6 + i * 0.05} strokeOpacity={0.08 + i * 0.025} style={{ animationDelay: `${-i * 1.3}s` }} />
      ))}
    </svg>
  );
}
