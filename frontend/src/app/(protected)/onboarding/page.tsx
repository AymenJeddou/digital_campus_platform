'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { Check } from 'lucide-react';
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

  // Questionnaire: answering the status question moves straight on.
  const choice = (value: Status, title: string, hint: string) => (
    <label
      className={`flex cursor-pointer flex-col rounded-md border-2 bg-surface px-4 py-3.5 transition-colors has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 ${
        status === value ? 'border-red' : 'border-line-strong hover:border-ink'
      }`}
    >
      <input
        type="radio"
        name="status"
        value={value}
        checked={status === value}
        onChange={() => {
          setStatus(value);
          setTimeout(() => setStep('studies'), 260);
        }}
        className="sr-only"
      />
      <span className="placard text-2xl">{title}</span>
      <span className="mt-1 text-sm text-ink-2">{hint}</span>
    </label>
  );

  return (
    <div className="mx-auto w-full max-w-xl px-4 py-10 sm:py-16">
      <p className="sr-only">{fill(t.onboarding.step, { n: index + 1, total: steps.length })}</p>
      <ol className="flex items-center gap-2" aria-hidden>
        {steps.map((s, i) => (
          <li key={s} className="flex flex-1 items-center gap-2 last:flex-none">
            <span
              className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md border-2 text-sm font-semibold tabular-nums transition-colors ${
                i < index ? 'border-ink bg-ink text-surface' : i === index ? 'border-red text-red-ink' : 'border-line-strong text-ink-3'
              }`}
            >
              {i < index ? <Check className="h-4 w-4" /> : i + 1}
            </span>
            <span className={`hidden text-sm sm:inline ${i === index ? 'font-semibold' : 'text-ink-3'}`}>{t.onboarding.steps[i]}</span>
            {i < steps.length - 1 && <span className={`h-0.5 flex-1 rounded-full ${i < index ? 'bg-ink' : 'bg-line'}`} />}
          </li>
        ))}
      </ol>
      <h1 className="placard mt-6 text-[clamp(2rem,6vw,2.8rem)]">{t.onboarding.title}</h1>
      <p className="mt-1 text-ink-2">{t.onboarding.lead}</p>

      <form key={step} onSubmit={next} className="msg-in mt-8 space-y-5">
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
                <ChipChoice legend={t.onboarding.year} options={t.onboarding.years} value={year} onChange={setYear} />
              </>
            ) : (
              <>
                <ChipChoice legend={t.onboarding.bacType} options={t.onboarding.bacTypes} value={bacType} onChange={setBacType} />
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

/** One question, answered by tapping a chip (a styled radio group). */
function ChipChoice({ legend, options, value, onChange }: { legend: string; options: string[]; value: string; onChange: (v: string) => void }) {
  return (
    <fieldset>
      <legend className="mb-2 text-sm font-medium">{legend}</legend>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <label
            key={option}
            className={`cursor-pointer rounded-md border-2 px-3.5 py-2 text-sm transition-colors has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 ${
              value === option ? 'border-red bg-red-wash font-semibold text-ink' : 'border-line-strong text-ink-2 hover:border-ink'
            }`}
          >
            <input type="radio" name={legend} value={option} checked={value === option} onChange={() => onChange(option)} className="sr-only" />
            {option}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
