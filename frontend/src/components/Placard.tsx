'use client';

import Link from 'next/link';
import { useLocale } from '@/lib/i18n';

/** The brand: a roof placard reading "FSB" over the louage band. */
export function Mark({ href = '/', compact = false }: { href?: string; compact?: boolean }) {
  return (
    <Link href={href} className="inline-flex items-center gap-2.5 rounded-md" aria-label="FSB Nexus">
      <span className="inline-flex flex-col overflow-hidden rounded-[5px] border-2 border-ink bg-surface">
        <span className="placard px-2 pt-1.5 pb-1 text-[17px] text-ink">FSB</span>
        <span className="band" />
      </span>
      {!compact && <span className="text-[15px] font-semibold tracking-tight max-[420px]:hidden">Nexus</span>}
    </Link>
  );
}

/**
 * A bilingual destination placard, the way louage signs carry both scripts.
 * The interface language reads first and large; the other script follows.
 */
export function Placard({
  fr,
  ar,
  size = 'md',
  pressed,
  onClick,
  hint,
}: {
  fr: string;
  ar: string;
  size?: 'sm' | 'md' | 'lg';
  pressed?: boolean;
  onClick?: () => void;
  hint?: string;
}) {
  const locale = useLocale();
  const [primary, secondary] = locale === 'ar' ? [ar, fr] : [fr, ar];
  const big = { sm: 'text-lg', md: 'text-2xl', lg: 'text-[clamp(1.6rem,3.2vw,2.4rem)]' }[size];
  const body = (
    <>
      <span className={`placard block ${big}`}>{primary}</span>
      <span className="placard mt-1 block text-[15px] text-ink-2" lang={locale === 'ar' ? 'fr' : 'ar'}>
        {secondary}
      </span>
      {hint && <span className="mt-2 block text-xs leading-snug text-ink-3">{hint}</span>}
    </>
  );
  const base =
    'relative block rounded-md border-2 bg-surface px-3.5 pt-3 pb-2.5 text-start transition-[transform,box-shadow,border-color] duration-200';
  if (!onClick) return <div className={`${base} border-ink`}>{body}</div>;
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={pressed}
      className={`${base} min-h-11 cursor-pointer hover:-translate-y-0.5 hover:shadow-[0_6px_14px_-8px_rgb(0_0_0/0.35)] ${
        pressed ? 'border-red shadow-[0_6px_14px_-8px_rgb(0_0_0/0.35)]' : 'border-ink'
      }`}
    >
      {pressed && <span aria-hidden className="absolute inset-x-0 bottom-0 h-[5px] rounded-b-[3px] bg-red" />}
      {body}
    </button>
  );
}
