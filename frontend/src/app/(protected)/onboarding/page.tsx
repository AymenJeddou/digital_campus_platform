'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { ProgramSelect, splitTags } from '@/components/ProgramSelect';
import { Field, buttonClass, inputClass } from '@/components/ui';
import { api } from '@/lib/api';
import { fill } from '@/lib/dictionary';
import { useT } from '@/lib/i18n';
import { useProfile } from '@/lib/profile';
import { PENDING_QUESTION_KEY } from '@/lib/types';

type Status = 'prospective' | 'enrolled';
type Step = 'status' | 'studies' | 'about';

export default function OnboardingPage() {
  const t = useT();
  const router = useRouter();
  const { refresh } = useProfile();
  const [step, setStep] = useState<Step>('status');
  const [status, setStatus] = useState<Status | null>(null);
  const [programId, setProgramId] = useState('');
  const [year, setYear] = useState('');
  const [bacType, setBacType] = useState('');
  const [bacScore, setBacScore] = useState('');
  const [interests, setInterests] = useState('');
  const [goals, setGoals] = useState('');
  const [busy, setBusy] = useState(false);

  const steps: Step[] = ['status', 'studies', 'about'];
  const index = steps.indexOf(step);

  const finish = async () => {
    setBusy(true);
    try {
      await api('profile/onboarding', {
        json: {
          student_status: status,
          program_id: programId || undefined,
          academic_year: status === 'enrolled' && year ? year : undefined,
          bac_type: bacType || undefined,
          bac_score: bacScore ? Number(bacScore) : undefined,
          interests: splitTags(interests),
          goals: splitTags(goals),
        },
      });
      await refresh();
      toast.success(t.onboarding.done);
      let pending = false;
      try {
        pending = !!sessionStorage.getItem(PENDING_QUESTION_KEY);
      } catch {}
      router.replace(pending ? '/chat' : '/dashboard');
    } catch {
      toast.error(t.onboarding.failed);
      setBusy(false);
    }
  };

  const next = (e: React.FormEvent) => {
    e.preventDefault();
    if (index < steps.length - 1) setStep(steps[index + 1]);
    else finish();
  };

  const choice = (value: Status, title: string, hint: string) => (
    <label
      className={`flex cursor-pointer flex-col rounded-md border-2 bg-surface px-4 py-3.5 transition-colors ${
        status === value ? 'border-red' : 'border-line-strong hover:border-ink'
      }`}
    >
      <input type="radio" name="status" value={value} checked={status === value} onChange={() => setStatus(value)} className="sr-only" />
      <span className="placard text-2xl">{title}</span>
      <span className="mt-1 text-sm text-ink-2">{hint}</span>
    </label>
  );

  return (
    <div className="mx-auto w-full max-w-xl px-4 py-10 sm:py-16">
      <p className="text-sm text-ink-3">{fill(t.onboarding.step, { n: index + 1, total: steps.length })}</p>
      <div className="mt-2 flex gap-1.5" aria-hidden>
        {steps.map((s, i) => (
          <span key={s} className={`h-1.5 flex-1 rounded-full ${i <= index ? 'bg-red' : 'bg-line'}`} />
        ))}
      </div>
      <h1 className="placard mt-6 text-[clamp(2rem,6vw,2.8rem)]">{t.onboarding.title}</h1>
      <p className="mt-1 text-ink-2">{t.onboarding.lead}</p>

      <form onSubmit={next} className="mt-8 space-y-5">
        {step === 'status' && (
          <fieldset>
            <legend className="mb-3 font-semibold">{t.onboarding.statusTitle}</legend>
            <div className="grid gap-3 sm:grid-cols-2">
              {choice('prospective', t.onboarding.prospective, t.onboarding.prospectiveHint)}
              {choice('enrolled', t.onboarding.enrolled, t.onboarding.enrolledHint)}
            </div>
          </fieldset>
        )}

        {step === 'studies' && (
          <>
            <h2 className="font-semibold">{status === 'enrolled' ? t.onboarding.programTitle : t.onboarding.bacTitle}</h2>
            {status === 'enrolled' ? (
              <>
                <Field label={t.onboarding.program}>{(id) => <ProgramSelect id={id} value={programId} onChange={setProgramId} />}</Field>
                <Field label={t.onboarding.year}>
                  {(id) => (
                    <select id={id} value={year} onChange={(e) => setYear(e.target.value)} className={inputClass}>
                      <option value="">—</option>
                      {t.onboarding.years.map((y) => (
                        <option key={y}>{y}</option>
                      ))}
                    </select>
                  )}
                </Field>
              </>
            ) : (
              <>
                <Field label={t.onboarding.bacType}>
                  {(id) => (
                    <select id={id} value={bacType} onChange={(e) => setBacType(e.target.value)} className={inputClass}>
                      <option value="">—</option>
                      {t.onboarding.bacTypes.map((b) => (
                        <option key={b}>{b}</option>
                      ))}
                    </select>
                  )}
                </Field>
                <Field label={`${t.onboarding.bacScore} (${t.common.optional})`}>
                  {(id) => (
                    <input id={id} type="number" inputMode="decimal" min={0} max={300} step="0.01" value={bacScore} onChange={(e) => setBacScore(e.target.value)} className={inputClass} />
                  )}
                </Field>
              </>
            )}
          </>
        )}

        {step === 'about' && (
          <>
            <h2 className="font-semibold">{t.onboarding.aboutTitle}</h2>
            <Field label={`${t.onboarding.interests} (${t.common.optional})`} hint={t.onboarding.interestsHint}>
              {(id) => <input id={id} value={interests} onChange={(e) => setInterests(e.target.value)} className={inputClass} />}
            </Field>
            <Field label={`${t.onboarding.goals} (${t.common.optional})`} hint={t.onboarding.goalsHint}>
              {(id) => <input id={id} value={goals} onChange={(e) => setGoals(e.target.value)} className={inputClass} />}
            </Field>
          </>
        )}

        <div className="flex items-center justify-between pt-4">
          {index > 0 ? (
            <button type="button" onClick={() => setStep(steps[index - 1])} className={buttonClass.ghost}>
              {t.common.back}
            </button>
          ) : (
            <span />
          )}
          <button type="submit" disabled={busy || (step === 'status' && !status)} className={buttonClass.primary}>
            {index === steps.length - 1 ? (busy ? t.common.saving : t.onboarding.finish) : t.common.next}
          </button>
        </div>
      </form>
    </div>
  );
}
