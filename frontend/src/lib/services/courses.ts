import api from '../api';

export interface Course {
  id: string;
  name: string;
  code?: string | null;
  description?: string | null;
  program_id?: string | null;
}

export interface EnrolledCourse extends Course {
  enrolled_at: string;
  source: 'manual' | 'google_classroom';
  material_count: number;
}

export interface CourseMaterial {
  id: string;
  course_id: string;
  title: string;
  source: 'manual' | 'upload' | 'google_classroom';
  status: 'pending' | 'ingested' | 'error';
  chunk_count: number;
  error_message?: string | null;
  original_filename?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CourseDetail extends Course {
  materials: CourseMaterial[];
}

export interface ClassroomStatus {
  connected: boolean;
  connected_at?: string | null;
  last_synced_at?: string | null;
}

export interface ClassroomSyncResult {
  courses_synced: number;
  materials_synced: number;
}

export const coursesService = {
  listMine: async () => (await api.get<EnrolledCourse[]>('/courses/mine')).data,

  /** Create a course (by name) and enrol the current student in one step. */
  create: async (data: { name: string; code?: string; description?: string }) =>
    (await api.post<EnrolledCourse>('/courses', data)).data,

  unenroll: async (courseId: string) => {
    await api.delete(`/courses/enroll/${courseId}`);
  },

  getDetail: async (courseId: string) =>
    (await api.get<CourseDetail>(`/courses/${courseId}`)).data,

  addMaterial: async (courseId: string, data: { title: string; content: string }) =>
    (await api.post<CourseMaterial>(`/courses/${courseId}/materials`, data)).data,

  uploadMaterial: async (courseId: string, file: File, title?: string) => {
    const form = new FormData();
    form.append('file', file);
    if (title) form.append('title', title);
    return (
      await api.post<CourseMaterial>(`/courses/${courseId}/materials/upload`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    ).data;
  },

  deleteMaterial: async (courseId: string, materialId: string) => {
    await api.delete(`/courses/${courseId}/materials/${materialId}`);
  },

  // --- Google Classroom ---
  classroomStatus: async () =>
    (await api.get<ClassroomStatus>('/courses/classroom/status')).data,

  classroomAuthorize: async () =>
    (await api.post<{ authorization_url: string }>('/courses/classroom/authorize')).data,

  classroomSync: async () =>
    (await api.post<ClassroomSyncResult>('/courses/classroom/sync')).data,
};
