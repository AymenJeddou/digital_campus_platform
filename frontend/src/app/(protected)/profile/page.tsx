'use client';

import { useState } from 'react';
import { useTheme } from 'next-themes';
import { toast } from 'sonner';
import { ProgramSelect, splitTags } from '@/components/ProgramSelect';
import { Field, buttonClass, inputClass } from '@/components/ui';
import { ApiError, api, errorMessage } from '@/lib/api';
import { useLocale, useSwitchLocale, useT } from '@/lib/i18n';
import { useProfile } from '@/lib/profile';
import type { Profile } from '@/lib/types';

type Status = 'prospective' | 'enrolled' | 'alumni';

export default function ProfilePage() {
  const { profile } = useProfile();
  const t = useT();
  if (!profile) return <p className="mx-auto max-w-3xl px-4 py-12 text-ink-3">{t.common.loading}</p>;
  // Keyed so the form re-initialises if a different account loads.
  return <ProfileForm key={profile.email} profile={profile} />;
}

function ProfileForm({ profile }: { profile: Profile }) {
  const t = useT();
  const locale = useLocale();
  const switchLocale = useSwitchLocale();
  const { theme, setTheme } = useTheme();
  const { refresh } = useProfile();
  const [form, setForm] = useState({
    full_name: profile.full_name ?? '',
    student_status: (profile.student_status ?? 'prospective') as Status,
    program_id: profile.program?.id ?? '',
    academic_year: profile.academic_year ?? '',
    bac_type: profile.bac_type ?? '',
    bac_score: profile.bac_score?.toString() ?? '',
    interests: (profile.interests ?? []).join(', '),
    goals: (profile.goals ?? []).join(', '),
  });
  const [busy, setBusy] = useState(false);

  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api('profile', {
        method: 'PATCH',
        json: {
          full_name: form.full_name.trim() || undefined,
          student_status: form.student_status,
          program_id: form.program_id || null,
          academic_year: form.academic_year.trim() || undefined,
          bac_type: form.bac_type.trim() || undefined,
          bac_score: form.bac_score ? Number(form.bac_score) : undefined,
          interests: splitTags(form.interests),
          goals: splitTags(form.goals),
        },
      });
      await refresh();
      toast.success(t.profile.saved);
    } catch (err) {
      toast.error(err instanceof ApiError && err.status === 422 ? t.profile.invalid : errorMessage(err, t));
    } finally {
      setBusy(false);
    }
  };

  const section = 'grid gap-5 border-t border-line pt-6 md:grid-cols-[12rem_1fr]';

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 lg:py-12">
      <h1 className="placard text-[clamp(2.2rem,5vw,3.2rem)]">{t.profile.title}</h1>
      <p className="mt-1 text-ink-3">{profile.email}</p>

      <form onSubmit={save} className="mt-8 space-y-8">
        <div className={section}>
          <h2 className="font-semibold">{t.profile.account}</h2>
          <div className="space-y-4">
            <Field label={t.auth.fullName}>
              {(id) => <input id={id} value={form.full_name} onChange={set('full_name')} maxLength={120} className={inputClass} />}
            </Field>
          </div>
        </div>

        <div className={section}>
          <h2 className="font-semibold">{t.profile.studies}</h2>
          <div className="space-y-4">
            <Field label={t.profile.status}>
              {(id) => (
                <select id={id} value={form.student_status} onChange={set('student_status')} className={inputClass}>
                  {(Object.keys(t.profile.statuses) as Status[]).map((s) => (
                    <option key={s} value={s}>
                      {t.profile.statuses[s]}
                    </option>
                  ))}
                </select>
              )}
            </Field>
            <Field label={t.onboarding.program}>
              {(id) => <ProgramSelect id={id} value={form.program_id} onChange={(v) => setForm((f) => ({ ...f, program_id: v }))} />}
            </Field>
            <Field label={t.onboarding.year}>
              {(id) => (
                <select id={id} value={form.academic_year} onChange={set('academic_year')} className={inputClass}>
                  <option value="">—</option>
                  {[...new Set([...t.onboarding.years, form.academic_year].filter(Boolean))].map((y) => (
                    <option key={y}>{y}</option>
                  ))}
                </select>
              )}
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label={t.onboarding.bacType}>
                {(id) => (
                  <select id={id} value={form.bac_type} onChange={set('bac_type')} className={inputClass}>
                    <option value="">—</option>
                    {[...new Set([...t.onboarding.bacTypes, form.bac_type].filter(Boolean))].map((b) => (
                      <option key={b}>{b}</option>
                    ))}
                  </select>
                )}
              </Field>
              <Field label={t.onboarding.bacScore}>
                {(id) => (
                  <input id={id} type="number" inputMode="decimal" min={0} max={300} step="0.01" value={form.bac_score} onChange={set('bac_score')} className={inputClass} />
                )}
              </Field>
            </div>
          </div>
        </div>

        <div className={section}>
          <h2 className="font-semibold">{t.profile.about}</h2>
          <div className="space-y-4">
            <Field label={t.onboarding.interests} hint={t.onboarding.interestsHint}>
              {(id) => <input id={id} value={form.interests} onChange={set('interests')} className={inputClass} />}
            </Field>
            <Field label={t.onboarding.goals} hint={t.onboarding.goalsHint}>
              {(id) => <input id={id} value={form.goals} onChange={set('goals')} className={inputClass} />}
            </Field>
          </div>
        </div>

        <div className="flex justify-end">
          <button type="submit" disabled={busy} className={buttonClass.primary}>
            {busy ? t.common.saving : t.common.save}
          </button>
        </div>
      </form>

      <div className={`${section} mt-10`}>
        <h2 className="font-semibold">{t.profile.preferences}</h2>
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span className="text-sm">{t.profile.languageTitle}</span>
            <div className="inline-flex rounded-md border border-line-strong p-0.5" role="group" aria-label={t.profile.languageTitle}>
              {(['fr', 'ar'] as const).map((l) => (
                <button
                  key={l}
                  type="button"
                  aria-pressed={locale === l}
                  onClick={() => locale !== l && switchLocale()}
                  className={`placard rounded px-3 py-1.5 text-base ${locale === l ? 'bg-ink text-surface' : 'text-ink-2'}`}
                >
                  {l === 'fr' ? 'Français' : 'العربية'}
                </button>
              ))}
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span className="text-sm">{t.profile.themeTitle}</span>
            <div className="inline-flex rounded-md border border-line-strong p-0.5" role="group" aria-label={t.profile.themeTitle}>
              {(
                [
                  ['system', t.profile.themeSystem],
                  ['light', t.common.themeLight],
                  ['dark', t.common.themeDark],
                ] as const
              ).map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  aria-pressed={theme === value}
                  onClick={() => setTheme(value)}
                  className={`rounded px-3 py-1.5 text-sm ${theme === value ? 'bg-ink text-surface' : 'text-ink-2'}`}
                  suppressHydrationWarning
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
