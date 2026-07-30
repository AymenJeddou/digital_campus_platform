'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, ArrowRight, Check, GraduationCap, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { profileService, OnboardingRequest } from '@/lib/services/profile';

type Status = 'prospective' | 'enrolled';

const ACADEMIC_YEARS = ['1ère année', '2ème année', '3ème année', 'Master', 'Doctorat'];
const BAC_TYPES = ['Mathématiques', 'Sciences expérimentales', 'Techniques', 'Informatique', 'Économie', 'Lettres', 'Autre'];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  const [status, setStatus] = useState<Status | null>(null);
  const [academicYear, setAcademicYear] = useState('');
  const [bacType, setBacType] = useState('');
  const [bacScore, setBacScore] = useState('');
  const [interests, setInterests] = useState('');
  const [goals, setGoals] = useState('');

  // Enrolled students get the academic-year step; prospective students skip it.
  const steps = status === 'enrolled' ? ['status', 'year', 'bac', 'about'] : ['status', 'bac', 'about'];
  const current = steps[step];
  const isLast = step === steps.length - 1;

  const canNext = () => {
    if (current === 'status') return status !== null;
    if (current === 'year') return !!academicYear;
    return true; // bac + about are optional
  };

  const next = () => {
    if (!canNext()) return;
    if (isLast) {
      submit();
      return;
    }
    setStep((s) => s + 1);
  };

  const back = () => setStep((s) => Math.max(0, s - 1));

  const submit = async () => {
    if (!status) return;
    setSubmitting(true);
    const payload: OnboardingRequest = {
      student_status: status,
      academic_year: status === 'enrolled' && academicYear ? academicYear : undefined,
      bac_type: bacType || undefined,
      bac_score: bacScore ? Number(bacScore) : undefined,
      interests: interests
        ? interests.split(',').map((s) => s.trim()).filter(Boolean)
        : undefined,
      goals: goals
        ? goals.split(',').map((s) => s.trim()).filter(Boolean)
        : undefined,
    };
    try {
      await profileService.completeOnboarding(payload);
      toast.success('Profil complété !');
      router.replace('/dashboard');
    } catch {
      toast.error('Impossible d’enregistrer. Réessaie.');
      setSubmitting(false);
    }
  };

  const progress = ((step + 1) / steps.length) * 100;

  return (
    <div className="flex min-h-[70vh] items-center justify-center">
      <div className="w-full max-w-xl rounded-3xl border border-slate-200/80 bg-white p-8 shadow-[0_24px_55px_rgba(15,23,42,0.08)]">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#eff6ff] text-[#2563eb]">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#1d4ed8]">
              Bienvenue
            </p>
            <h1 className="text-xl font-semibold text-[#0f172a]">Configurons ton profil</h1>
          </div>
        </div>

        {/* Progress */}
        <div className="mt-6 h-2 rounded-full bg-slate-100">
          <div
            className="h-2 rounded-full bg-[#2563eb] transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        <div className="mt-8 min-h-[220px]">
          <AnimatePresence mode="wait">
            <motion.div
              key={current}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.25 }}
            >
              {current === 'status' && (
                <div>
                  <h2 className="text-lg font-semibold text-[#0f172a]">Où en es-tu ?</h2>
                  <p className="mt-1 text-sm text-slate-500">
                    Cela nous aide à adapter les réponses de l’assistant.
                  </p>
                  <div className="mt-5 grid gap-3 sm:grid-cols-2">
                    {([
                      { v: 'prospective' as Status, t: 'Futur étudiant', d: 'Je m’intéresse à la faculté' },
                      { v: 'enrolled' as Status, t: 'Étudiant inscrit', d: 'Je suis déjà inscrit' },
                    ]).map((o) => (
                      <button
                        key={o.v}
                        type="button"
                        onClick={() => setStatus(o.v)}
                        className={`rounded-2xl border p-4 text-left transition-colors ${
                          status === o.v
                            ? 'border-[#2563eb] bg-[#eff6ff]'
                            : 'border-slate-200 bg-white hover:border-blue-200'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <GraduationCap className="h-5 w-5 text-[#2563eb]" />
                          {status === o.v && <Check className="h-4 w-4 text-[#2563eb]" />}
                        </div>
                        <p className="mt-3 font-semibold text-[#0f172a]">{o.t}</p>
                        <p className="mt-1 text-sm text-slate-500">{o.d}</p>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {current === 'year' && (
                <div>
                  <h2 className="text-lg font-semibold text-[#0f172a]">Ton année académique</h2>
                  <p className="mt-1 text-sm text-slate-500">Sélectionne ton niveau actuel.</p>
                  <div className="mt-5 flex flex-wrap gap-2">
                    {ACADEMIC_YEARS.map((y) => (
                      <button
                        key={y}
                        type="button"
                        onClick={() => setAcademicYear(y)}
                        className={`rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
                          academicYear === y
                            ? 'border-[#2563eb] bg-[#2563eb] text-white'
                            : 'border-slate-200 bg-white text-[#0f172a] hover:border-blue-200'
                        }`}
                      >
                        {y}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {current === 'bac' && (
                <div>
                  <h2 className="text-lg font-semibold text-[#0f172a]">Ton baccalauréat</h2>
                  <p className="mt-1 text-sm text-slate-500">Optionnel — tu peux passer cette étape.</p>
                  <div className="mt-5 space-y-4">
                    <div>
                      <label className="text-sm font-medium text-slate-600">Section</label>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {BAC_TYPES.map((b) => (
                          <button
                            key={b}
                            type="button"
                            onClick={() => setBacType(bacType === b ? '' : b)}
                            className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
                              bacType === b
                                ? 'border-[#2563eb] bg-[#eff6ff] text-[#1d4ed8]'
                                : 'border-slate-200 bg-white text-slate-600 hover:border-blue-200'
                            }`}
                          >
                            {b}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div>
                      <label htmlFor="bacScore" className="text-sm font-medium text-slate-600">
                        Score au bac
                      </label>
                      <input
                        id="bacScore"
                        type="number"
                        step="0.01"
                        value={bacScore}
                        onChange={(e) => setBacScore(e.target.value)}
                        placeholder="ex. 14.5"
                        className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-[#0f172a] outline-none focus:border-[#2563eb]"
                      />
                    </div>
                  </div>
                </div>
              )}

              {current === 'about' && (
                <div>
                  <h2 className="text-lg font-semibold text-[#0f172a]">Tes centres d’intérêt</h2>
                  <p className="mt-1 text-sm text-slate-500">
                    Sépare par des virgules. Optionnel.
                  </p>
                  <div className="mt-5 space-y-4">
                    <div>
                      <label htmlFor="interests" className="text-sm font-medium text-slate-600">
                        Centres d’intérêt
                      </label>
                      <input
                        id="interests"
                        value={interests}
                        onChange={(e) => setInterests(e.target.value)}
                        placeholder="ex. intelligence artificielle, mathématiques"
                        className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-[#0f172a] outline-none focus:border-[#2563eb]"
                      />
                    </div>
                    <div>
                      <label htmlFor="goals" className="text-sm font-medium text-slate-600">
                        Objectifs
                      </label>
                      <input
                        id="goals"
                        value={goals}
                        onChange={(e) => setGoals(e.target.value)}
                        placeholder="ex. réussir ma licence, trouver un stage"
                        className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-[#0f172a] outline-none focus:border-[#2563eb]"
                      />
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Controls */}
        <div className="mt-8 flex items-center justify-between">
          <button
            type="button"
            onClick={back}
            disabled={step === 0}
            className="inline-flex items-center gap-2 rounded-full px-4 py-2.5 text-sm font-medium text-slate-500 transition-colors hover:text-[#0f172a] disabled:opacity-0"
          >
            <ArrowLeft className="h-4 w-4" />
            Retour
          </button>
          <button
            type="button"
            onClick={next}
            disabled={!canNext() || submitting}
            className="inline-flex items-center gap-2 rounded-full bg-[#2563eb] px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-500/20 transition-colors hover:bg-[#1d4ed8] disabled:opacity-50"
          >
            {submitting ? 'Enregistrement…' : isLast ? 'Terminer' : 'Continuer'}
            {!submitting && (isLast ? <Check className="h-4 w-4" /> : <ArrowRight className="h-4 w-4" />)}
          </button>
        </div>
      </div>
    </div>
  );
}
