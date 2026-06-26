'use client';

import { useEffect, useState } from 'react';
import { profileService } from '@/lib/services/profile';
import {
  CheckCircle2,
  Circle,
  GraduationCap,
  LayoutList,
  Trophy,
  ArrowRight,
  MessageSquare,
  TrendingUp,
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
      iconBg: 'bg-indigo-50',
      iconColor: 'text-indigo-600',
      accent: 'border-l-indigo-500',
    },
    {
      name: 'Academic Year',
      value: onboardingStatus?.academic_year || 'Not configured',
      icon: Trophy,
      iconBg: 'bg-violet-50',
      iconColor: 'text-violet-600',
      accent: 'border-l-violet-500',
    },
    {
      name: 'Setup Progress',
      value: onboardingStatus?.onboarding_completed ? 'Complete' : 'In progress',
      icon: LayoutList,
      iconBg: onboardingStatus?.onboarding_completed ? 'bg-emerald-50' : 'bg-amber-50',
      iconColor: onboardingStatus?.onboarding_completed ? 'text-emerald-600' : 'text-amber-600',
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
    <div className="space-y-6 max-w-6xl mx-auto">

      {/* Welcome banner */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="bg-white border border-gray-200 rounded-xl p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
      >
        <div>
          <h2 className="text-xl font-bold text-gray-900">Welcome back 👋</h2>
          <p className="mt-1 text-sm text-gray-500">
            Your Digital Campus dashboard gives you a real-time view of your academic profile.
          </p>
        </div>
        <Link
          href="/chat"
          className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors duration-150 whitespace-nowrap"
        >
          <MessageSquare className="h-4 w-4" />
          Ask the Assistant
        </Link>
      </motion.div>

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.name}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.07, duration: 0.3 }}
            className={`bg-white border border-gray-200 rounded-xl p-5 border-l-4 ${stat.accent} hover:shadow-sm transition-shadow duration-200`}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{stat.name}</p>
                <p className="mt-2 text-lg font-bold text-gray-900 capitalize">
                  {isLoading ? (
                    <span className="inline-block h-6 w-32 bg-gray-100 rounded animate-pulse" />
                  ) : (
                    stat.value
                  )}
                </p>
              </div>
              <div className={`p-2.5 rounded-lg ${stat.iconBg}`}>
                <stat.icon className={`h-5 w-5 ${stat.iconColor}`} />
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Two column section */}
      <div className="grid gap-4 lg:grid-cols-5">

        {/* Getting started — 3 cols */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25, duration: 0.3 }}
          className="lg:col-span-3 bg-white border border-gray-200 rounded-xl overflow-hidden"
        >
          <div className="px-6 py-5 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-gray-900">Setup Checklist</h3>
              <p className="text-xs text-gray-400 mt-0.5">Complete all steps to unlock the full experience.</p>
            </div>
            <span className="text-xs font-semibold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full">
              {completedCount}/{steps.length} done
            </span>
          </div>

          {/* Progress bar */}
          <div className="px-6 pt-4">
            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-indigo-500 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${progressPct}%` }}
                transition={{ duration: 0.6, delay: 0.4, ease: 'easeOut' }}
              />
            </div>
          </div>

          <div className="px-6 py-5 space-y-3">
            {steps.map((step) => (
              <Link
                key={step.label}
                href={step.href}
                className="group flex items-center gap-4 rounded-lg p-3 hover:bg-gray-50 transition-colors"
              >
                <div className="flex-shrink-0">
                  {step.done ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                  ) : (
                    <Circle className="h-5 w-5 text-gray-300 group-hover:text-indigo-400 transition-colors" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-semibold ${step.done ? 'text-gray-400 line-through' : 'text-gray-800'}`}>
                    {step.label}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5 truncate">{step.description}</p>
                </div>
                {!step.done && (
                  <span className="text-xs font-medium text-indigo-600 group-hover:text-indigo-700 flex items-center gap-1 whitespace-nowrap">
                    {step.cta}
                    <ArrowRight className="h-3 w-3" />
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
          className="lg:col-span-2 flex flex-col gap-4"
        >
          {/* AI CTA card */}
          <div className="flex-1 bg-indigo-600 rounded-xl p-5 flex flex-col justify-between text-white">
            <div className="p-2.5 bg-indigo-500 rounded-lg w-fit mb-4">
              <MessageSquare className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="text-sm font-bold text-white">AI-Powered Assistance</p>
              <p className="text-xs text-indigo-200 mt-1 leading-relaxed">
                Ask questions, get explanations, and receive personalized study recommendations.
              </p>
              <Link
                href="/chat"
                className="mt-4 inline-flex items-center gap-1.5 bg-white text-indigo-700 text-xs font-bold px-4 py-2 rounded-lg hover:bg-indigo-50 transition-colors"
              >
                Open Chat
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>

          {/* Platform info card */}
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="h-4 w-4 text-gray-400" />
              <p className="text-xs font-bold text-gray-500 uppercase tracking-wider">Platform</p>
            </div>
            <ul className="space-y-2.5">
              {[
                { label: 'AI Assistant', status: 'Active' },
                { label: 'Profile Setup', status: onboardingStatus?.onboarding_completed ? 'Complete' : 'Pending' },
              ].map((item) => (
                <li key={item.label} className="flex items-center justify-between text-xs">
                  <span className="text-gray-600 font-medium">{item.label}</span>
                  <span className={`font-semibold px-2 py-0.5 rounded-full ${
                    item.status === 'Active' || item.status === 'Complete'
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'bg-amber-50 text-amber-700'
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
