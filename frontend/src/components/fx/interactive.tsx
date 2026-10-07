'use client';

// Interaction pieces rebuilt from the 21st.dev picks: Magnetic Button,
// animated theme toggle, Typing Indicator + AI Loader, Halo Dropzone and the
// Admit One Ticket (source stub). No animation library: CSS + a few pointer
// handlers, all disabled for reduced motion.

import { useEffect, useRef, useState } from 'react';
import { flushSync } from 'react-dom';
import { Moon, Sun, Upload } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useT } from '@/lib/i18n';
import type { Citation } from '@/lib/types';
import { usePrefersReducedMotion } from './text';

/** Wraps a button/link so it leans toward the pointer and springs back. */
export function Magnetic({ children, strength = 0.28, className = '' }: { children: React.ReactNode; strength?: number; className?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const reduced = usePrefersReducedMotion();
  const onMove = (e: React.PointerEvent) => {
    const el = ref.current;
    if (!el || reduced || e.pointerType !== 'mouse') return;
    const r = el.getBoundingClientRect();
    const x = (e.clientX - (r.left + r.width / 2)) * strength;
    const y = (e.clientY - (r.top + r.height / 2)) * strength;
    el.style.transform = `translate(${x}px, ${y}px)`;
  };
  const reset = () => {
    if (ref.current) ref.current.style.transform = '';
  };
  return (
    <span ref={ref} onPointerMove={onMove} onPointerLeave={reset} className={`magnetic inline-flex ${className}`}>
      {children}
    </span>
  );
}

/** Theme switch with a circular reveal from the button (View Transitions),
 * falling back to an instant switch where unsupported. */
export function ThemeToggle({ className = '' }: { className?: string }) {
  const t = useT();
  const { resolvedTheme, setTheme } = useTheme();
  const reduced = usePrefersReducedMotion();
  const dark = resolvedTheme === 'dark';

  const toggle = (e: React.MouseEvent<HTMLButtonElement>) => {
    const next = dark ? 'light' : 'dark';
    const doc = document as Document & { startViewTransition?: (cb: () => void) => { ready: Promise<void> } };
    if (!doc.startViewTransition || reduced) {
      setTheme(next);
      return;
    }
    const r = e.currentTarget.getBoundingClientRect();
    const x = r.left + r.width / 2;
    const y = r.top + r.height / 2;
    const radius = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
    doc.startViewTransition(() => flushSync(() => setTheme(next))).ready.then(() => {
      document.documentElement.animate(
        { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${radius}px at ${x}px ${y}px)`] },
        { duration: 520, easing: 'cubic-bezier(0.16, 1, 0.3, 1)', pseudoElement: '::view-transition-new(root)' },
      );
    });
  };

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={dark ? t.common.themeLight : t.common.themeDark}
      className={`theme-toggle inline-flex h-10 w-10 items-center justify-center rounded-md text-ink-2 hover:bg-sunken hover:text-ink ${className}`}
      suppressHydrationWarning
    >
      <Sun className="theme-icon theme-sun h-[18px] w-[18px]" />
      <Moon className="theme-icon theme-moon h-[18px] w-[18px]" />
    </button>
  );
}

/** Three bouncing dots, plus what the assistant is doing and for how long. */
export function ThinkingIndicator() {
  const t = useT();
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, []);
  const phase = seconds < 3 ? t.chat.phaseSearching : seconds < 8 ? t.chat.phaseReading : t.chat.phaseWriting;
  return (
    <div role="status" className="inline-flex items-center gap-3 rounded-lg border border-line bg-surface px-3.5 py-2.5 text-sm text-ink-2">
      <span className="typing-dots" aria-hidden>
        <span />
        <span />
        <span />
      </span>
      <span>{phase}</span>
      <span className="tabular-nums text-ink-3">{seconds}s</span>
    </div>
  );
}

/** Drag-and-drop file zone with an animated glowing rim. */
export function HaloDropzone({
  onFile,
  busy,
  accept,
  title,
  hint,
}: {
  onFile: (file: File) => void;
  busy: boolean;
  accept: string;
  title: string;
  hint: string;
}) {
  const [over, setOver] = useState(false);
  return (
    <label
      onDragOver={(e) => {
        e.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setOver(false);
        const file = e.dataTransfer.files?.[0];
        if (file && !busy) onFile(file);
      }}
      className={`halo ${over ? 'halo-over' : ''} ${busy ? 'halo-busy' : ''}`}
    >
      <span className="halo-inner">
        <Upload className="h-6 w-6 text-ink-2" aria-hidden />
        <span className="font-medium">{title}</span>
        <span className="text-xs text-ink-3">{hint}</span>
      </span>
      <input
        type="file"
        accept={accept}
        className="sr-only"
        disabled={busy}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onFile(file);
          e.target.value = '';
        }}
      />
    </label>
  );
}

/** A source as an "admit one" ticket: perforated stub with the number,
 * dithered paper, and a 3D tilt with glare under the pointer. */
export function SourceTicket({ n, source, onOpen }: { n: number; source: Citation; onOpen?: () => void }) {
  const t = useT();
  const ref = useRef<HTMLButtonElement>(null);
  const reduced = usePrefersReducedMotion();
  const onMove = (e: React.PointerEvent) => {
    const el = ref.current;
    if (!el || reduced || e.pointerType !== 'mouse') return;
    const r = el.getBoundingClientRect();
    const dx = (e.clientX - r.left) / r.width - 0.5;
    const dy = (e.clientY - r.top) / r.height - 0.5;
    el.style.transform = `perspective(700px) rotateX(${-dy * 14}deg) rotateY(${dx * 14}deg) scale(1.03)`;
    el.style.setProperty('--gx', `${(dx + 0.5) * 100}%`);
    el.style.setProperty('--gy', `${(dy + 0.5) * 100}%`);
  };
  const reset = () => {
    if (ref.current) ref.current.style.transform = '';
  };
  return (
    <button ref={ref} type="button" onClick={onOpen} onPointerMove={onMove} onPointerLeave={reset} className="ticket">
      <span className="ticket-stub tabular-nums">{n}</span>
      <span className="ticket-body">
        <span className="ticket-title">{source.document}</span>
        <span className="ticket-page tabular-nums">
          {t.common.page} {source.page}
        </span>
      </span>
      <span className="ticket-glare" aria-hidden />
    </button>
  );
}
