'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Sidebar from '@/components/layout/Sidebar';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, Search } from 'lucide-react';

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  '/dashboard': { title: 'Dashboard', subtitle: 'Overview of your academic journey' },
  '/chat': { title: 'AI Assistant', subtitle: 'Get personalized academic support' },
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

  useEffect(() => {
    // Temporarily bypassed for UI testing
    // const token = localStorage.getItem('token');
    // if (!token) {
    //   router.push('/login');
    // } else {
      setIsAuthenticated(true);
    // }
  }, [router]);

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
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Top header bar */}
        <header className="flex h-16 flex-shrink-0 items-center justify-between border-b border-border bg-background px-8">
          <div className="flex flex-col">
            <h1 className="text-sm font-bold tracking-tight text-foreground">{page.title}</h1>
            {page.subtitle && (
              <p className="text-[11px] text-muted-foreground font-medium">{page.subtitle}</p>
            )}
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-secondary/50 border border-border rounded-lg text-muted-foreground">
              <Search className="h-3.5 w-3.5" />
              <span className="text-xs font-medium">Search anything...</span>
              <kbd className="ml-4 pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border border-border bg-card px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
                <span className="text-xs">⌘</span>K
              </kbd>
            </div>

            <div className="flex items-center gap-2">
              <button className="relative flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-secondary hover:text-foreground transition-all">
                <Bell className="h-4 w-4" />
                <span className="absolute top-2 right-2 h-1.5 w-1.5 rounded-full bg-primary ring-2 ring-card" />
              </button>
              <div className="h-9 w-9 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center cursor-pointer hover:bg-primary/20 transition-all">
                <span className="text-xs font-bold text-primary tracking-tighter">JD</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto bg-background">
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
              className="h-full p-8 max-w-7xl mx-auto w-full"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
