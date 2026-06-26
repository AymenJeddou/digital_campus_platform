'use client';

import { useEffect, useState } from 'react';
import { profileService, ProfileResponse } from '@/lib/services/profile';
import { toast } from 'sonner';
import { User, BookOpen, Lightbulb, Target, Mail, Save, Lock } from 'lucide-react';
import { motion } from 'framer-motion';

function SectionHeader({
  icon: Icon,
  title,
  description,
}: {
  icon: React.ElementType;
  title: string;
  description: string;
}) {
  return (
    <div className="px-6 py-5 border-b border-gray-100 flex items-center gap-4">
      <div className="p-2 bg-indigo-50 rounded-lg flex-shrink-0">
        <Icon className="h-4 w-4 text-indigo-600" />
      </div>
      <div>
        <h3 className="text-sm font-bold text-gray-900">{title}</h3>
        <p className="text-xs text-gray-400 mt-0.5">{description}</p>
      </div>
    </div>
  );
}

function FormField({
  id,
  label,
  hint,
  children,
}: {
  id: string;
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-xs font-semibold text-gray-700 mb-1.5 uppercase tracking-wide">
        {label}
      </label>
      {children}
      {hint && <p className="mt-1.5 text-xs text-gray-400">{hint}</p>}
    </div>
  );
}

const inputClass =
  'w-full px-4 py-3 rounded-lg text-sm font-medium bg-gray-50 border border-gray-200 placeholder-gray-400 text-gray-900 focus:outline-none focus:border-indigo-400 focus:bg-white focus:ring-2 focus:ring-indigo-500/10 transition-all duration-150';

const disabledInputClass =
  'w-full px-4 py-3 rounded-lg text-sm font-medium bg-gray-100 border border-gray-200 text-gray-400 cursor-not-allowed';

export default function ProfilePage() {
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [fullName, setFullName] = useState('');
  const [academicYear, setAcademicYear] = useState('');
  const [interests, setInterests] = useState('');
  const [goals, setGoals] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await profileService.getProfile();
        setProfile(data);
        setFullName(data.full_name || '');
        setAcademicYear(data.academic_year || '');
        setInterests(data.interests?.join(', ') || '');
        setGoals(data.goals?.join(', ') || '');
      } catch {
        toast.error('Failed to load profile');
      } finally {
        setIsLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await profileService.updateProfile({
        full_name: fullName,
        interests: interests.split(',').map((i) => i.trim()).filter(Boolean),
        goals: goals.split(',').map((i) => i.trim()).filter(Boolean),
      });
      if (academicYear !== profile?.academic_year) {
        await profileService.updateAcademicYear(academicYear);
      }
      toast.success('Profile updated successfully');
    } catch {
      toast.error('Failed to update profile');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 border-2 border-gray-200 border-t-indigo-600 rounded-full animate-spin" />
          <p className="text-sm text-gray-400 font-medium">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-5">

      {/* Account Information */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        className="bg-white border border-gray-200 rounded-xl overflow-hidden"
      >
        <SectionHeader
          icon={User}
          title="Account Information"
          description="Basic details associated with your Digital Campus account."
        />
        <div className="px-6 py-5 space-y-4">
          <FormField id="email" label="Email Address" hint="Your login email cannot be changed.">
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                id="email"
                type="email"
                value={profile?.email || ''}
                disabled
                className={`${disabledInputClass} pl-10`}
              />
              <Lock className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-300" />
            </div>
          </FormField>

          <FormField id="fullName" label="Full Name">
            <input
              id="fullName"
              type="text"
              placeholder="e.g. Jane Doe"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className={inputClass}
            />
          </FormField>
        </div>
      </motion.div>

      {/* Academic Profile */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, delay: 0.08 }}
        className="bg-white border border-gray-200 rounded-xl overflow-hidden"
      >
        <SectionHeader
          icon={BookOpen}
          title="Academic Profile"
          description="Your academic details help us tailor the assistant's recommendations."
        />
        <div className="px-6 py-5 space-y-4">
          <FormField id="academicYear" label="Academic Year">
            <input
              id="academicYear"
              type="text"
              placeholder="e.g. Sophomore, Year 2, Master's 1st Year"
              value={academicYear}
              onChange={(e) => setAcademicYear(e.target.value)}
              className={inputClass}
            />
          </FormField>

          <FormField
            id="interests"
            label="Interests"
            hint="Separate multiple interests with a comma."
          >
            <div className="relative">
              <Lightbulb className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                id="interests"
                type="text"
                placeholder="e.g. Machine Learning, Web Development, Design"
                value={interests}
                onChange={(e) => setInterests(e.target.value)}
                className={`${inputClass} pl-10`}
              />
            </div>
          </FormField>

          <FormField
            id="goals"
            label="Learning Goals"
            hint="Separate multiple goals with a comma."
          >
            <div className="relative">
              <Target className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                id="goals"
                type="text"
                placeholder="e.g. Learn React, Build a startup, Graduate with honors"
                value={goals}
                onChange={(e) => setGoals(e.target.value)}
                className={`${inputClass} pl-10`}
              />
            </div>
          </FormField>
        </div>
      </motion.div>

      {/* Save row */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.25, delay: 0.15 }}
        className="flex items-center justify-between bg-white border border-gray-200 rounded-xl px-6 py-4"
      >
        <p className="text-xs text-gray-400">Changes are saved to your account immediately.</p>
        <button
          id="save-profile-btn"
          onClick={handleSave}
          disabled={isSaving}
          className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors duration-150 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <Save className="h-4 w-4" />
          {isSaving ? 'Saving…' : 'Save Changes'}
        </button>
      </motion.div>
    </div>
  );
}
