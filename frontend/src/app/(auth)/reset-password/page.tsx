'use client';

import { Suspense, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { api, errorMessage } from '@/lib/api';
import { useT } from '@/lib/i18n';
import { PasswordInput, PasswordRules, buttonClass, passwordOk } from '@/components/ui';

function Reset() {
  const t = useT();
  const token = useSearchParams().get('token') ?? '';
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState(token ? '' : t.auth.errors.badLink);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!passwordOk(password)) return setError(t.auth.errors.weak);
    setBusy(true);
    setError('');
    try {
      await api('auth/reset-password', { json: { token, password } });
      setDone(true);
    } catch (err) {
      setError(errorMessage(err, t));
    } finally {
      setBusy(false);
    }
  };

  if (done) {
    return (
      <>
        <h1 className="placard text-4xl">{t.auth.resetTitle}</h1>
        <p role="status" className="mt-3 text-ink-2">{t.auth.resetDone}</p>
        <Link href="/login" className={`${buttonClass.primary} mt-8 w-full`}>
          {t.auth.toLogin}
        </Link>
      </>
    );
  }

  return (
    <>
      <h1 className="placard text-4xl">{t.auth.resetTitle}</h1>
      <form onSubmit={submit} className="mt-8 space-y-5">
        <div className="space-y-2">
          <label htmlFor="password" className="block text-sm font-medium">
            {t.auth.newPassword}
          </label>
          <PasswordInput id="password" value={password} onChange={setPassword} autoComplete="new-password" />
          <PasswordRules password={password} />
        </div>
        {error && (
          <p role="alert" className="rounded-md bg-red-wash px-3 py-2.5 text-sm text-red-ink">
            {error}{' '}
            {error === t.auth.errors.badLink && (
              <Link href="/forgot-password" className="font-medium underline">
                {t.auth.sendLink}
              </Link>
            )}
          </p>
        )}
        <button type="submit" disabled={busy || !token} className={`${buttonClass.primary} w-full`}>
          {busy ? t.common.saving : t.auth.reset}
        </button>
      </form>
    </>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense>
      <Reset />
    </Suspense>
  );
}
