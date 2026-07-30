'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Sidebar from '@/components/layout/Sidebar';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, LogOut, Search } from 'lucide-react';
import { getToken, removeToken } from '@/lib/auth';
import { profileService, ProfileResponse } from '@/lib/services/profile';

const STATUS_LABELS: Record<string, string> = {
  prospective: 'Futur étudiant',
  enrolled: 'Étudiant inscrit',
  admin: 'Administration',
};

function initials(name?: string | null, email?: string): string {
  if (name) {
    return name
      .split(' ')
      .map((p) => p[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  }
  if (email) return email.substring(0, 2).toUpperCase();
  return 'U';
}

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  '/dashboard': { title: 'Dashboard', subtitle: 'Overview of your academic journey' },
  '/chat': { title: 'AI Assistant', subtitle: 'Get personalized academic support' },
  '/courses': { title: 'My Courses', subtitle: 'Bring in your courses and ask about them' },
  '/profile': { title: 'Profile Settings', subtitle: 'Manage your account and preferences' },
};

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [profile, setProfile] = useState<ProfileResponse | null>(null);

  useEffect(() => {
    // Guard every protected route: no token -> bounce to /login.
    const token = getToken();
    if (!token) {
      router.replace('/login');
      return;
    }
    setIsAuthenticated(true);
    profileService.getProfile().then(setProfile).catch(() => {});
  }, [router]);

  const handleLogout = () => {
    removeToken();
    router.replace('/login');
  };

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="h-10 w-10 border-2 border-primary/20 border-t-primary rounded-full animate-spin" />
          <p className="text-sm text-muted-foreground font-medium">Loading your campus...</p>
        </div>
      </div>
    );
  }

  const page = pageTitles[pathname] ?? { title: 'Digital Campus', subtitle: '' };

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--background)] text-[var(--foreground)]">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <header className="sticky top-0 z-20 flex h-20 flex-shrink-0 items-center justify-between border-b border-[color:var(--border)]/70 bg-[color:var(--background)]/95 px-6 backdrop-blur-xl sm:px-8">
          <div className="flex items-center gap-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-200 bg-white px-4 py-2 text-sm font-medium text-[#1d4ed8] shadow-sm">
              <span className="h-2 w-2 rounded-full bg-[#2563eb]" />
              <span>Faculty of Digital Systems</span>
            </div>
            <div className="hidden lg:block">
              <h1 className="text-sm font-semibold tracking-tight text-[#0f172a]">{page.title}</h1>
              {page.subtitle && <p className="text-xs text-slate-500">{page.subtitle}</p>}
            </div>
          </div>

          <div className="flex items-center gap-3 sm:gap-4">
            <label className="hidden md:flex min-w-[340px] items-center gap-3 rounded-full border border-slate-200 bg-white px-4 py-3 shadow-sm">
              <Search className="h-4 w-4 text-slate-400" />
              <input
                aria-label="Search dashboard"
                placeholder="Search courses, documents, or faculty"
                className="w-full bg-transparent text-sm text-slate-700 outline-none placeholder:text-slate-400"
              />
            </label>

            <button className="relative flex h-12 w-12 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 shadow-sm transition-colors hover:border-blue-200 hover:text-[#1d4ed8]">
              <Bell className="h-5 w-5" />
              <span className="absolute right-3 top-3 h-2.5 w-2.5 rounded-full border-2 border-white bg-[#2563eb]" />
            </button>

            <div className="hidden items-center gap-3 rounded-full border border-slate-200 bg-white px-3 py-2 shadow-sm lg:flex">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#eff6ff] text-sm font-semibold text-[#1d4ed8]">
                {initials(profile?.full_name, profile?.email)}
              </div>
              <div className="pr-2">
                <p className="text-sm font-semibold text-[#0f172a]">
                  {profile?.full_name || profile?.email?.split('@')[0] || 'Étudiant'}
                </p>
                <p className="text-xs text-slate-500">
                  {profile?.student_status
                    ? STATUS_LABELS[profile.student_status] ?? profile.student_status
                    : 'Compte'}
                </p>
              </div>
            </div>

            <button
              onClick={handleLogout}
              aria-label="Se déconnecter"
              title="Se déconnecter"
              className="relative flex h-12 w-12 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 shadow-sm transition-colors hover:border-blue-200 hover:text-[#1d4ed8]"
            >
              <LogOut className="h-5 w-5" />
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto bg-[var(--background)]">
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
              className="mx-auto h-full w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
