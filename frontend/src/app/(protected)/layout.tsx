'use client';

import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Bell, BookOpenText, CalendarDays, Home, LogOut, MessageSquareText, ShieldCheck, UserRound } from 'lucide-react';
import { Mark } from '@/components/Placard';
import { LocaleToggle, ThemeToggle, buttonClass } from '@/components/ui';
import { api } from '@/lib/api';
import { formatDate, useLocale, useT } from '@/lib/i18n';
import { ProfileProvider, useProfile } from '@/lib/profile';
import type { Notification } from '@/lib/types';

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProfileProvider>
      <Shell>{children}</Shell>
    </ProfileProvider>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  const t = useT();
  const pathname = usePathname();
  const router = useRouter();
  const { profile } = useProfile();

  // A new account answers the onboarding questions once before anything else.
  useEffect(() => {
    if (profile && !profile.onboarding_completed && pathname !== '/onboarding') router.replace('/onboarding');
  }, [profile, pathname, router]);

  const nav = [
    { href: '/dashboard', label: t.nav.dashboard, icon: Home },
    { href: '/chat', label: t.nav.chat, icon: MessageSquareText },
    { href: '/courses', label: t.nav.courses, icon: BookOpenText },
    { href: '/profile', label: t.nav.profile, icon: UserRound },
    ...(profile?.role === 'admin' ? [{ href: '/admin', label: t.nav.admin, icon: ShieldCheck }] : []),
  ];

  const signOut = async () => {
    await api('auth/logout', { method: 'POST' }).catch(() => {});
    router.replace('/login');
    router.refresh();
  };

  const isActive = (href: string) => pathname === href || pathname.startsWith(`${href}/`);
  const notifications = useNotifications();
  const railRef = useRef<HTMLElement>(null);
  const railBeam = useLimelight(railRef, 'v', pathname + nav.length);
  const barRef = useRef<HTMLUListElement>(null);
  const barBeam = useLimelight(barRef, 'h', pathname + nav.length);

  return (
    <div className="flex min-h-dvh flex-col lg:h-dvh lg:flex-row">
      {/* Desktop rail */}
      <aside className="hidden w-60 shrink-0 flex-col border-e border-line bg-surface lg:flex">
        <div className="band" />
        <div className="flex items-center justify-between px-5 pt-5 pb-6">
          <Mark href="/dashboard" />
          <Notifications id="notifications-rail" {...notifications} />
        </div>
        <nav ref={railRef} aria-label={t.nav.menu} className="relative mx-3 flex-1 space-y-1">
          <span ref={railBeam} aria-hidden className="limelight limelight-v" />
          {nav.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              aria-current={isActive(href) ? 'page' : undefined}
              className={`relative flex min-h-11 items-center gap-3 rounded-md px-3 text-[15px] transition-colors ${
                isActive(href) ? 'font-semibold text-ink' : 'text-ink-2 hover:bg-sunken hover:text-ink'
              }`}
            >
              <Icon className="h-[18px] w-[18px]" aria-hidden />
              {label}
            </Link>
          ))}
        </nav>
        <div className="border-t border-line p-3">
          {profile && (
            <p className="truncate px-2 pb-2 text-sm font-medium" title={profile.email}>
              {profile.full_name || profile.email}
            </p>
          )}
          <div className="flex items-center gap-1">
            <LocaleToggle />
            <ThemeToggle />
            <button type="button" onClick={signOut} aria-label={t.common.signOut} title={t.common.signOut} className={`${buttonClass.ghost} ms-auto w-10 px-0`}>
              <LogOut className="h-[18px] w-[18px] rtl:-scale-x-100" />
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile top bar */}
      <header className="sticky top-0 z-30 border-b border-line bg-surface lg:hidden">
        <div className="band" />
        <div className="flex h-14 items-center justify-between px-3">
          <Mark href="/dashboard" compact />
          <div className="flex items-center gap-0.5">
            <LocaleToggle />
            <ThemeToggle />
            <Notifications id="notifications-bar" {...notifications} />
            <button type="button" onClick={signOut} aria-label={t.common.signOut} className={`${buttonClass.ghost} w-10 px-0`}>
              <LogOut className="h-[18px] w-[18px] rtl:-scale-x-100" />
            </button>
          </div>
        </div>
      </header>

      <main id="main" className="flex min-h-0 flex-1 flex-col pb-16 lg:overflow-y-auto lg:pb-0">
        {children}
      </main>

      {/* Mobile tab bar */}
      <nav aria-label={t.nav.menu} className="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-surface pb-[env(safe-area-inset-bottom)] lg:hidden">
        <ul ref={barRef} className="relative flex">
          <li aria-hidden className="contents">
            <span ref={barBeam} className="limelight limelight-h" />
          </li>
          {nav.map(({ href, label, icon: Icon }) => (
            <li key={href} className="flex-1">
              <Link
                href={href}
                aria-current={isActive(href) ? 'page' : undefined}
                className={`flex min-h-14 flex-col items-center justify-center gap-0.5 text-[11px] ${
                  isActive(href) ? 'font-semibold text-ink' : 'text-ink-3'
                }`}
              >
                <Icon className="h-5 w-5" aria-hidden />
                {label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}

/** Positions the "limelight" beam over the current nav item (vertical rail
 * or horizontal tab bar) and keeps it there on resize. Writes the transform
 * straight to the element, so the glide is a CSS transition. */
function useLimelight(containerRef: React.RefObject<HTMLElement | null>, axis: 'v' | 'h', key: string) {
  const beamRef = useRef<HTMLSpanElement>(null);
  useLayoutEffect(() => {
    const place = () => {
      const beam = beamRef.current;
      const active = containerRef.current?.querySelector<HTMLElement>('[aria-current="page"]');
      if (!beam) return;
      if (!active) {
        beam.style.opacity = '0';
        return;
      }
      beam.style.opacity = '1';
      if (axis === 'v') {
        beam.style.transform = `translateY(${active.offsetTop}px)`;
        beam.style.height = `${active.offsetHeight}px`;
      } else {
        const li = active.parentElement as HTMLElement;
        beam.style.transform = `translateX(${li.offsetLeft}px)`;
        beam.style.width = `${li.offsetWidth}px`;
      }
    };
    place();
    window.addEventListener('resize', place);
    return () => window.removeEventListener('resize', place);
  }, [containerRef, axis, key]);
  return beamRef;
}

const SEEN_KEY = 'fsb:seen-notifications';

function useNotifications() {
  const [items, setItems] = useState<Notification[]>([]);
  const [unseen, setUnseen] = useState(0);

  useEffect(() => {
    api<Notification[]>('notifications')
      .then((list) => {
        setItems(list);
        let seen: string[] = [];
        try {
          seen = JSON.parse(localStorage.getItem(SEEN_KEY) ?? '[]');
        } catch {}
        setUnseen(list.filter((n) => !seen.includes(n.id)).length);
      })
      .catch(() => {});
  }, []);

  const markSeen = () => {
    try {
      localStorage.setItem(SEEN_KEY, JSON.stringify(items.map((n) => n.id)));
    } catch {}
    setUnseen(0);
  };
  return { items, unseen, markSeen };
}

/** Classroom due dates and calendar dates for the next two weeks, in a native
 * popover (light-dismiss and Esc for free). */
function Notifications({ id, items, unseen, markSeen }: { id: string } & ReturnType<typeof useNotifications>) {
  const t = useT();
  const locale = useLocale();
  return (
    <>
      <button
        type="button"
        popoverTarget={id}
        aria-label={`${t.nav.notifications}${unseen ? ` (${unseen})` : ''}`}
        className={`${buttonClass.ghost} relative w-10 px-0`}
      >
        <Bell className="h-[18px] w-[18px]" />
        {unseen > 0 && (
          <span aria-hidden className="absolute top-1.5 end-1.5 min-w-4 rounded-full bg-red px-1 text-[10px] leading-4 font-semibold text-on-red">
            {unseen}
          </span>
        )}
      </button>
      <div
        id={id}
        popover="auto"
        onToggle={(e) => e.newState === 'open' && markSeen()}
        className="fixed inset-x-3 top-16 m-0 ms-auto max-h-[70dvh] w-auto overflow-y-auto rounded-lg border border-line bg-surface p-0 text-ink shadow-[0_18px_40px_-16px_rgb(0_0_0/0.4)] sm:inset-x-auto sm:end-4 sm:w-[22rem] lg:start-[15.5rem] lg:end-auto lg:top-6"
      >
        <p className="border-b border-line px-4 py-3 text-sm font-semibold">{t.nav.notifications}</p>
        {items.length === 0 ? (
          <p className="px-4 py-6 text-sm text-ink-3">{t.nav.noNotifications}</p>
        ) : (
          <ul className="divide-y divide-line">
            {items.map((n) => (
              <li key={n.id} className="flex gap-3 px-4 py-3">
                <CalendarDays className={`mt-0.5 h-4 w-4 shrink-0 ${n.kind === 'deadline' ? 'text-red' : 'text-amber'}`} aria-hidden />
                <div className="min-w-0 text-sm">
                  <p className="font-medium">{n.title}</p>
                  <p className="text-ink-3">
                    {n.kind === 'deadline' ? t.nav.deadline : t.nav.calendar} · {formatDate(n.date, locale, n.kind === 'deadline')} · {n.detail}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}
