import type { Metadata, Viewport } from 'next';
import { Lalezar, Rubik } from 'next/font/google';
import { cookies } from 'next/headers';
import { ThemeProvider } from 'next-themes';
import { Toaster } from 'sonner';
import { LocaleProvider } from '@/lib/i18n';
import { LOCALE_COOKIE } from '@/lib/session';
import type { Locale } from '@/lib/dictionary';
import './globals.css';
import './effects.css';

// Rubik (UI) and Lalezar (hand-painted signage) both cover Arabic and Latin,
// so French and Arabic share one voice.
const rubik = Rubik({ variable: '--font-rubik', subsets: ['latin', 'arabic'], display: 'swap' });
const lalezar = Lalezar({ variable: '--font-lalezar', subsets: ['latin', 'arabic'], weight: '400', display: 'swap' });

export const metadata: Metadata = {
  title: { default: 'Platform', template: '%s · Platform' },
  description:
    'Pose tes questions sur la Faculté des Sciences de Bizerte : admissions, cours, démarches. Réponses sourcées depuis les documents officiels.',
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#f4f4f1' },
    { media: '(prefers-color-scheme: dark)', color: '#111215' },
  ],
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const locale: Locale = (await cookies()).get(LOCALE_COOKIE)?.value === 'ar' ? 'ar' : 'fr';
  return (
    <html
      lang={locale}
      dir={locale === 'ar' ? 'rtl' : 'ltr'}
      suppressHydrationWarning
      className={`${rubik.variable} ${lalezar.variable}`}
    >
      <body className="min-h-dvh bg-ground text-ink">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          <LocaleProvider locale={locale}>
            {children}
            <Toaster
              position={locale === 'ar' ? 'top-left' : 'top-right'}
              dir={locale === 'ar' ? 'rtl' : 'ltr'}
              toastOptions={{
                style: { background: 'var(--surface)', color: 'var(--ink)', border: '1px solid var(--line)' },
              }}
            />
          </LocaleProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
