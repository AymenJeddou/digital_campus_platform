'use client';

import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { api } from './api';
import type { Profile } from './types';

type ProfileState = { profile: Profile | null; refresh: () => Promise<Profile | null> };

const ProfileContext = createContext<ProfileState>({ profile: null, refresh: async () => null });

/** Loads the signed-in profile once for the whole app shell. */
export function ProfileProvider({ children }: { children: React.ReactNode }) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const refresh = useCallback(async () => {
    const p = await api<Profile>('profile');
    setProfile(p);
    return p;
  }, []);
  useEffect(() => {
    api<Profile>('profile').then(setProfile).catch(() => {});
  }, []);
  return <ProfileContext.Provider value={{ profile, refresh }}>{children}</ProfileContext.Provider>;
}

export const useProfile = () => useContext(ProfileContext);
