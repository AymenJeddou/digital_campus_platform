export type Line = 'orientation' | 'academic' | 'administrative' | 'learning';
export const LINES: Line[] = ['orientation', 'academic', 'administrative', 'learning'];

export interface Program {
  id: string;
  name: string;
  level: 'licence' | 'master_recherche' | 'master_pro' | null;
  department: string | null;
}

export interface Profile {
  email: string;
  full_name: string | null;
  role: 'student' | 'admin' | null;
  student_status: 'prospective' | 'enrolled' | 'alumni' | null;
  academic_year: string | null;
  program: { id: string; name: string; level: string | null } | null;
  bac_type: string | null;
  bac_score: number | null;
  interests: string[] | null;
  goals: string[] | null;
  onboarding_completed: boolean;
}

export interface Citation {
  document: string;
  page: number;
}

export interface ChatSession {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  citations: Citation[] | null;
  grounded: boolean | null;
  created_at: string;
  rating: number | null;
  /** client-only: still streaming */
  streaming?: boolean;
}

export interface EnrolledCourse {
  id: string;
  name: string;
  code: string | null;
  description: string | null;
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
  error_message: string | null;
  original_filename: string | null;
  due_at: string | null;
  created_at: string;
}

export interface CourseDetail {
  id: string;
  name: string;
  code: string | null;
  source: string;
  materials: CourseMaterial[];
}

export interface ClassroomStatus {
  connected: boolean;
  last_synced_at: string | null;
  sync_status: 'idle' | 'running' | 'success' | 'error';
  sync_courses_synced: number;
  sync_materials_synced: number;
  sync_materials_failed: number;
  sync_error: string | null;
}

export interface Notification {
  id: string;
  kind: 'deadline' | 'calendar';
  title: string;
  detail: string;
  date: string;
  course_id: string | null;
}

export const PENDING_QUESTION_KEY = 'fsb:pending-question';
