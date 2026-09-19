'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import {
  BookOpenText,
  Bot,
  ChevronRight,
  Home,
  UserRound,
} from 'lucide-react';
import { profileService, ProfileResponse } from '@/lib/services/profile';

const navigation = [
  { name: 'Aperçu', href: '/dashboard', icon: Home },
  { name: 'Assistant IA', href: '/chat', icon: Bot },
  { name: 'Mes cours', href: '/courses', icon: BookOpenText },
  { name: 'Profil', href: '/profile', icon: UserRound },
];

const STATUS_LABELS: Record<string, string> = {
  prospective: 'Futur étudiant',
  enrolled: 'Étudiant inscrit',
  admin: 'Administration',
};

// Honest completeness: fraction of onboarding-relevant fields that are filled.
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
  return Math.round((checks.filter(Boolean).length / checks.length) * 100);
}

export default function Sidebar() {
  const pathname = usePathname();
  const [profile, setProfile] = useState<ProfileResponse | null>(null);

  useEffect(() => {
    profileService.getProfile().then(setProfile).catch(() => {});
  }, []);

  const completeness = computeCompleteness(profile);

  const getInitials = (name?: string | null) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map((part) => part[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  };

  return (
    <aside className="flex h-full w-[280px] flex-col border-r border-[color:var(--sidebar-border)] bg-[var(--sidebar)] text-[var(--sidebar-foreground)]">
      <div className="flex items-center gap-3 border-b border-white/10 px-6 py-6">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--sidebar-primary)] text-sm font-semibold text-white shadow-lg shadow-blue-950/25">
          DC
        </div>
        <div>
          <p className="text-sm font-semibold text-white">Digital Campus</p>
          <p className="text-sm text-slate-300">Sciences de Bizerte</p>
        </div>
      </div>

      <nav className="flex-1 space-y-2 px-4 py-5">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`group flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-white/10 text-white shadow-[0_0_0_1px_rgba(255,255,255,0.08)]'
                  : 'text-slate-300 hover:bg-white/10 hover:text-white'
              }`}
            >
              <item.icon
                className={`h-4 w-4 flex-shrink-0 ${
                  isActive ? 'text-white' : 'text-slate-400 group-hover:text-white'
                }`}
                strokeWidth={2}
              />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto px-4 pb-5 pt-3">
        <div className="rounded-3xl border border-white/10 bg-white/5 p-4 shadow-[0_24px_50px_rgba(15,23,42,0.2)]">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 text-sm font-semibold text-white">
              {getInitials(profile?.full_name)}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-white">
                {profile?.full_name || profile?.email?.split('@')[0] || 'Étudiant'}
              </p>
              <p className="truncate text-sm text-slate-300">
                {profile?.student_status
                  ? STATUS_LABELS[profile.student_status] ?? profile.student_status
                  : 'Compte'}
              </p>
            </div>
          </div>

          <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-3">
            <div className="flex items-center justify-between text-sm text-slate-200">
              <span>Profil complété</span>
              <span>{completeness}%</span>
            </div>
            <div className="mt-3 h-2 rounded-full bg-white/10">
              <div
                className="h-2 rounded-full bg-[var(--sidebar-primary)]"
                style={{ width: `${completeness}%` }}
              />
            </div>
          </div>

          <Link
            href="/profile"
            className="mt-4 flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300 transition-colors hover:bg-white/10 hover:text-white"
          >
            <span>Voir le profil</span>
            <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </aside>
  );
}
