import api from '../api';

export interface ProfileResponse {
  email: string;
  full_name: string | null;
  student_status: string | null;
  academic_year: string | null;
  bac_type: string | null;
  bac_score: number | null;
  interests: string[] | null;
  goals: string[] | null;
  enrollment_date: string | null;
  onboarding_completed: boolean;
}

export interface ProfileUpdate {
  full_name?: string;
  student_status?: string;
  interests?: string[];
  goals?: string[];
}

export const profileService = {
  getProfile: async () => {
    const response = await api.get<ProfileResponse>('/profile');
    return response.data;
  },

  updateProfile: async (data: ProfileUpdate) => {
    const response = await api.patch<ProfileResponse>('/profile', data);
    return response.data;
  },

  getOnboardingStatus: async () => {
    const response = await api.get('/profile/onboarding/status');
    return response.data;
  },

  updateAcademicYear: async (academic_year: string) => {
    const response = await api.patch<ProfileResponse>('/profile/academic-year', { academic_year });
    return response.data;
  },
};
