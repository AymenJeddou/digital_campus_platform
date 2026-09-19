'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  ArrowUpRight,
  Bot,
  BookOpenText,
  ChevronRight,
  Clock3,
  FileText,
  Layers3,
  MessageSquareText,
  Plus,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';
import { profileService, ProfileResponse } from '@/lib/services/profile';
import { coursesService, EnrolledCourse } from '@/lib/services/courses';
import { chatService, ChatSession } from '@/lib/services/chat';

function firstName(profile: ProfileResponse | null): string {
  if (profile?.full_name) return profile.full_name.split(' ')[0];
  if (profile?.email) return profile.email.split('@')[0];
  return 'là';
}

// Honest completeness: fraction of the onboarding-relevant fields that are filled.
function computeCompleteness(p: ProfileResponse | null): number {
  if (!p) return 0;
  const checks = [
    !!p.full_name,
    !!p.student_status,
    !!p.academic_year,
    !!p.bac_type,
    p.bac_score != null,
    !!(p.interests && p.interests.length),
    !!(p.goals && p.goals.length),
  ];
  const filled = checks.filter(Boolean).length;
  return Math.round((filled / checks.length) * 100);
}

function relativeDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' });
}

const STATUS_LABELS: Record<string, string> = {
  prospective: 'Futur étudiant',
  enrolled: 'Étudiant inscrit',
  admin: 'Administration',
};

