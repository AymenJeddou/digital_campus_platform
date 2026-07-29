import {
  ArrowUpRight,
  Bot,
  BookOpenText,
  Bell,
  ChevronRight,
  Clock3,
  Download,
  FileText,
  GraduationCap,
  Layers3,
  Sparkles,
  Upload,
  ChartColumnIncreasing,
  CheckCircle2,
} from 'lucide-react';

const stats = [
  { label: 'Enrolled Courses', value: '8', detail: '2 advanced modules added', icon: BookOpenText },
  { label: 'Credits Earned', value: '52', detail: '12 credits from core studies', icon: ChartColumnIncreasing },
  { label: 'GPA', value: '3.87', detail: 'Above faculty benchmark', icon: Sparkles },
  { label: 'Onboarding', value: '92%', detail: '1 checklist item remaining', icon: CheckCircle2 },
];

const highlights = [
  {
    title: 'Faculty of Digital Systems',
    description: 'A structured path through analytics, product thinking, and applied AI.',
    metricLabel: 'Attendance',
    metricValue: '96%',
    accent: '#2563eb',
    imageLabel: 'Digital Systems',
  },
  {
    title: 'Applied Intelligence Track',
    description: 'Focused study blocks with project reviews and guided lab sessions.',
    metricLabel: 'Attendance',
    metricValue: '94%',
    accent: '#1d4ed8',
    imageLabel: 'Applied AI',
  },
];

const citations = ['Course Policy A-12', 'Module Plan 2026', 'Attendance Log Q2'];

const documents = [
  { title: 'Updated enrollment letter', detail: 'PDF · received 2 hours ago', state: 'Ready for review' },
  { title: 'Course plan summary', detail: 'DOCX · synced from academic office', state: 'Published' },
  { title: 'Onboarding checklist', detail: 'PDF · last edited yesterday', state: 'In progress' },
];

const activity = [
  {
    title: 'AI assistant generated a course recommendation',
    detail: 'Based on attendance, credit load, and prior module results.',
    time: '10 min ago',
    icon: Bot,
  },
  {
    title: 'Transcript request approved',
    detail: 'Student records office confirmed the latest revision.',
    time: '1 hour ago',
    icon: FileText,
  },
  {
    title: 'Program milestone completed',
    detail: 'You reached 92% onboarding completion.',
    time: 'Today',
    icon: CheckCircle2,
  },
];

