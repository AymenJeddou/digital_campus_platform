'use client';

import { useId, useState } from 'react';
import { Check, Eye, EyeOff } from 'lucide-react';
import { useSwitchLocale, useT } from '@/lib/i18n';

export { ThemeToggle } from './fx/interactive';

export const inputClass =
  'w-full rounded-md border border-line-strong bg-surface px-3.5 py-2.5 text-[15px] text-ink placeholder:text-ink-3 outline-none transition-colors focus:border-ink focus-visible:outline-2 focus-visible:outline-offset-1 disabled:opacity-60';

export const buttonClass = {
  primary:
    'inline-flex min-h-11 items-center justify-center gap-2 whitespace-nowrap rounded-md bg-red px-5 text-[15px] font-semibold text-on-red transition-[filter,transform] hover:brightness-110 active:translate-y-px disabled:cursor-not-allowed disabled:opacity-55 disabled:hover:brightness-100',
  secondary:
    'inline-flex min-h-11 items-center justify-center gap-2 whitespace-nowrap rounded-md border border-line-strong bg-surface px-4 text-[15px] font-medium text-ink transition-colors hover:border-ink disabled:cursor-not-allowed disabled:opacity-55',
  ghost:
    'inline-flex min-h-10 items-center justify-center gap-2 whitespace-nowrap rounded-md px-3 text-sm font-medium text-ink-2 transition-colors hover:bg-sunken hover:text-ink disabled:opacity-55',
};

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: (id: string) => React.ReactNode;
}) {
  const id = useId();
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-sm font-medium text-ink">
        {label}
      </label>
      {children(id)}
      {hint && <p className="text-xs text-ink-3">{hint}</p>}
    </div>
  );
}

export function PasswordInput({
  id,
  value,
  onChange,
  autoComplete,
}: {
  id: string;
  value: string;
  onChange: (v: string) => void;
  autoComplete: string;
}) {
  const t = useT();
  const [show, setShow] = useState(false);
  return (
    <div className="relative">
      <input
        id={id}
        type={show ? 'text' : 'password'}
        autoComplete={autoComplete}
        required
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`${inputClass} pe-11`}
      />
      <button
        type="button"
        onClick={() => setShow(!show)}
        aria-label={show ? t.auth.hide : t.auth.show}
        aria-pressed={show}
        className="absolute inset-y-0 end-0 flex w-11 items-center justify-center text-ink-3 hover:text-ink"
      >
        {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </button>
    </div>
  );
}

// Mirrors backend/app/core/security.py PASSWORD_RULES.
const RULES: [keyof ReturnType<typeof useT>['auth']['rules'], RegExp][] = [
  ['length', /.{8,}/],
  ['upper', /[A-Z]/],
  ['lower', /[a-z]/],
  ['digit', /[0-9]/],
  ['special', /[^A-Za-z0-9]/],
];

export function passwordOk(password: string) {
  return RULES.every(([, re]) => re.test(password));
}

export function PasswordRules({ password }: { password: string }) {
  const t = useT();
  return (
    <ul className="grid grid-cols-1 gap-1 text-xs sm:grid-cols-2" aria-live="polite">
      {RULES.map(([key, re]) => {
        const ok = re.test(password);
        return (
          <li key={key} className={`flex items-center gap-1.5 ${ok ? 'text-ok' : 'text-ink-3'}`}>
            <Check className={`h-3.5 w-3.5 ${ok ? 'opacity-100' : 'opacity-30'}`} aria-hidden />
            <span>{t.auth.rules[key]}</span>
            <span className="sr-only">{ok ? '✓' : ''}</span>
          </li>
        );
      })}
    </ul>
  );
}

export function LocaleToggle({ className = '' }: { className?: string }) {
  const t = useT();
  const switchLocale = useSwitchLocale();
  return (
    <button type="button" onClick={switchLocale} aria-label={t.common.languageLabel} className={`${buttonClass.ghost} ${className}`}>
      <span className="placard text-base leading-none">{t.common.language}</span>
    </button>
  );
}

export function Spinner({ label }: { label: string }) {
  return (
    <span role="status" className="inline-flex items-center gap-2 text-sm text-ink-3">
      <span aria-hidden className="h-4 w-4 animate-spin rounded-full border-2 border-line-strong border-t-red" />
      {label}
    </span>
  );
}
