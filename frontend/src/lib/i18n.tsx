'use client';

import { createContext, useContext } from 'react';
import { useRouter } from 'next/navigation';
import { dictionaries, type Locale, type Messages } from './dictionary';

import { LOCALE_COOKIE } from './session';

const LocaleContext = createContext<Locale>('fr');

export function LocaleProvider({ locale, children }: { locale: Locale; children: React.ReactNode }) {
  return <LocaleContext.Provider value={locale}>{children}</LocaleContext.Provider>;
}

export function useLocale(): Locale {
  return useContext(LocaleContext);
}

export function useT(): Messages {
  return dictionaries[useContext(LocaleContext)];
}

/** Switch language: the root layout reads the cookie on the server, so a
 * refresh re-renders <html lang dir> without a full reload. */
export function useSwitchLocale() {
  const router = useRouter();
  const locale = useLocale();
  return () => {
    const next: Locale = locale === 'fr' ? 'ar' : 'fr';
    document.cookie = `${LOCALE_COOKIE}=${next}; Path=/; Max-Age=31536000; SameSite=Lax`;
    router.refresh();
  };
}

export function formatDate(iso: string | null | undefined, locale: Locale, withTime = false): string {
  if (!iso) return '';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleDateString(locale === 'ar' ? 'ar-TN' : 'fr-FR', {
    day: 'numeric',
    month: 'short',
    ...(withTime ? { hour: '2-digit', minute: '2-digit' } : {}),
  });
}
