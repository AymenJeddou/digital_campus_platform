'use client';

import { Suspense, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { api, errorMessage } from '@/lib/api';
import { fill } from '@/lib/dictionary';
import { useT } from '@/lib/i18n';
import { Field, Spinner, buttonClass, inputClass } from '@/components/ui';

type State = 'check' | 'verifying' | 'verified' | 'failed';

function Verify() {
  const t = useT();
  const params = useSearchParams();
  const token = params.get('token');
  const [state, setState] = useState<State>(token ? 'verifying' : 'check');
  const [email, setEmail] = useState(params.get('email') ?? '');
  const [note, setNote] = useState('');
  const started = useRef(false);

  useEffect(() => {
    if (!token || started.current) return;
    started.current = true; // the link is single-purpose; don't post it twice
    api('auth/verify', { json: { token } })
      .then(() => setState('verified'))
      .catch(() => setState('failed'));
  }, [token]);

  const resend = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api('auth/resend-verification', { json: { email: email.trim() } });
      setNote(t.auth.resent);
    } catch (err) {
      setNote(errorMessage(err, t));
    }
  };

  if (state === 'verifying') return <Spinner label={t.auth.verifying} />;

  if (state === 'verified') {
    return (
      <>
        <h1 className="placard text-4xl">{t.auth.verifiedTitle}</h1>
        <p className="mt-3 text-ink-2">{t.auth.verifiedBody}</p>
        <Link href="/login" className={`${buttonClass.primary} mt-8 w-full`}>
          {t.auth.toLogin}
        </Link>
      </>
    );
  }

  return (
    <>
      <h1 className="placard text-4xl">{state === 'failed' ? t.auth.verifyFailedTitle : t.auth.checkTitle}</h1>
      <p className="mt-3 text-ink-2">
        {state === 'failed' ? t.auth.verifyFailedBody : fill(t.auth.checkBody, { email: email || '…' })}
      </p>

      <form onSubmit={resend} className="mt-8 space-y-4">
        <Field label={t.auth.email}>
          {(id) => (
            <input id={id} type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className={inputClass} />
          )}
        </Field>
        <button type="submit" className={`${buttonClass.secondary} w-full`}>
          {t.auth.resend}
        </button>
        {note && (
          <p role="status" className="text-sm text-ink-2">
            {note}
          </p>
        )}
      </form>

      <Link href="/login" className={`${buttonClass.primary} mt-6 w-full`}>
        {t.auth.toLogin}
      </Link>
    </>
  );
}

export default function VerifyPage() {
  return (
    <Suspense>
      <Verify />
    </Suspense>
  );
}
