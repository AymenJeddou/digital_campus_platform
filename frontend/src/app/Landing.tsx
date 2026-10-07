'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowRight, ArrowLeft } from 'lucide-react';
import { Answer } from '@/components/Answer';
import { DocumentsIllustration } from '@/components/fx/DocumentsIllustration';
import { Magnetic } from '@/components/fx/interactive';
import { ShaderBackground } from '@/components/fx/ShaderBackground';
import { FlipBoard, Scramble, useTypewriter } from '@/components/fx/text';
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
  const placeholder = useTypewriter(t.starters[line], !question);

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
      {/* ---- Hero: the station at night ---- */}
      <div className="on-dark relative isolate overflow-hidden bg-[#0e0f12] text-ink">
        <div className="absolute inset-0 -z-10">
          <ShaderBackground />
          <div className="absolute inset-0 bg-[linear-gradient(to_bottom,rgb(14_15_18/0.25),rgb(14_15_18/0.55)_70%,#0e0f12)]" />
        </div>
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

        <section className="mx-auto grid max-w-6xl items-center gap-10 px-4 pt-6 pb-12 sm:px-6 lg:grid-cols-[1.25fr_1fr] lg:pt-12 lg:pb-16">
          <div>
            <p className="text-xs font-medium text-ink-2" id="board-label">
              {t.landing.boardLabel2}
            </p>
            <FlipBoard words={t.landing.boardWords} className="mt-2" />
            <h1 className="placard mt-6 max-w-[16ch] text-[clamp(2.4rem,6vw,4.6rem)] text-balance">{t.landing.headline}</h1>
            <p className="mt-5 max-w-[54ch] text-lg leading-relaxed text-ink-2">{t.landing.sub}</p>

            <form onSubmit={ask} className="composer mt-8 rounded-lg border-2 border-ink bg-surface/85 p-3 backdrop-blur-sm sm:p-4">
              <label htmlFor="ask" className="placard block text-xl">
                {t.landing.askLabel}
              </label>
              <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                <input
                  id="ask"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder={placeholder}
                  aria-describedby="ask-note"
                  maxLength={4000}
                  className="min-h-12 flex-1 rounded-md border border-line-strong bg-ground px-4 text-base text-ink outline-none placeholder:text-ink-3 focus:border-ink"
                />
                <Magnetic>
                  <button type="submit" disabled={!question.trim()} className={`${buttonClass.primary} min-h-12 w-full px-6 sm:w-auto`}>
                    {t.landing.ask}
                    <Arrow className="h-4 w-4" />
                  </button>
                </Magnetic>
              </div>
              <ul className="mt-3 flex flex-wrap gap-2" aria-label={t.lines[line].fr}>
                {t.starters[line].slice(0, 2).map((s) => (
                  <li key={s}>
                    <button
                      type="button"
                      onClick={() => setQuestion(s)}
                      className="rounded-full border border-line-strong px-3 py-1.5 text-start text-sm text-ink-2 hover:border-ink hover:text-ink"
                    >
                      {s}
                    </button>
                  </li>
                ))}
              </ul>
              {!signedIn && (
                <p id="ask-note" className="mt-3 text-xs text-ink-3">
                  {t.landing.askNote}
                </p>
              )}
            </form>
          </div>

          <DocumentsIllustration className="mx-auto w-full max-w-[26rem] lg:max-w-none" />
        </section>

        <div className="mx-auto max-w-6xl px-4 pb-12 sm:px-6">
          <p id="lines-label" className="text-sm font-medium text-ink-2">
            {t.landing.boardLabel}
          </p>
          <div role="group" aria-labelledby="lines-label" className="mt-3 grid grid-cols-2 gap-3 lg:grid-cols-4">
            {LINES.map((l) => (
              <Placard key={l} fr={t.lines[l].fr} ar={t.lines[l].ar} hint={t.lines[l].hint} pressed={line === l} onClick={() => setLine(l)} />
            ))}
          </div>
        </div>
      </div>

      <main>
        {/* A real answer from the knowledge base, played out as a conversation. */}
        <section className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
          <span className="rounded-[3px] border border-line-strong px-1.5 py-0.5 text-xs font-medium text-ink-3">{t.common.example}</span>
          <ExampleConversation />
        </section>

        {/* Departures board: what the assistant actually knows. */}
        <section className="bg-[#16171b] py-14 text-[#f1f0ec] dark:bg-sunken">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <Scramble as="h2" text={t.landing.boardTitle} className="placard text-[clamp(1.8rem,4vw,2.8rem)]" />
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
            <Scramble as="h2" text={t.landing.honestTitle} className="placard text-[clamp(1.8rem,4vw,2.6rem)] text-balance" />
            <p className="mt-4 max-w-[52ch] leading-relaxed text-ink-2">{t.landing.honestBody}</p>
          </div>
          <div className="rounded-lg border border-line bg-surface p-5 text-[15px] text-ink">{t.landing.honestRefusal}</div>
        </section>

        <section className="border-t border-line">
          <div className="mx-auto flex max-w-6xl flex-col items-start gap-5 px-4 py-14 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <Scramble as="h2" text={t.landing.closeTitle} className="placard text-[clamp(1.6rem,3.6vw,2.4rem)] text-balance" />
            <Magnetic>
              <Link href={signedIn ? '/chat' : '/register'} className={buttonClass.primary}>
                {signedIn ? t.landing.openApp : t.landing.signUp}
                <Arrow className="h-4 w-4" />
              </Link>
            </Magnetic>
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

/** The example plays out like a real chat when it scrolls into view:
 * question, the assistant searching, then the cited answer. */
function ExampleConversation() {
  const t = useT();
  const ref = useRef<HTMLDivElement>(null);
  const [step, setStep] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const timers: ReturnType<typeof setTimeout>[] = [];
    const observer = new IntersectionObserver(([entry]) => {
      if (!entry?.isIntersecting) return;
      observer.disconnect();
      if (reduced) return setStep(3);
      setStep(1);
      timers.push(setTimeout(() => setStep(2), 700), setTimeout(() => setStep(3), 2300));
    }, { threshold: 0.4 });
    observer.observe(el);
    return () => {
      observer.disconnect();
      timers.forEach(clearTimeout);
    };
  }, []);

  return (
    <div ref={ref} className="mt-4 min-h-[18rem] space-y-3" aria-live="polite">
      {step >= 1 && (
        <p className="msg-in ms-auto w-fit max-w-[85%] rounded-lg rounded-ee-sm bg-ink px-4 py-2.5 text-[15px] text-surface">
          {t.landing.exampleQuestion}
        </p>
      )}
      {step === 2 && (
        <div className="msg-in inline-flex items-center gap-3 rounded-lg border border-line bg-surface px-3.5 py-2.5 text-sm text-ink-2">
          <span className="typing-dots" aria-hidden>
            <span />
            <span />
            <span />
          </span>
          {t.landing.exampleTyping}
        </div>
      )}
      {step >= 3 && (
        <div className="msg-in rounded-lg border border-line bg-surface p-4 sm:p-5">
          <Answer
            text={`${t.landing.exampleAnswer} [${t.landing.exampleSource}, p.0]`}
            citations={[{ document: t.landing.exampleSource, page: 0 }]}
          />
        </div>
      )}
    </div>
  );
}