export default function DashboardPage() {
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [courses, setCourses] = useState<EnrolledCourse[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    Promise.allSettled([
      profileService.getProfile(),
      coursesService.listMine(),
      chatService.getSessions(),
    ]).then(([p, c, s]) => {
      if (!active) return;
      if (p.status === 'fulfilled') setProfile(p.value);
      if (c.status === 'fulfilled') setCourses(c.value);
      if (s.status === 'fulfilled') setSessions(s.value);
      setLoading(false);
    });
    return () => {
      active = false;
    };
  }, []);

  const completeness = useMemo(() => computeCompleteness(profile), [profile]);
  const totalMaterials = useMemo(
    () => courses.reduce((sum, c) => sum + (c.material_count || 0), 0),
    [courses],
  );
  const recentSessions = useMemo(() => sessions.slice(0, 4), [sessions]);

  const stats = [
    {
      label: 'Cours suivis',
      value: String(courses.length),
      detail: courses.length ? 'Ajoutés à ton espace' : 'Aucun cours pour l’instant',
      icon: BookOpenText,
    },
    {
      label: 'Supports de cours',
      value: String(totalMaterials),
      detail: totalMaterials ? 'Documents disponibles' : 'Ajoute tes premiers supports',
      icon: FileText,
    },
    {
      label: 'Conversations',
      value: String(sessions.length),
      detail: sessions.length ? 'Avec l’assistant IA' : 'Pose ta première question',
      icon: MessageSquareText,
    },
    {
      label: 'Profil complété',
      value: `${completeness}%`,
      detail: profile?.onboarding_completed ? 'Onboarding terminé' : 'Complète ton profil',
      icon: CheckCircle2,
    },
  ];

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center py-24">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#2563eb]/20 border-t-[#2563eb]" />
      </div>
    );
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
      <div className="space-y-6">
        {/* Greeting */}
        <section className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-[0_24px_55px_rgba(15,23,42,0.07)]">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-2xl space-y-4">
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#1d4ed8]">
                Ton espace
              </p>
              <h2 className="text-3xl font-semibold tracking-tight text-[#0f172a] sm:text-4xl">
                Bonjour {firstName(profile)}, bienvenue sur ton campus.
              </h2>
              <p className="max-w-2xl text-base leading-7 text-slate-600">
                Retrouve tes cours, tes conversations avec l’assistant, et pose des questions
                sourcées sur la Faculté des Sciences de Bizerte.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:min-w-[320px] lg:grid-cols-1">
              <div className="rounded-2xl border border-slate-200 bg-[var(--background)] px-4 py-3">
                <p className="text-sm text-slate-500">Statut</p>
                <p className="mt-1 text-lg font-semibold text-[#0f172a]">
                  {profile?.student_status
                    ? STATUS_LABELS[profile.student_status] ?? profile.student_status
                    : '—'}
                </p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-[var(--background)] px-4 py-3">
                <p className="text-sm text-slate-500">Année académique</p>
                <p className="mt-1 text-lg font-semibold text-[#0f172a]">
                  {profile?.academic_year || 'Non renseignée'}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {stats.map(({ label, value, detail, icon: Icon }) => (
            <article
              key={label}
              className="rounded-3xl border border-slate-200/80 bg-white p-5 shadow-[0_18px_40px_rgba(15,23,42,0.06)]"
            >
              <div className="flex items-center justify-between">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#eff6ff] text-[#2563eb]">
                  <Icon className="h-5 w-5" />
                </div>
              </div>
              <p className="mt-5 text-sm font-medium text-slate-500">{label}</p>
              <p className="mt-2 text-3xl font-semibold tracking-tight text-[#0f172a]">{value}</p>
              <p className="mt-2 text-sm leading-6 text-slate-500">{detail}</p>
            </article>
          ))}
        </section>

        {/* Courses */}
        <section className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-[0_24px_55px_rgba(15,23,42,0.07)]">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#1d4ed8]">
                Mes cours
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[#0f172a]">
                Tes matières et leurs supports
              </h2>
            </div>
            <Link
              href="/courses"
              className="inline-flex items-center gap-2 rounded-full bg-[#2563eb] px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-500/20 transition-colors hover:bg-[#1d4ed8]"
            >
              <Plus className="h-4 w-4" />
              Ajouter un cours
            </Link>
          </div>

          <div className="mt-6 space-y-3">
            {courses.length === 0 && (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-[#eff6ff] px-4 py-8 text-center">
                <p className="text-sm font-medium text-[#0f172a]">Aucun cours pour l’instant</p>
                <p className="mt-1 text-sm text-slate-500">
                  Ajoute un cours pour poser des questions sur tes propres supports.
                </p>
                <Link
                  href="/courses"
                  className="mt-4 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-[#1d4ed8] transition-colors hover:border-blue-200"
                >
                  <Plus className="h-4 w-4" />
                  Ajouter mon premier cours
                </Link>
              </div>
            )}

            {courses.map((course) => (
              <article
                key={course.id}
                className="flex items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-[#eff6ff] px-4 py-4"
              >
                <div className="flex min-w-0 items-center gap-4">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-[#2563eb] shadow-sm">
                    <BookOpenText className="h-5 w-5" />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-[#0f172a]">{course.name}</p>
                    <p className="truncate text-sm text-slate-500">
                      {course.material_count} support{course.material_count === 1 ? '' : 's'}
                      {course.code ? ` · ${course.code}` : ''}
                    </p>
                  </div>
                </div>

                <Link
                  href={`/chat?course=${course.id}&name=${encodeURIComponent(course.name)}`}
                  className="inline-flex shrink-0 items-center gap-2 rounded-full bg-white px-3 py-2 text-xs font-semibold text-[#1d4ed8] shadow-sm transition-colors hover:text-[#2563eb]"
                >
                  <Bot className="h-4 w-4" />
                  Poser une question
                </Link>
              </article>
            ))}
          </div>
        </section>
      </div>

      {/* Sidebar column */}
      <div className="space-y-6 xl:sticky xl:top-24 xl:self-start">
        {/* Complete your profile */}
        {!profile?.onboarding_completed && (
          <section className="rounded-3xl bg-[#0f172a] p-6 text-white shadow-[0_26px_60px_rgba(15,23,42,0.28)]">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-400">
                  À faire
                </p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight">Complète ton profil</h2>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 text-[#93c5fd]">
                <ArrowUpRight className="h-5 w-5" />
              </div>
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-300">
              Renseigne ton statut et tes centres d’intérêt pour des réponses plus adaptées.
            </p>
            <div className="mt-6 rounded-3xl border border-white/10 bg-white/5 p-4">
              <div className="flex items-center justify-between text-sm text-slate-300">
                <span>Profil complété</span>
                <span>{completeness}%</span>
              </div>
              <div className="mt-3 h-2 rounded-full bg-white/10">
                <div
                  className="h-2 rounded-full bg-[#2563eb]"
                  style={{ width: `${completeness}%` }}
                />
              </div>
            </div>
            <Link
              href="/profile"
              className="mt-5 inline-flex items-center gap-2 rounded-full bg-[#2563eb] px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[#1d4ed8]"
            >
              Compléter maintenant
              <ChevronRight className="h-4 w-4" />
            </Link>
          </section>
        )}

        {/* Recent conversations */}
        <section className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-[0_24px_55px_rgba(15,23,42,0.07)]">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#1d4ed8]">
                Assistant IA
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[#0f172a]">
                Conversations récentes
              </h2>
            </div>
            <Clock3 className="h-5 w-5 text-slate-400" />
          </div>

          <div className="mt-6 space-y-3">
            {recentSessions.length === 0 && (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-[#eff6ff] px-4 py-6 text-center">
                <p className="text-sm font-medium text-[#0f172a]">Aucune conversation</p>
                <p className="mt-1 text-sm text-slate-500">
                  Démarre une discussion avec l’assistant.
                </p>
              </div>
            )}

            {recentSessions.map((s) => (
              <Link
                key={s.id}
                href="/chat"
                className="flex items-center gap-4 rounded-2xl bg-[#eff6ff] p-4 transition-colors hover:bg-[#dbeafe]"
              >
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-[#2563eb] shadow-sm">
                  <MessageSquareText className="h-5 w-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-medium leading-6 text-[#0f172a]">Conversation</p>
                  <p className="mt-0.5 text-sm text-slate-500">{relativeDate(s.created_at)}</p>
                </div>
                <ChevronRight className="h-4 w-4 shrink-0 text-slate-400" />
              </Link>
            ))}

            <Link
              href="/chat"
              className="flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-[#1d4ed8] transition-colors hover:border-blue-200"
            >
              <Sparkles className="h-4 w-4" />
              Ouvrir l’assistant
            </Link>
          </div>
        </section>

        {/* Quick tip */}
        <section className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-[0_24px_55px_rgba(15,23,42,0.07)]">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#eff6ff] text-[#2563eb]">
              <Layers3 className="h-5 w-5" />
            </div>
            <h3 className="text-base font-semibold text-[#0f172a]">Le savais-tu ?</h3>
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-600">
            L’assistant cite toujours les documents officiels utilisés pour répondre. Vérifie les
            sources en bas de chaque réponse.
          </p>
        </section>
      </div>
    </div>
  );
}
