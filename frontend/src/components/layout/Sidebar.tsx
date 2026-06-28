'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { 
  Home, BookOpen, Calendar, ClipboardList, CheckSquare, 
  Users, BarChart2, Folder, Mail, Settings, ChevronDown, 
  Sparkles, Sun, Moon
} from 'lucide-react';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import { profileService, ProfileResponse } from '@/lib/services/profile';

const navigation = [
  { name: 'AI Assistant', href: '/chat', icon: Sparkles },
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Settings', href: '/profile', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [profile, setProfile] = useState<ProfileResponse | null>(null);

  useEffect(() => {
    setMounted(true);
    // Fetch profile for the bottom section
    profileService.getProfile().then(setProfile).catch(() => {});
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  const getInitials = (name?: string) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  };

  return (
    <div className="flex h-full w-[260px] flex-col bg-background border-r border-border transition-colors z-10">
      <style jsx>{`
      `}</style>
      
      {/* Brand */}
      <div className="flex h-[72px] items-center gap-3 px-6 pt-2">
        <div className="flex h-8 w-8 items-center justify-center bg-primary rounded-md shadow-sm">
           <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 text-white"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>
        </div>
        <span className="text-[17px] font-bold tracking-tight text-foreground">Digital Campus</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1 scrollbar-hide">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`group flex items-center gap-3.5 rounded-lg px-3 py-2.5 text-[14px] font-medium transition-all ${
                isActive
                  ? 'bg-primary/10 dark:bg-primary/20 text-primary dark:text-primary'
                  : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
              }`}
            >
              <item.icon
                className={`h-4 w-4 flex-shrink-0 ${
                  isActive ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'
                }`}
                strokeWidth={2}
              />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Theme toggle & Profile Footer */}
      <div className="p-4 mt-auto space-y-2">
        <div 
          className="flex items-center gap-3 p-3 rounded-xl hover:bg-secondary cursor-pointer transition-colors"
          onClick={handleLogout}
          title="Click to logout"
        >
          <div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center flex-shrink-0 text-white font-semibold text-sm">
            {getInitials(profile?.full_name)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-foreground truncate">
              {profile?.full_name || 'Student'}
            </p>
            <p className="text-xs text-muted-foreground truncate">
              {profile?.student_status || 'Undergraduate'}
            </p>
          </div>
          <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
        </div>

        {mounted && (
          <div className="flex justify-center border-t border-border pt-4">
            <button
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="p-2 rounded-lg text-muted-foreground hover:bg-secondary transition-colors"
              title="Toggle theme"
            >
              {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
