'use client';

import { AnimatedPaths } from '@/components/fx/blocks';
import { Mark } from '@/components/Placard';
import { LocaleToggle, ThemeToggle } from '@/components/ui';
import { useT } from '@/lib/i18n';

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const t = useT();
  return (
    <div className="flex min-h-dvh flex-col">
      <div className="band" />
      <div className="grid flex-1 lg:grid-cols-[1fr_1.05fr]">
        {/* Split login: route lines drifting behind the brand and its promise. */}
        <aside className="on-dark relative hidden overflow-hidden bg-[#0e0f12] text-ink lg:flex lg:flex-col lg:justify-between lg:p-10">
          <AnimatedPaths className="absolute inset-0 h-full w-full" />
          <div aria-hidden className="absolute inset-x-0 bottom-0 h-48 bg-gradient-to-t from-[#0e0f12] from-40% to-transparent" />
          <div className="relative">
            <Mark />
          </div>
          <div className="relative">
            <p className="placard max-w-[14ch] text-[clamp(2.2rem,3.6vw,3.4rem)] leading-[1.05] text-balance">{t.landing.headline}</p>
            <blockquote className="mt-6 max-w-[40ch] border-s border-line-strong ps-4 text-lg leading-relaxed text-ink-2">
              {t.auth.asideQuote}
            </blockquote>
          </div>
          <p className="relative max-w-[48ch] text-xs text-ink-3">{t.landing.footer}</p>
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
