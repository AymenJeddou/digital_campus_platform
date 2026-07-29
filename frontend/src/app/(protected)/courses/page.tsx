'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import {
  BookOpenText, Plus, Trash2, Upload, FileText, MessageSquare, Loader2,
  Link2, RefreshCw, CheckCircle2, AlertCircle, X,
} from 'lucide-react';
import {
  coursesService, EnrolledCourse, CourseDetail, CourseMaterial, ClassroomStatus,
} from '@/lib/services/courses';

function StatusBadge({ status }: { status: CourseMaterial['status'] }) {
  const map = {
    ingested: { icon: CheckCircle2, cls: 'text-emerald-600 bg-emerald-50 dark:bg-emerald-500/10', label: 'Ready' },
    pending: { icon: Loader2, cls: 'text-amber-600 bg-amber-50 dark:bg-amber-500/10', label: 'Processing' },
    error: { icon: AlertCircle, cls: 'text-destructive bg-destructive/10', label: 'Error' },
  }[status];
  const Icon = map.icon;
  return (
    <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-semibold ${map.cls}`}>
      <Icon className={`h-3 w-3 ${status === 'pending' ? 'animate-spin' : ''}`} />
      {map.label}
    </span>
  );
}

export default function CoursesPage() {
  const router = useRouter();
  const [courses, setCourses] = useState<EnrolledCourse[]>([]);
  const [loading, setLoading] = useState(true);
  const [newName, setNewName] = useState('');
  const [adding, setAdding] = useState(false);
  const [selected, setSelected] = useState<CourseDetail | null>(null);
  const [classroom, setClassroom] = useState<ClassroomStatus | null>(null);
  const [syncing, setSyncing] = useState(false);

  const load = async () => {
    try {
      setCourses(await coursesService.listMine());
    } catch {
      toast.error('Failed to load courses');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    coursesService.classroomStatus().then(setClassroom).catch(() => {});
  }, []);

  const addCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    const name = newName.trim();
    if (!name) return;
    setAdding(true);
    try {
      await coursesService.create({ name });
      setNewName('');
      toast.success('Course added');
      load();
    } catch {
      toast.error('Could not add course');
    } finally {
      setAdding(false);
    }
  };

  const openCourse = async (id: string) => {
    try {
      setSelected(await coursesService.getDetail(id));
    } catch {
      toast.error('Could not open course');
    }
  };

  const removeCourse = async (id: string) => {
    try {
      await coursesService.unenroll(id);
      toast.success('Course removed');
      if (selected?.id === id) setSelected(null);
      load();
    } catch {
      toast.error('Could not remove course');
    }
  };

  const connectClassroom = async () => {
    try {
      const { authorization_url } = await coursesService.classroomAuthorize();
      window.location.href = authorization_url;
    } catch {
      toast.error('Google Classroom is not configured');
    }
  };

  const syncClassroom = async () => {
    setSyncing(true);
    try {
      const res = await coursesService.classroomSync();
      toast.success(`Synced ${res.courses_synced} courses, ${res.materials_synced} materials`);
      load();
      coursesService.classroomStatus().then(setClassroom).catch(() => {});
    } catch {
      toast.error('Sync failed — connect Google Classroom first');
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground">My Courses</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Bring in your courses and ask the assistant about their content.
          </p>
        </div>
      </div>

      {/* Google Classroom card */}
      <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Link2 className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-semibold text-foreground">Google Classroom</p>
              <p className="text-xs text-muted-foreground">
                {classroom?.connected
                  ? `Connected${classroom.last_synced_at ? ` · last synced ${new Date(classroom.last_synced_at).toLocaleDateString()}` : ''}`
                  : 'Connect to import your courses automatically.'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {classroom?.connected ? (
              <button
                onClick={syncClassroom}
                disabled={syncing}
                className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
              >
                {syncing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                Sync now
              </button>
            ) : (
              <button
                onClick={connectClassroom}
                className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-secondary/60"
              >
                <Link2 className="h-4 w-4" /> Connect
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Add course */}
      <form onSubmit={addCourse} className="flex items-center gap-3">
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="Add a course by name (e.g. Analyse 1)"
          className="flex-1 rounded-xl border border-border bg-card px-4 py-3 text-sm text-foreground outline-none transition-all placeholder:text-muted-foreground focus:border-primary focus:ring-1 focus:ring-primary"
        />
        <button
          type="submit"
          disabled={adding || !newName.trim()}
          className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
        >
          {adding ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          Add
        </button>
      </form>

      {/* Courses grid */}
      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : courses.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-border py-16 text-center">
          <BookOpenText className="mx-auto h-8 w-8 text-muted-foreground" />
          <p className="mt-3 text-sm font-medium text-foreground">No courses yet</p>
          <p className="text-xs text-muted-foreground">Add one above or connect Google Classroom.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {courses.map((c) => (
            <motion.div
              key={c.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col rounded-2xl border border-border bg-card p-5 shadow-sm"
            >
              <div className="flex items-start justify-between">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <BookOpenText className="h-5 w-5" />
                </div>
                <span className="rounded-md bg-secondary px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                  {c.source === 'google_classroom' ? 'Classroom' : 'Manual'}
                </span>
              </div>
              <p className="mt-4 text-sm font-semibold text-foreground">{c.name}</p>
              <p className="text-xs text-muted-foreground">
                {c.material_count} material{c.material_count === 1 ? '' : 's'}
              </p>
              <div className="mt-4 flex items-center gap-2">
                <button
                  onClick={() => openCourse(c.id)}
                  className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-xs font-medium text-foreground transition-colors hover:bg-secondary/60"
                >
                  Open
                </button>
                <button
                  onClick={() => router.push(`/chat?course=${c.id}&name=${encodeURIComponent(c.name)}`)}
                  title="Ask about this course"
                  className="flex items-center justify-center rounded-lg bg-primary px-3 py-2 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90"
                >
                  <MessageSquare className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => removeCourse(c.id)}
                  title="Remove course"
                  className="flex items-center justify-center rounded-lg border border-border px-3 py-2 text-muted-foreground transition-colors hover:text-destructive"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {selected && (
        <CourseDetailPanel
          detail={selected}
          onClose={() => setSelected(null)}
          onChanged={async () => {
            setSelected(await coursesService.getDetail(selected.id));
            load();
          }}
          onAsk={() => router.push(`/chat?course=${selected.id}&name=${encodeURIComponent(selected.name)}`)}
        />
      )}
    </div>
  );
}

function CourseDetailPanel({
  detail, onClose, onChanged, onAsk,
}: {
  detail: CourseDetail;
  onClose: () => void;
  onChanged: () => void;
  onAsk: () => void;
}) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [busy, setBusy] = useState(false);

  const addText = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    setBusy(true);
    try {
      await coursesService.addMaterial(detail.id, { title: title.trim(), content: content.trim() });
      setTitle(''); setContent('');
      toast.success('Material added');
      onChanged();
    } catch {
      toast.error('Could not add material');
    } finally {
      setBusy(false);
    }
  };

  const upload = async (file: File) => {
    setBusy(true);
    try {
      await coursesService.uploadMaterial(detail.id, file);
      toast.success('File uploaded');
      onChanged();
    } catch {
      toast.error('Upload failed');
    } finally {
      setBusy(false);
    }
  };

  const removeMaterial = async (id: string) => {
    try {
      await coursesService.deleteMaterial(detail.id, id);
      toast.success('Material removed');
      onChanged();
    } catch {
      toast.error('Could not remove material');
    }
  };

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/40" onClick={onClose}>
      <motion.div
        initial={{ x: 40, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        onClick={(e) => e.stopPropagation()}
        className="flex h-full w-full max-w-md flex-col overflow-y-auto border-l border-border bg-background p-6"
      >
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-bold text-foreground">{detail.name}</h2>
            <p className="text-xs text-muted-foreground">{detail.materials.length} materials</p>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-muted-foreground hover:bg-secondary/60">
            <X className="h-5 w-5" />
          </button>
        </div>

        <button
          onClick={onAsk}
          className="mt-4 inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
        >
          <MessageSquare className="h-4 w-4" /> Ask about this course
        </button>

        {/* Materials */}
        <div className="mt-6 space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Materials</p>
          {detail.materials.length === 0 && (
            <p className="text-sm text-muted-foreground">No materials yet. Add text or upload a file below.</p>
          )}
          {detail.materials.map((m) => (
            <div key={m.id} className="flex items-center justify-between rounded-xl border border-border bg-card p-3">
              <div className="flex min-w-0 items-center gap-3">
                <FileText className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-foreground">{m.title}</p>
                  <div className="mt-0.5 flex items-center gap-2">
                    <StatusBadge status={m.status} />
                    {m.status === 'ingested' && (
                      <span className="text-[11px] text-muted-foreground">{m.chunk_count} chunks</span>
                    )}
                  </div>
                </div>
              </div>
              <button
                onClick={() => removeMaterial(m.id)}
                className="flex-shrink-0 rounded-lg p-1.5 text-muted-foreground hover:text-destructive"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>

        {/* Add material */}
        <div className="mt-6 space-y-4 border-t border-border pt-6">
          <label className="flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-dashed border-border py-3 text-sm font-medium text-muted-foreground transition-colors hover:border-primary hover:text-primary">
            <Upload className="h-4 w-4" />
            {busy ? 'Uploading…' : 'Upload a file (PDF, DOCX, PPTX, TXT)'}
            <input
              type="file"
              accept=".pdf,.docx,.pptx,.txt,.md"
              className="hidden"
              disabled={busy}
              onChange={(e) => { const f = e.target.files?.[0]; if (f) upload(f); e.target.value = ''; }}
            />
          </label>

          <form onSubmit={addText} className="space-y-2">
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Material title"
              className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary"
            />
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste notes or course text here…"
              rows={4}
              className="w-full resize-none rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary"
            />
            <button
              type="submit"
              disabled={busy || !title.trim() || !content.trim()}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
            >
              <Plus className="h-4 w-4" /> Add text material
            </button>
          </form>
        </div>
      </motion.div>
    </div>
  );
}
