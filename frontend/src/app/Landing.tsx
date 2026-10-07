'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowRight, ArrowLeft } from 'lucide-react';
import { Answer } from '@/components/Answer';
import { Mark, Placard } from '@/components/Placard';
import { LocaleToggle, ThemeToggle, buttonClass } from '@/components/ui';
import { useLocale, useT } from '@/lib/i18n';
import { LINES, PENDING_QUESTION_KEY, type Line } from '@/lib/types';

export default function Landing({ signedIn }: { signedIn: boolean }) {
  const t = useT();
  const locale = useLocale();
  const router = useRouter();
  const [line, setLine] = useState<Line>('orientation');
  const [question, setQuestion] = useState('');
  const Arrow = locale === 'ar' ? ArrowLeft : ArrowRight;

  const ask = (e: React.FormEvent) => {
    e.preventDefault();
    const q = question.trim();
    if (!q) return;
    try {
      sessionStorage.setItem(PENDING_QUESTION_KEY, q);
    } catch {
      /* private mode: the student just retypes it */
    }
    router.push(signedIn ? '/chat' : '/register');
  };

  return (
    <div className="min-h-dvh">
      <div className="band" />
      <header className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-4 sm:px-6">
        <Mark />
        <nav className="flex items-center gap-1 sm:gap-2">
          <LocaleToggle />
          <ThemeToggle />
          {signedIn ? (
            <Link href="/dashboard" className={`${buttonClass.primary} ms-1 min-h-10 px-4 text-sm`}>
              {t.landing.openApp}
            </Link>
          ) : (
            <>
              <Link href="/login" className={`${buttonClass.ghost} max-sm:hidden`}>
                {t.landing.signIn}
              </Link>
              <Link href="/register" className={`${buttonClass.primary} ms-1 min-h-10 px-4 text-sm`}>
                {t.landing.signUp}
              </Link>
            </>
          )}
        </nav>
      </header>

      <main>
        {/* The station: pick a line, say where you're going. */}
        <section className="mx-auto max-w-6xl px-4 pt-8 pb-14 sm:px-6 sm:pt-14">
          <h1 className="placard max-w-[18ch] text-[clamp(2.4rem,6.4vw,4.9rem)] text-balance text-ink">
            {t.landing.headline}
          </h1>
          <p className="mt-5 max-w-[58ch] text-lg leading-relaxed text-ink-2">{t.landing.sub}</p>

          <div className="mt-10">
            <p id="lines-label" className="text-sm font-medium text-ink-2">
              {t.landing.boardLabel}
            </p>
            <div role="group" aria-labelledby="lines-label" className="mt-3 grid grid-cols-2 gap-3 lg:grid-cols-4">
              {LINES.map((l) => (
                <Placard
                  key={l}
                  fr={t.lines[l].fr}
                  ar={t.lines[l].ar}
                  hint={t.lines[l].hint}
                  pressed={line === l}
                  onClick={() => setLine(l)}
                />
              ))}
            </div>
          </div>

          <form onSubmit={ask} className="mt-6 rounded-lg border-2 border-ink bg-surface p-3 sm:p-4">
            <label htmlFor="ask" className="placard block text-xl text-ink">
              {t.landing.askLabel}
            </label>
            <div className="mt-3 flex flex-col gap-2 sm:flex-row">
              <input
                id="ask"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder={t.landing.askPlaceholder}
                maxLength={4000}
                className="min-h-12 flex-1 rounded-md border border-line-strong bg-ground px-4 text-base text-ink outline-none placeholder:text-ink-3 focus:border-ink"
              />
              <button type="submit" disabled={!question.trim()} className={`${buttonClass.primary} min-h-12 px-6`}>
                {t.landing.ask}
                <Arrow className="h-4 w-4" />
              </button>
            </div>
            <ul className="mt-3 flex flex-wrap gap-2" aria-label={t.lines[line].fr}>
              {t.starters[line].slice(0, line === 'learning' ? 2 : 3).map((s) => (
                <li key={s}>
                  <button
                    type="button"
                    onClick={() => setQuestion(s)}
                    className="rounded-full border border-line bg-ground px-3 py-1.5 text-sm text-ink-2 hover:border-ink hover:text-ink"
                  >
                    {s}
                  </button>
                </li>
              ))}
            </ul>
            {!signedIn && <p className="mt-3 text-xs text-ink-3">{t.landing.askNote}</p>}
          </form>

          {/* A real answer from the knowledge base, labelled as an example. */}
          <figure className="mt-10 max-w-3xl">
            <figcaption className="flex items-center gap-2 text-xs font-medium text-ink-3">
              <span className="rounded-[3px] border border-line-strong px-1.5 py-0.5">{t.common.example}</span>
            </figcaption>
            <p className="mt-3 ms-auto w-fit max-w-[85%] rounded-lg rounded-ee-sm bg-ink px-4 py-2.5 text-[15px] text-surface">
              {t.landing.exampleQuestion}
            </p>
            <div className="mt-3 rounded-lg border border-line bg-surface p-4 sm:p-5">
              <Answer
                text={`${t.landing.exampleAnswer} [${t.landing.exampleSource}, p.0]`}
                citations={[{ document: t.landing.exampleSource, page: 0 }]}
              />
            </div>
          </figure>
        </section>

        {/* Departures board: what the assistant actually knows. */}
        <section className="bg-[#16171b] py-14 text-[#f1f0ec] dark:bg-sunken">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <h2 className="placard text-[clamp(1.8rem,4vw,2.8rem)]">{t.landing.boardTitle}</h2>
            <div className="mt-8 overflow-x-auto">
              <table className="w-full min-w-[40rem] border-collapse text-start">
                <thead>
                  <tr className="border-b border-white/20 text-xs uppercase text-[#ffc14d]">
                    <th scope="col" className="py-3 pe-4 text-start font-medium">{t.landing.boardColumns.topic}</th>
                    <th scope="col" className="py-3 pe-4 text-start font-medium">{t.landing.boardColumns.sources}</th>
                    <th scope="col" className="py-3 text-start font-medium">{t.landing.boardColumns.asks}</th>
                  </tr>
                </thead>
                <tbody>
                  {t.landing.board.map((row) => (
                    <tr key={row.topic} className="border-b border-white/10">
                      <th scope="row" className="placard py-4 pe-4 text-start text-xl font-normal">{row.topic}</th>
                      <td className="py-4 pe-4 text-sm text-[#bcbec5]">{row.sources}</td>
                      <td className="py-4 text-sm text-[#f1f0ec]">« {row.asks} »</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section className="mx-auto grid max-w-6xl gap-8 px-4 py-16 sm:px-6 md:grid-cols-[1fr_1.1fr] md:items-center">
          <div>
            <h2 className="placard text-[clamp(1.8rem,4vw,2.6rem)] text-balance">{t.landing.honestTitle}</h2>
            <p className="mt-4 max-w-[52ch] leading-relaxed text-ink-2">{t.landing.honestBody}</p>
          </div>
          <div className="rounded-lg border border-line bg-surface p-5 text-[15px] text-ink">{t.landing.honestRefusal}</div>
        </section>

        <section className="border-t border-line">
          <div className="mx-auto flex max-w-6xl flex-col items-start gap-5 px-4 py-14 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <h2 className="placard text-[clamp(1.6rem,3.6vw,2.4rem)] text-balance">{t.landing.closeTitle}</h2>
            <Link href={signedIn ? '/chat' : '/register'} className={buttonClass.primary}>
              {signedIn ? t.landing.openApp : t.landing.signUp}
              <Arrow className="h-4 w-4" />
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-8 text-sm text-ink-3 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <Mark />
          <p className="max-w-[70ch]">{t.landing.footer}</p>
        </div>
      </footer>
    </div>
  );
}
