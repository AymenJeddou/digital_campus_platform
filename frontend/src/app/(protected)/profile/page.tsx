'use client';

import { useEffect, useState } from 'react';
import { profileService, ProfileResponse } from '@/lib/services/profile';
import { toast } from 'sonner';
import { User, BookOpen, Lightbulb, Target, Mail, Save, Lock, Loader2 } from 'lucide-react';
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
    <div className="px-8 py-6 border-b border-border flex items-center gap-5 bg-secondary/20">
      <div className="p-3 bg-primary/10 rounded-xl flex-shrink-0 border border-primary/20">
        <Icon className="h-5 w-5 text-primary" />
      </div>
      <div>
        <h3 className="text-sm font-bold tracking-tight text-foreground">{title}</h3>
        <p className="text-[11px] text-muted-foreground font-medium mt-0.5">{description}</p>
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
    <div className="space-y-2">
      <label htmlFor={id} className="block text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
        {label}
      </label>
      {children}
      {hint && <p className="text-[10px] text-muted-foreground font-medium italic">{hint}</p>}
    </div>
  );
}

const inputClass =
  'w-full px-4 py-3 rounded-xl text-sm font-medium bg-secondary/50 border border-border placeholder:text-muted-foreground/50 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-150';

const disabledInputClass =
  'w-full px-4 py-3 rounded-xl text-sm font-medium bg-secondary/30 border border-border text-muted-foreground/60 cursor-not-allowed opacity-70';

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
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground font-medium">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">

      <div className="grid gap-8 lg:grid-cols-1">
        {/* Account Information */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm"
        >
          <SectionHeader
            icon={User}
            title="Account Information"
            description="Basic details associated with your Digital Campus account."
          />
          <div className="px-8 py-8 grid gap-6 sm:grid-cols-2">
            <FormField id="email" label="Email Address" hint="Your login email cannot be changed.">
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/50" />
                <input
                  id="email"
                  type="email"
                  value={profile?.email || ''}
                  disabled
                  className={`${disabledInputClass} pl-11`}
                />
                <Lock className="absolute right-3.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/30" />
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
          transition={{ duration: 0.3, delay: 0.1 }}
          className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm"
        >
          <SectionHeader
            icon={BookOpen}
            title="Academic Profile"
            description="Your academic details help us tailor the assistant's recommendations."
          />
          <div className="px-8 py-8 space-y-8">
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

            <div className="grid gap-8 sm:grid-cols-2">
              <FormField
                id="interests"
                label="Interests"
                hint="Separate multiple interests with a comma."
              >
                <div className="relative">
                  <Lightbulb className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/50" />
                  <input
                    id="interests"
                    type="text"
                    placeholder="e.g. AI, Web Dev, Design"
                    value={interests}
                    onChange={(e) => setInterests(e.target.value)}
                    className={`${inputClass} pl-11`}
                  />
                </div>
              </FormField>

              <FormField
                id="goals"
                label="Learning Goals"
                hint="Separate multiple goals with a comma."
              >
                <div className="relative">
                  <Target className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/50" />
                  <input
                    id="goals"
                    type="text"
                    placeholder="e.g. Learn React, Graduate"
                    value={goals}
                    onChange={(e) => setGoals(e.target.value)}
                    className={`${inputClass} pl-11`}
                  />
                </div>
              </FormField>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Save row */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3, delay: 0.2 }}
        className="flex items-center justify-between bg-card border border-border rounded-2xl px-8 py-5 shadow-sm"
      >
        <p className="text-xs font-medium text-muted-foreground">Changes are saved to your account immediately.</p>
        <button
          id="save-profile-btn"
          onClick={handleSave}
          disabled={isSaving}
          className="inline-flex items-center gap-2.5 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-bold px-6 py-3 rounded-xl transition-all shadow-sm shadow-primary/20 disabled:opacity-60 disabled:cursor-not-allowed group"
        >
          {isSaving ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Save className="h-4 w-4 transition-transform group-hover:scale-110" />
          )}
          {isSaving ? 'Saving…' : 'Save Changes'}
        </button>
      </motion.div>
    </div>
  );
}
