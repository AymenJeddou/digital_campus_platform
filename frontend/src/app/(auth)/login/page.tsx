'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/services/auth';
import { toast } from 'sonner';
import Link from 'next/link';
import { BookOpen, Users, Calendar, BarChart2, Eye, EyeOff, Sun, Moon } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useEffect } from 'react';

const GoogleIcon = () => (
  <svg className="h-4 w-4" viewBox="0 0 533.5 544.3" aria-hidden="true">
    <path d="M533.5 278.4c0-18.5-1.5-37.1-4.7-55.3H272.1v104.8h147c-6.1 33.8-25.7 63.7-54.4 82.7v68h87.7c51.5-47.4 81.1-117.4 81.1-200.2z" fill="#4285f4" />
    <path d="M272.1 544.3c73.4 0 135.3-24.1 180.4-65.7l-87.7-68c-24.4 16.6-55.9 26-92.6 26-71 0-131.2-47.9-152.8-112.3H28.9v70.1c46.2 91.9 140.3 149.9 243.2 149.9z" fill="#34a853" />
    <path d="M119.3 324.3c-11.4-33.8-11.4-70.4 0-104.2V150H28.9c-38.6 76.9-38.6 167.5 0 244.4l90.4-70.1z" fill="#fbbc04" />
    <path d="M272.1 107.7c38.8-.6 76.3 14 104.4 40.8l77.7-77.7C405 24.6 339.7-.8 272.1 0 169.2 0 75.1 58 28.9 150l90.4 70.1c21.5-64.5 81.8-112.4 152.8-112.4z" fill="#ea4335" />
  </svg>
);



