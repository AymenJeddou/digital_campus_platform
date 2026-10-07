'use client';

// Text effects (rebuilt from the 21st.dev picks "Text Flipping Board",
// "Typewriter" and "Text Scramble"). All of them fall back to plain text for
// reduced-motion users, and leave Arabic intact (letters join, so they are
// animated as whole words, never split into tiles or scrambled).

import { useEffect, useRef, useState } from 'react';

const ARABIC = /[؀-ۿ]/;
const FLAPS = ' ABCDEFGHIJKLMNOPQRSTUVWXYZÀÂÇÉÈÊËÎÏÔÙÛ0123456789-·';

export function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReduced(mq.matches);
    update();
    mq.addEventListener('change', update);
    return () => mq.removeEventListener('change', update);
  }, []);
  return reduced;
}

/** Split-flap departure board cycling through `words`. */
export function FlipBoard({ words, interval = 3200, className = '' }: { words: string[]; interval?: number; className?: string }) {
  const reduced = usePrefersReducedMotion();
  const [index, setIndex] = useState(0);
  useEffect(() => {
    if (reduced || words.length < 2) return;
    const id = setInterval(() => setIndex((i) => (i + 1) % words.length), interval);
    return () => clearInterval(id);
  }, [reduced, words.length, interval]);

  const word = words[index % words.length] ?? '';
  const arabic = ARABIC.test(word);
  const width = Math.min(14, Math.max(...words.map((w) => w.length)));

  return (
    <div className={`flipboard ${className}`} role="img" aria-label={word}>
      {arabic ? (
        <FlapTile key={word} char={word} wide flip={!reduced} />
      ) : (
        word
          .toUpperCase()
          .padEnd(width)
          .slice(0, width)
          .split('')
          .map((ch, i) => <SteppingTile key={i} target={ch} delay={i * 45} animate={!reduced} />)
      )}
    </div>
  );
}

/** One tile that steps through the flap alphabet until it shows `target`. */
function SteppingTile({ target, delay, animate }: { target: string; delay: number; animate: boolean }) {
  const [shown, setShown] = useState(target);
  const shownRef = useRef(target);
  useEffect(() => {
    if (!animate || shownRef.current === target) {
      shownRef.current = target;
      return;
    }
    const from = Math.max(0, FLAPS.indexOf(shownRef.current));
    const to = Math.max(0, FLAPS.indexOf(target));
    // At most 8 visible steps, like a board that has been "spinning".
    const span = (to - from + FLAPS.length) % FLAPS.length;
    const steps = Math.min(span, 8);
    const timers: ReturnType<typeof setTimeout>[] = [];
    for (let s = 1; s <= steps; s++) {
      const ch = s === steps ? target : FLAPS[(from + Math.round((span * s) / steps)) % FLAPS.length];
      timers.push(
        setTimeout(() => {
          shownRef.current = ch;
          setShown(ch);
        }, delay + s * 55),
      );
    }
    if (steps === 0) {
      timers.push(setTimeout(() => setShown(target), delay));
      shownRef.current = target;
    }
    return () => timers.forEach(clearTimeout);
  }, [target, delay, animate]);
  return <FlapTile key={shown} char={shown} flip={animate} />;
}

function FlapTile({ char, wide = false, flip }: { char: string; wide?: boolean; flip: boolean }) {
  return (
    <span aria-hidden className={`flap ${wide ? 'flap-wide' : ''} ${flip ? 'flap-anim' : ''}`}>
      <span className="flap-char">{char === ' ' ? ' ' : char}</span>
    </span>
  );
}

/** Types, pauses, deletes and loops through `phrases` (for placeholders). */
export function useTypewriter(phrases: readonly string[], enabled = true): string {
  const reduced = usePrefersReducedMotion();
  const [text, setText] = useState('');
  const animate = enabled && !reduced && phrases.length > 0;
  useEffect(() => {
    if (!animate) return;
    let phrase = 0;
    let len = 0;
    let deleting = false;
    let timer: ReturnType<typeof setTimeout>;
    const tick = () => {
      const full = phrases[phrase];
      if (!deleting) {
        len++;
        setText(full.slice(0, len));
        if (len >= full.length) {
          deleting = true;
          timer = setTimeout(tick, 1900);
          return;
        }
        timer = setTimeout(tick, 42);
      } else {
        len--;
        setText(full.slice(0, len));
        if (len <= 0) {
          deleting = false;
          phrase = (phrase + 1) % phrases.length;
          timer = setTimeout(tick, 350);
          return;
        }
        timer = setTimeout(tick, 18);
      }
    };
    timer = setTimeout(() => {
      setText('');
      tick();
    }, 500);
    return () => clearTimeout(timer);
  }, [phrases, animate]);
  return animate ? text : (phrases[0] ?? '');
}

const GLYPHS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789#%&*+=?';

/** Text that decodes from random glyphs when it first scrolls into view. */
export function Scramble({ text, className = '', as: Tag = 'span' }: { text: string; className?: string; as?: 'span' | 'h2' | 'p' }) {
  const reduced = usePrefersReducedMotion();
  const ref = useRef<HTMLElement>(null);
  const [out, setOut] = useState(text);

  useEffect(() => {
    const el = ref.current;
    if (!el || reduced || ARABIC.test(text)) {
      setOut(text);
      return;
    }
    let raf = 0;
    const run = () => {
      const start = performance.now();
      const duration = Math.min(900, 250 + text.length * 22);
      const frame = (now: number) => {
        const progress = Math.min(1, (now - start) / duration);
        const fixed = Math.floor(progress * text.length);
        setOut(
          text
            .split('')
            .map((ch, i) => (i < fixed || ch === ' ' ? ch : GLYPHS[Math.floor(Math.random() * GLYPHS.length)]))
            .join(''),
        );
        if (progress < 1) raf = requestAnimationFrame(frame);
      };
      raf = requestAnimationFrame(frame);
    };
    const observer = new IntersectionObserver(([entry]) => {
      if (entry?.isIntersecting) {
        observer.disconnect();
        run();
      }
    });
    observer.observe(el);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(raf);
    };
  }, [text, reduced]);

  return (
    <Tag ref={ref as never} className={className} aria-label={text}>
      <span aria-hidden>{out}</span>
    </Tag>
  );
}
