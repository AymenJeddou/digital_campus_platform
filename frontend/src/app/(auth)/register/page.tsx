'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api, errorMessage } from '@/lib/api';
import { useT } from '@/lib/i18n';
import { Field, PasswordInput, PasswordRules, buttonClass, inputClass, passwordOk } from '@/components/ui';

export default function RegisterPage() {
  const t = useT();
  const router = useRouter();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!passwordOk(password)) {
      setError(t.auth.errors.weak);
      return;
    }
    setBusy(true);
    setError('');
    try {
      await api('auth/register', { json: { email: email.trim(), password, full_name: fullName.trim() } });
      router.push(`/verify?email=${encodeURIComponent(email.trim())}`);
    } catch (err) {
      setError(errorMessage(err, t));
      setBusy(false);
    }
  };

  return (
    <>
      <h1 className="placard text-4xl">{t.auth.registerTitle}</h1>
      <p className="mt-2 text-ink-2">{t.auth.registerSub}</p>

      <form onSubmit={submit} className="mt-8 space-y-5">
        <Field label={t.auth.fullName}>
          {(id) => (
            <input id={id} autoComplete="name" required maxLength={120} value={fullName} onChange={(e) => setFullName(e.target.value)} className={inputClass} />
          )}
        </Field>
        <Field label={t.auth.email}>
          {(id) => (
            <input id={id} type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} className={inputClass} />
          )}
        </Field>
        <div className="space-y-2">
          <label htmlFor="password" className="block text-sm font-medium">
            {t.auth.password}
          </label>
          <PasswordInput id="password" value={password} onChange={setPassword} autoComplete="new-password" />
          <PasswordRules password={password} />
        </div>

        {error && (
          <p role="alert" className="rounded-md bg-red-wash px-3 py-2.5 text-sm text-red-ink">
            {error}
          </p>
        )}

        <button type="submit" disabled={busy} className={`${buttonClass.primary} w-full`}>
          {busy ? t.common.loading : t.auth.register}
        </button>
      </form>

      <p className="mt-8 text-sm text-ink-2">
        {t.auth.haveAccount}{' '}
        <Link href="/login" className="font-medium text-red-ink underline-offset-2 hover:underline">
          {t.auth.login}
        </Link>
      </p>
    </>
  );
}
