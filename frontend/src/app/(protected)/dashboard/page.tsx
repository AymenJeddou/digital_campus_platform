'use client';

import { useEffect, useState } from 'react';
import { profileService, ProfileResponse } from '@/lib/services/profile';
import {
  CheckCircle2,
  Circle,
  GraduationCap,
  LayoutList,
  Trophy,
  ArrowRight,
  MessageSquare,
  TrendingUp,
  Sparkles,
} from 'lucide-react';
import { motion } from 'framer-motion';
import Link from 'next/link';

export default function DashboardPage() {
  const [onboardingStatus, setOnboardingStatus] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const status = await profileService.getOnboardingStatus();
        setOnboardingStatus(status);
      } catch (error) {
        console.error('Failed to load onboarding status');
      } finally {
        setIsLoading(false);
      }
    };
    fetchStatus();
  }, []);

  const stats = [
    {
      name: 'Student Status',
      value: onboardingStatus?.student_status || 'Not configured',
      icon: GraduationCap,
      iconBg: 'bg-primary/10',
      iconColor: 'text-primary',
      accent: 'border-l-primary',
    },
    {
      name: 'Academic Year',
      value: onboardingStatus?.academic_year || 'Not configured',
      icon: Trophy,
      iconBg: 'bg-primary/10',
      iconColor: 'text-primary',
      accent: 'border-l-primary',
    },
    {
      name: 'Setup Progress',
      value: onboardingStatus?.onboarding_completed ? 'Complete' : 'In progress',
      icon: LayoutList,
      iconBg: onboardingStatus?.onboarding_completed ? 'bg-emerald-500/10' : 'bg-amber-500/10',
      iconColor: onboardingStatus?.onboarding_completed ? 'text-emerald-500' : 'text-amber-500',
      accent: onboardingStatus?.onboarding_completed ? 'border-l-emerald-500' : 'border-l-amber-500',
    },
  ];

  const steps = [
    {
      label: 'Complete your profile',
      description: 'Add your academic year and learning goals.',
      done: !!(onboardingStatus?.student_status && onboardingStatus?.academic_year),
      href: '/profile',
      cta: 'Go to Profile',
    },
    {
      label: 'Start a conversation',
      description: 'Get personalized academic support from the AI assistant.',
      done: false,
      href: '/chat',
      cta: 'Open Assistant',
    },
  ];

  const completedCount = steps.filter((s) => s.done).length;
  const progressPct = Math.round((completedCount / steps.length) * 100);

  return (
    <div className="space-y-8 max-w-6xl mx-auto">

      {/* Welcome banner */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="bg-card border border-border rounded-2xl p-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6 shadow-sm shadow-primary/5"
      >
        <div className="space-y-1">
          <h2 className="text-2xl font-bold tracking-tight text-foreground">Welcome back</h2>
          <p className="text-sm text-muted-foreground max-w-md leading-relaxed">
            Your Digital Campus dashboard gives you a real-time view of your academic profile and progress.
          </p>
        </div>
        <Link
          href="/chat"
          className="inline-flex items-center gap-2.5 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-semibold px-6 py-3 rounded-xl transition-all shadow-sm shadow-primary/20 whitespace-nowrap group"
        >
          <Sparkles className="h-4 w-4 transition-transform group-hover:scale-110" />
          Ask the Assistant
        </Link>
      </motion.div>

      {/* Stat cards */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.name}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.07, duration: 0.3 }}
            className={`bg-card border border-border rounded-2xl p-6 border-l-4 ${stat.accent} hover:shadow-md transition-all duration-300 group`}
          >
            <div className="flex items-start justify-between">
              <div className="space-y-3">
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">{stat.name}</p>
                <p className="text-lg font-bold text-foreground capitalize tracking-tight">
                  {isLoading ? (
                    <span className="inline-block h-6 w-32 bg-secondary rounded-lg animate-pulse" />
                  ) : (
                    stat.value
                  )}
                </p>
              </div>
              <div className={`p-3 rounded-xl ${stat.iconBg} transition-transform group-hover:scale-110`}>
                <stat.icon className="h-5 w-5 ${stat.iconColor}" />
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Two column section */}
      <div className="grid gap-6 lg:grid-cols-5">

        {/* Getting started — 3 cols */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25, duration: 0.3 }}
          className="lg:col-span-3 bg-card border border-border rounded-2xl overflow-hidden shadow-sm"
        >
          <div className="px-8 py-6 border-b border-border flex items-center justify-between bg-secondary/30">
            <div className="space-y-1">
              <h3 className="text-sm font-bold tracking-tight text-foreground">Setup Checklist</h3>
              <p className="text-xs text-muted-foreground">Complete all steps to unlock the full experience.</p>
            </div>
            <span className="text-[10px] font-bold text-primary bg-primary/10 px-3 py-1 rounded-full uppercase tracking-wider">
              {completedCount}/{steps.length} completed
            </span>
          </div>

          {/* Progress bar */}
          <div className="px-8 pt-6">
            <div className="h-2 bg-secondary rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-primary rounded-full shadow-[0_0_10px_rgba(var(--primary),0.5)]"
                initial={{ width: 0 }}
                animate={{ width: `${progressPct}%` }}
                transition={{ duration: 0.8, delay: 0.4, ease: [0.23, 1, 0.32, 1] }}
              />
            </div>
          </div>

          <div className="px-8 py-6 space-y-4">
            {steps.map((step) => (
              <Link
                key={step.label}
                href={step.href}
                className="group flex items-center gap-5 rounded-xl p-4 hover:bg-secondary/50 transition-all border border-transparent hover:border-border"
              >
                <div className="flex-shrink-0">
                  {step.done ? (
                    <div className="h-6 w-6 rounded-full bg-emerald-500/10 flex items-center justify-center">
                      <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    </div>
                  ) : (
                    <div className="h-6 w-6 rounded-full border-2 border-border group-hover:border-primary/50 transition-colors flex items-center justify-center">
                      <Circle className="h-2 w-2 text-transparent group-hover:text-primary/30 transition-colors" />
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-bold tracking-tight ${step.done ? 'text-muted-foreground line-through opacity-60' : 'text-foreground'}`}>
                    {step.label}
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5 truncate">{step.description}</p>
                </div>
                {!step.done && (
                  <span className="text-xs font-bold text-primary group-hover:translate-x-1 transition-transform flex items-center gap-1.5 whitespace-nowrap uppercase tracking-wider">
                    {step.cta}
                    <ArrowRight className="h-3.5 w-3.5" />
                  </span>
                )}
              </Link>
            ))}
          </div>
        </motion.div>

        {/* Quick info panel — 2 cols */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.32, duration: 0.3 }}
          className="lg:col-span-2 flex flex-col gap-6"
        >
          {/* AI CTA card */}
          <div className="flex-1 bg-primary rounded-2xl p-6 flex flex-col justify-between text-primary-foreground relative overflow-hidden group">
            <div className="absolute -right-8 -top-8 h-32 w-32 bg-white/10 rounded-full blur-3xl transition-transform group-hover:scale-150" />
            <div className="relative z-10">
              <div className="p-3 bg-white/20 backdrop-blur-md rounded-xl w-fit mb-6">
                <MessageSquare className="h-5 w-5 text-white" />
              </div>
              <p className="text-lg font-bold tracking-tight text-white">AI-Powered Assistance</p>
              <p className="text-sm text-primary-foreground/80 mt-2 leading-relaxed">
                Ask questions, get explanations, and receive personalized study recommendations instantly.
              </p>
            </div>
            <Link
              href="/chat"
              className="mt-8 relative z-10 inline-flex items-center justify-center gap-2 bg-white text-primary text-xs font-bold px-5 py-3 rounded-xl hover:bg-primary-foreground transition-all shadow-lg shadow-black/10 group/btn"
            >
              Open Chat
              <ArrowRight className="h-4 w-4 transition-transform group-hover/btn:translate-x-1" />
            </Link>
          </div>

          {/* Platform info card */}
          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-5">
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
              <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Platform Status</p>
            </div>
            <ul className="space-y-4">
              {[
                { label: 'AI Assistant', status: 'Active' },
                { label: 'Profile Setup', status: onboardingStatus?.onboarding_completed ? 'Complete' : 'Pending' },
              ].map((item) => (
                <li key={item.label} className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground font-bold">{item.label}</span>
                  <span className={`font-bold px-3 py-1 rounded-full text-[10px] uppercase tracking-wider ${item.status === 'Active' || item.status === 'Complete'
                      ? 'bg-emerald-500/10 text-emerald-500'
                      : 'bg-amber-500/10 text-amber-500'
                    }`}>
                    {item.status}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