function buildIllustration(accent: string, variant: 1 | 2) {
  const svg =
    variant === 1
      ? `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400" fill="none">
          <rect width="640" height="400" rx="32" fill="#eff6ff"/>
          <rect x="48" y="46" width="544" height="308" rx="28" fill="#ffffff" opacity="0.82"/>
          <path d="M96 278C164 230 224 248 280 214C339 178 392 118 504 120" stroke="${accent}" stroke-width="16" stroke-linecap="round" opacity="0.92"/>
          <path d="M132 136H278" stroke="#93c5fd" stroke-width="20" stroke-linecap="round"/>
          <path d="M132 176H244" stroke="#bfdbfe" stroke-width="16" stroke-linecap="round"/>
          <path d="M132 214H220" stroke="#dbeafe" stroke-width="16" stroke-linecap="round"/>
          <circle cx="486" cy="146" r="52" fill="${accent}" opacity="0.14"/>
          <circle cx="498" cy="146" r="26" fill="${accent}" opacity="0.28"/>
          <rect x="388" y="232" width="150" height="74" rx="22" fill="#dbeafe"/>
          <rect x="410" y="254" width="106" height="12" rx="6" fill="#2563eb" opacity="0.75"/>
          <rect x="410" y="276" width="72" height="12" rx="6" fill="#93c5fd"/>
        </svg>`
      : `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400" fill="none">
          <rect width="640" height="400" rx="32" fill="#eff6ff"/>
          <rect x="56" y="54" width="528" height="292" rx="30" fill="#ffffff" opacity="0.86"/>
          <rect x="110" y="108" width="210" height="172" rx="28" fill="#dbeafe"/>
          <path d="M150 190L214 144L268 176L320 126" stroke="${accent}" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="380" cy="170" r="58" fill="${accent}" opacity="0.16"/>
          <circle cx="380" cy="170" r="22" fill="${accent}" opacity="0.34"/>
          <path d="M404 244H516" stroke="#93c5fd" stroke-width="16" stroke-linecap="round"/>
          <path d="M404 278H486" stroke="#bfdbfe" stroke-width="16" stroke-linecap="round"/>
          <path d="M404 312H456" stroke="#dbeafe" stroke-width="16" stroke-linecap="round"/>
        </svg>`;

  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

export default function DashboardPage() {
  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
      <div className="space-y-6">
        <section className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-[0_24px_55px_rgba(15,23,42,0.07)]">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-2xl space-y-4">
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#1d4ed8]">
                Personalized Overview
              </p>
              <h2 className="text-3xl font-semibold tracking-tight text-[#0f172a] sm:text-4xl">
                Good morning, Amina. Your campus workspace is in steady shape.
              </h2>
              <p className="max-w-2xl text-base leading-7 text-slate-600">
                Track your academic progress, review the assistant’s recommendations, and keep
                document requests moving without leaving the dashboard.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:min-w-[320px] lg:grid-cols-1">
              <div className="rounded-2xl border border-slate-200 bg-[var(--background)] px-4 py-3">
                <p className="text-sm text-slate-500">Current term</p>
                <p className="mt-1 text-lg font-semibold text-[#0f172a]">Spring 2026</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-[var(--background)] px-4 py-3">
                <p className="text-sm text-slate-500">Next review</p>
                <p className="mt-1 text-lg font-semibold text-[#0f172a]">Thursday, 10:30 AM</p>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {stats.map(({ label, value, detail, icon: Icon }) => (
            <article
              key={label}
              className="rounded-3xl border border-slate-200/80 bg-white p-5 shadow-[0_18px_40px_rgba(15,23,42,0.06)]"
            >
              <div className="flex items-center justify-between">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#eff6ff] text-[#2563eb]">
                  <Icon className="h-5 w-5" />
                </div>
                <span className="rounded-full bg-[#eff6ff] px-3 py-1 text-xs font-semibold text-[#1d4ed8]">
                  Live
                </span>
              </div>
              <p className="mt-5 text-sm font-medium text-slate-500">{label}</p>
              <p className="mt-2 text-3xl font-semibold tracking-tight text-[#0f172a]">{value}</p>
              <p className="mt-2 text-sm leading-6 text-slate-500">{detail}</p>
            </article>
          ))}
        </section>

        <section className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-[0_24px_55px_rgba(15,23,42,0.07)]">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#1d4ed8]">
                AI Assistant Snapshot
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[#0f172a]">
                Guided support for course planning and compliance questions
              </h2>
            </div>
            <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-[#eff6ff] px-4 py-2 text-sm font-medium text-[#1d4ed8]">
              <Sparkles className="h-4 w-4" />
              97% answer confidence
            </div>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_280px]">
            <div className="space-y-4 rounded-3xl border border-slate-200 bg-[#eff6ff] p-5">
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-[#2563eb] shadow-sm">
                  <Bot className="h-5 w-5" />
                </div>
                <div className="rounded-2xl rounded-tl-md bg-white px-4 py-3 shadow-sm">
                  <p className="text-sm leading-6 text-slate-700">
                    You are clear to continue the Applied Intelligence track. The assistant
                    recommends completing the research methods module before Thursday’s review.
                  </p>
                </div>
              </div>

              <div className="ml-12 flex items-start gap-3">
                <div className="rounded-2xl rounded-tl-md bg-[#dbeafe] px-4 py-3 shadow-sm">
                  <p className="text-sm leading-6 text-[#0f172a]">
                    That recommendation aligns with your attendance pattern and the latest
                    course policy update.
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 p-5">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-[#0f172a]">Citation chips</p>
                <ChevronRight className="h-4 w-4 text-slate-400" />
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {citations.map((citation) => (
                  <span
                    key={citation}
                    className="rounded-full border border-slate-200 bg-[#eff6ff] px-3 py-2 text-xs font-medium text-[#1d4ed8]"
                  >
                    {citation}
                  </span>
                ))}
              </div>
              <div className="mt-6 rounded-2xl bg-[#0f172a] p-4 text-white">
                <p className="text-sm text-slate-300">Recommended follow-up</p>
                <p className="mt-2 text-lg font-semibold leading-7">
                  Review the research methods outline and upload the missing reflection note.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-5 md:grid-cols-2">
          {highlights.map((card, index) => (
            <article
              key={card.title}
              className="overflow-hidden rounded-3xl border border-slate-200/80 bg-white shadow-[0_24px_55px_rgba(15,23,42,0.07)]"
            >
              <img
                src={buildIllustration(card.accent, index === 0 ? 1 : 2)}
                alt={card.imageLabel}
                className="h-48 w-full object-cover"
              />
              <div className="space-y-4 p-5">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-xl font-semibold tracking-tight text-[#0f172a]">
                      {card.title}
                    </h3>
                    <p className="mt-2 text-sm leading-6 text-slate-600">{card.description}</p>
                  </div>
                  <span className="rounded-full bg-[#eff6ff] px-3 py-1 text-xs font-semibold text-[#1d4ed8]">
                    Active
                  </span>
                </div>

                <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-[#eff6ff] px-4 py-3">
                  <div>
                    <p className="text-sm text-slate-500">{card.metricLabel}</p>
                    <p className="text-lg font-semibold text-[#0f172a]">{card.metricValue}</p>
                  </div>
                  <div className="flex items-center gap-2 text-sm font-medium text-[#1d4ed8]">
                    <Layers3 className="h-4 w-4" />
                    Structured schedule
                  </div>
                </div>
              </div>
            </article>
          ))}
        </section>

        <section className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-[0_24px_55px_rgba(15,23,42,0.07)]">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#1d4ed8]">
                Recent Documents
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[#0f172a]">
                Files ready for review and upload
              </h2>
            </div>

            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-full bg-[#2563eb] px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-500/20 transition-colors hover:bg-[#1d4ed8]"
            >
              <Upload className="h-4 w-4" />
              Upload document
            </button>
          </div>

          <div className="mt-6 space-y-3">
            {documents.map((document) => (
              <article
                key={document.title}
                className="flex items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-[#eff6ff] px-4 py-4"
              >
                <div className="flex min-w-0 items-center gap-4">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-[#2563eb] shadow-sm">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-[#0f172a]">{document.title}</p>
                    <p className="truncate text-sm text-slate-500">{document.detail}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-[#1d4ed8]">
                    {document.state}
                  </span>
                  <button
                    type="button"
                    className="flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 transition-colors hover:border-blue-200 hover:text-[#1d4ed8]"
                    aria-label={`Download ${document.title}`}
                  >
                    <Download className="h-4 w-4" />
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>

      <div className="space-y-6 xl:sticky xl:top-24 xl:self-start">
        <section className="rounded-3xl bg-[#0f172a] p-6 text-white shadow-[0_26px_60px_rgba(15,23,42,0.28)]">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-400">
                Recommendation
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight">
                Focus on the research methods module
              </h2>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 text-[#93c5fd]">
              <ArrowUpRight className="h-5 w-5" />
            </div>
          </div>

          <div className="mt-6 space-y-4 rounded-3xl border border-white/10 bg-white/5 p-4">
            <div className="flex items-start gap-3">
              <div className="mt-0.5 h-2.5 w-2.5 rounded-full bg-[#60a5fa]" />
              <div>
                <p className="font-medium text-white">Highest impact task</p>
                <p className="mt-1 text-sm leading-6 text-slate-300">
                  Finish the module outline before your Thursday review so the assistant can
                  confirm the next step.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="mt-0.5 h-2.5 w-2.5 rounded-full bg-[#93c5fd]" />
              <div>
                <p className="font-medium text-white">Why it matters</p>
                <p className="mt-1 text-sm leading-6 text-slate-300">
                  It keeps your credits, attendance, and onboarding checklist aligned.
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 rounded-3xl border border-white/10 bg-white/5 p-4">
            <div className="flex items-center justify-between text-sm text-slate-300">
              <span>Readiness score</span>
              <span>91/100</span>
            </div>
            <div className="mt-3 h-2 rounded-full bg-white/10">
              <div className="h-2 w-[91%] rounded-full bg-[#2563eb]" />
            </div>
          </div>
        </section>

        <section className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-[0_24px_55px_rgba(15,23,42,0.07)]">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#1d4ed8]">
                Recent Activity
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[#0f172a]">
                Latest campus updates
              </h2>
            </div>
            <Clock3 className="h-5 w-5 text-slate-400" />
          </div>

          <div className="mt-6 space-y-4">
            {activity.map(({ title, detail, time, icon: Icon }) => (
              <article key={title} className="flex gap-4 rounded-2xl bg-[#eff6ff] p-4">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-[#2563eb] shadow-sm">
                  <Icon className="h-5 w-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-medium leading-6 text-[#0f172a]">{title}</p>
                    <span className="shrink-0 text-xs font-medium text-slate-500">{time}</span>
                  </div>
                  <p className="mt-1 text-sm leading-6 text-slate-500">{detail}</p>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
