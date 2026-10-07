'use client';

import { Mark, Placard } from '@/components/Placard';
import { LocaleToggle, ThemeToggle } from '@/components/ui';
import { useT } from '@/lib/i18n';
import { LINES } from '@/lib/types';

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const t = useT();
  return (
    <div className="flex min-h-dvh flex-col">
      <div className="band" />
      <div className="grid flex-1 lg:grid-cols-[1fr_1.05fr]">
        {/* The station board: the four lines this account opens. */}
        <aside className="hidden flex-col justify-between border-e border-line bg-sunken p-10 lg:flex">
          <Mark />
          <div>
            <p className="placard text-[clamp(2rem,3.4vw,3rem)] leading-[1.05] text-balance">{t.landing.headline}</p>
            <div className="mt-8 grid grid-cols-2 gap-3">
              {LINES.map((l) => (
                <Placard key={l} fr={t.lines[l].fr} ar={t.lines[l].ar} hint={t.lines[l].hint} size="sm" />
              ))}
            </div>
          </div>
          <p className="max-w-[48ch] text-xs text-ink-3">{t.landing.footer}</p>
        </aside>

        <div className="flex flex-col">
          <div className="flex items-center justify-between px-4 py-4 sm:px-8">
            <span className="lg:invisible">
              <Mark />
            </span>
            <div className="flex items-center gap-1">
              <LocaleToggle />
              <ThemeToggle />
            </div>
          </div>
          <main className="flex flex-1 items-start justify-center px-4 pt-6 pb-16 sm:items-center sm:px-8 sm:pt-0">
            <div className="w-full max-w-[26rem]">{children}</div>
          </main>
        </div>
      </div>
    </div>
  );
}
