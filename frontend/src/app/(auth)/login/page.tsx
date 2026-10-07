'use client';

import { Suspense, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { ApiError, api, errorMessage } from '@/lib/api';
import { useT } from '@/lib/i18n';
import { PENDING_QUESTION_KEY } from '@/lib/types';
import { Field, PasswordInput, buttonClass, inputClass } from '@/components/ui';

/** Only same-site paths, so ?next= can't bounce the student to another site. */
function safeNext(next: string | null): string | null {
  return next && /^\/(?![/\\])/.test(next) ? next : null;
}

function LoginForm() {
  const t = useT();
  const router = useRouter();
  const params = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<{ text: string; unverified: boolean } | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.set('username', email.trim());
      form.set('password', password);
      await api('auth/login', { form });
      let pending = false;
      try {
        pending = !!sessionStorage.getItem(PENDING_QUESTION_KEY);
      } catch {}
      router.replace(pending ? '/chat' : safeNext(params.get('next')) ?? '/dashboard');
      router.refresh();
    } catch (err) {
      setError({ text: errorMessage(err, t), unverified: err instanceof ApiError && err.status === 403 });
      setBusy(false);
    }
  };

  return (
    <>
      <h1 className="placard text-4xl">{t.auth.loginTitle}</h1>
      <p className="mt-2 text-ink-2">{t.auth.loginSub}</p>

      <form onSubmit={submit} className="mt-8 space-y-5">
        <Field label={t.auth.email}>
          {(id) => (
            <input id={id} type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} className={inputClass} />
          )}
        </Field>
        <div className="space-y-1.5">
          <div className="flex items-baseline justify-between">
            <label htmlFor="password" className="text-sm font-medium">
              {t.auth.password}
            </label>
            <Link href="/forgot-password" className="text-sm text-red-ink underline-offset-2 hover:underline">
              {t.auth.forgot}
            </Link>
          </div>
          <PasswordInput id="password" value={password} onChange={setPassword} autoComplete="current-password" />
        </div>

        {error && (
          <p role="alert" className="rounded-md bg-red-wash px-3 py-2.5 text-sm text-red-ink">
            {error.text}{' '}
            {error.unverified && (
              <Link href={`/verify?email=${encodeURIComponent(email.trim())}`} className="font-medium underline">
                {t.auth.resend}
              </Link>
            )}
          </p>
        )}

        <button type="submit" disabled={busy} className={`${buttonClass.primary} w-full`}>
          {busy ? t.common.loading : t.auth.login}
        </button>
      </form>

      <p className="mt-8 text-sm text-ink-2">
        {t.auth.noAccount}{' '}
        <Link href="/register" className="font-medium text-red-ink underline-offset-2 hover:underline">
          {t.auth.register}
        </Link>
      </p>
    </>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