const inputBase =
  'w-full pl-4 pr-10 py-3 rounded-md text-sm font-medium bg-background border border-border placeholder-muted-foreground/60 text-foreground focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all duration-150';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const response = await authService.login({ username: email, password });
      localStorage.setItem('token', response.access_token);
      toast.success('Welcome back!');
      router.push('/dashboard');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Invalid email or password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-stretch">
      {/* ── Left panel: Dark Brand Section ─────────────────── */}
      <div className="hidden lg:flex flex-1 flex-col p-12 relative overflow-hidden" style={{ backgroundColor: '#0f142b' }}>
        {/* Geometric line background (approximated with CSS gradients for simplicity) */}
        <div className="absolute inset-0 opacity-20 pointer-events-none"
             style={{
               backgroundImage: `
                 linear-gradient(45deg, transparent 48%, rgba(255,255,255,0.2) 49%, rgba(255,255,255,0.2) 51%, transparent 52%),
                 linear-gradient(-45deg, transparent 48%, rgba(255,255,255,0.2) 49%, rgba(255,255,255,0.2) 51%, transparent 52%),
                 radial-gradient(circle at 100% 100%, transparent 40%, rgba(255,255,255,0.1) 41%, rgba(255,255,255,0.1) 42%, transparent 43%),
                 radial-gradient(circle at 0% 100%, transparent 60%, rgba(255,255,255,0.1) 61%, rgba(255,255,255,0.1) 62%, transparent 63%)
               `,
               backgroundSize: '400px 400px, 400px 400px, 600px 600px, 800px 800px'
             }}
        />

        <div className="relative z-10 flex flex-col h-full max-w-xl mx-auto w-full">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-10 items-center justify-center">
              {/* Mockup logo shape */}
              <div className="w-4 h-8 bg-blue-500 rounded-sm transform skew-y-6" />
              <div className="w-4 h-8 bg-blue-300 rounded-sm transform -skew-y-6 ml-0.5" />
            </div>
            <span className="text-white font-semibold text-lg tracking-tight">Digital Campus</span>
          </div>

          {/* Typography */}
          <div className="flex-1 flex flex-col justify-center mt-12">
            <h1 className="text-[44px] font-bold text-white leading-[1.1] tracking-tight">
              Your academic<br />journey, elevated.
            </h1>
            <p className="mt-6 text-slate-300 text-base leading-relaxed max-w-md font-medium">
              Digital Campus is your all-in-one platform to learn, collaborate, and achieve more—every day.
            </p>

            {/* Features */}
            <div className="mt-16 space-y-8">
              {[
                { label: 'Smart Learning', desc: 'Access modern courses and personalized learning paths.', icon: BookOpen },
                { label: 'Seamless Collaboration', desc: 'Work with peers and faculty in real time.', icon: Users },
                { label: 'Organized Campus', desc: 'Manage classes, assignments, and deadlines effortlessly.', icon: Calendar },
                { label: 'Track Your Progress', desc: 'Monitor your performance and reach your goals.', icon: BarChart2 },
              ].map((feat) => (
                <div key={feat.label} className="flex items-start gap-5">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-white/10 bg-white/5 flex-shrink-0">
                    <feat.icon className="h-5 w-5 text-blue-400" strokeWidth={1.5} />
                  </div>
                  <div>
                    <p className="text-[15px] font-semibold text-white">{feat.label}</p>
                    <p className="text-sm text-slate-400 mt-1">{feat.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Right panel: Form Section ─────────────────────────── */}
      <div className="flex-1 flex flex-col justify-center px-8 sm:px-16 lg:px-24 bg-background relative">
        {mounted && (
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="absolute top-6 right-6 p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/50 transition-colors"
            title="Toggle theme"
          >
            {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </button>
        )}
        <div className="w-full max-w-md mx-auto">
          {/* Mobile Logo */}
          <div className="flex items-center gap-3 mb-10 lg:hidden">
            <div className="flex h-8 w-10 items-center justify-center">
              <div className="w-4 h-8 bg-blue-600 rounded-sm transform skew-y-6" />
              <div className="w-4 h-8 bg-blue-400 rounded-sm transform -skew-y-6 ml-0.5" />
            </div>
            <span className="text-foreground font-semibold text-lg tracking-tight">Digital Campus</span>
          </div>

          <div className="mb-10 text-left">
            <h2 className="text-[32px] font-bold tracking-tight text-foreground">Welcome back</h2>
            <p className="mt-2 text-[15px] text-muted-foreground">
              Login to continue to Digital Campus
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label htmlFor="email" className="text-[13px] font-medium text-foreground">
                Email address
              </label>
              <div className="relative">
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  placeholder="name@university.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={inputBase}
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label htmlFor="password" className="text-[13px] font-medium text-foreground">
                  Password
                </label>
                <Link href="#" className="text-[13px] font-medium text-primary hover:underline">
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={inputBase}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground p-1"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center gap-2 pt-2 pb-4">
              <input
                type="checkbox"
                id="remember"
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <label htmlFor="remember" className="text-[13px] font-medium text-muted-foreground cursor-pointer">
                Remember me
              </label>
            </div>

            <button
              id="login-submit-btn"
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center bg-[#1d3557] hover:bg-[#152744] text-white text-[15px] font-medium py-3 rounded-md transition-colors disabled:opacity-70 disabled:cursor-not-allowed"
              style={{ backgroundColor: '#1e3a8a' }} // Deep blue matching mockup
            >
              {isLoading ? (
                <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                'Log in'
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-background px-4 text-muted-foreground/70">or continue with</span>
            </div>
          </div>

          {/* Social buttons */}
          <div className="grid grid-cols-1 gap-3 mb-10">
            <button
              type="button"
              className="flex items-center justify-center gap-2 py-2.5 px-3 bg-background border border-border rounded-md text-[13px] font-medium text-foreground hover:bg-secondary/50 transition-colors"
            >
              <GoogleIcon />
              Continue with Google
            </button>
          </div>

          <p className="text-left text-[13px] text-muted-foreground">
            Don't have an account?{' '}
            <Link href="/register" className="font-medium text-primary hover:underline">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
