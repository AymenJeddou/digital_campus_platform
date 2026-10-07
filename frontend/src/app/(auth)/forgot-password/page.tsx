'use client';

import { useState } from 'react';
import Link from 'next/link';
import { api, errorMessage } from '@/lib/api';
import { useT } from '@/lib/i18n';
import { Field, buttonClass, inputClass } from '@/components/ui';

export default function ForgotPasswordPage() {
  const t = useT();
  const [email, setEmail] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api('auth/forgot-password', { json: { email: email.trim() } });
      setMessage(t.auth.forgotSent);
    } catch (err) {
      setMessage(errorMessage(err, t));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <h1 className="placard text-4xl">{t.auth.forgotTitle}</h1>
      <p className="mt-2 text-ink-2">{t.auth.forgotSub}</p>
      <form onSubmit={submit} className="mt-8 space-y-5">
        <Field label={t.auth.email}>
          {(id) => (
            <input id={id} type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} className={inputClass} />
          )}
        </Field>
        <button type="submit" disabled={busy} className={`${buttonClass.primary} w-full`}>
          {busy ? t.common.loading : t.auth.sendLink}
        </button>
        {message && (
          <p role="status" className="rounded-md bg-sunken px-3 py-2.5 text-sm text-ink-2">
            {message}
          </p>
        )}
      </form>
      <Link href="/login" className="mt-8 inline-block text-sm font-medium text-red-ink underline-offset-2 hover:underline">
        {t.auth.toLogin}
      </Link>
    </>
  );
}
