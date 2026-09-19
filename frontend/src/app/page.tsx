'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion, useReducedMotion, type Variants } from 'framer-motion';
import {
  ArrowRight,
  BookOpen,
  FileText,
  Languages,
  MessageSquareText,
  Search,
  Sparkles,
} from 'lucide-react';
import ChatPreview from '@/components/landing/ChatPreview';
import { getToken } from '@/lib/auth';

const features = [
  {
    icon: FileText,
    title: 'Réponses sourcées',
    body: 'Chaque réponse cite les documents officiels de la faculté — jamais d’invention.',
  },
  {
    icon: BookOpen,
    title: 'Tes propres cours',
    body: 'Ajoute tes supports de cours et pose des questions dessus, à toi seul.',
  },
  {
    icon: MessageSquareText,
    title: 'Réponses en direct',
    body: 'Les réponses s’affichent au fur et à mesure, sans attendre.',
  },
  {
    icon: Languages,
    title: 'Multilingue',
    body: 'Pose tes questions en français, en arabe ou en anglais.',
  },
];

const steps = [
  {
    icon: MessageSquareText,
    title: 'Pose ta question',
    body: 'Admissions, cours, calendrier, prérequis — demande simplement.',
  },
  {
    icon: Search,
    title: 'Recherche dans les documents officiels',
    body: 'L’assistant parcourt les guides et supports validés de la FSB.',
  },
  {
    icon: FileText,
    title: 'Réponse citée',
    body: 'Tu obtiens une réponse claire avec les sources exactes.',
  },
];

export default function LandingPage() {
  const reduce = useReducedMotion();
  const [hasToken, setHasToken] = useState(false);

  useEffect(() => {
    setHasToken(!!getToken());
  }, []);

  const fadeUp: Variants = {
    hidden: { opacity: 0, y: reduce ? 0 : 24 },
    show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.23, 1, 0.32, 1] } },
  };

  const stagger: Variants = {
    hidden: {},
    show: { transition: { staggerChildren: 0.12 } },
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* ---- Top nav ---- */}
      <header className="sticky top-0 z-30 border-b border-border/70 bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sidebar text-sm font-bold text-white">
              DC
            </div>
            <div className="leading-tight">
              <p className="text-sm font-semibold">Digital Campus</p>
              <p className="text-xs text-muted-foreground">Faculté des Sciences de Bizerte</p>
            </div>
          </div>

          <nav className="flex items-center gap-2 sm:gap-3">
            {hasToken ? (
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-transform hover:scale-[1.03]"
              >
                Aller au tableau de bord
                <ArrowRight className="h-4 w-4" />
              </Link>
            ) : (
              <>
                <Link
                  href="/login"
                  className="rounded-full px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-secondary"
                >
                  Se connecter
                </Link>
                <Link
                  href="/register"
                  className="inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-transform hover:scale-[1.03]"
                >
                  Commencer
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      {/* ---- Hero ---- */}
      <section className="relative overflow-hidden">
        {/* Decorative blurred blobs */}
        <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute -left-24 top-0 h-72 w-72 rounded-full bg-primary/20 blur-3xl" />
          <div className="absolute right-0 top-40 h-80 w-80 rounded-full bg-sidebar/10 blur-3xl dark:bg-primary/10" />
        </div>

        <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:py-24">
          <motion.div variants={stagger} initial="hidden" animate="show">
            <motion.span
              variants={fadeUp}
              className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-medium text-primary"
            >
              <Sparkles className="h-3.5 w-3.5" />
              Assistant IA de la FSB
            </motion.span>

            <motion.h1
              variants={fadeUp}
              className="mt-5 text-4xl font-bold leading-tight tracking-tight sm:text-5xl"
            >
              Tes réponses académiques,{' '}
              <span className="text-primary">sourcées et fiables.</span>
            </motion.h1>

            <motion.p
              variants={fadeUp}
              className="mt-5 max-w-lg text-lg text-muted-foreground"
            >
              Un assistant intelligent qui répond à tes questions sur les admissions, les cours et la
              vie à la Faculté des Sciences de Bizerte — toujours avec les documents officiels à
              l’appui.
            </motion.p>

            <motion.div variants={fadeUp} className="mt-8 flex flex-wrap items-center gap-3">
              <Link
                href={hasToken ? '/dashboard' : '/register'}
                className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition-transform hover:scale-[1.03]"
              >
                {hasToken ? 'Aller au tableau de bord' : 'Commencer'}
                <ArrowRight className="h-4 w-4" />
              </Link>
              {!hasToken && (
                <Link
                  href="/login"
                  className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-6 py-3 text-sm font-semibold text-foreground transition-colors hover:bg-secondary"
                >
                  Se connecter
                </Link>
              )}
            </motion.div>
          </motion.div>

          <motion.div
            className="flex justify-center lg:justify-end"
            initial={reduce ? false : { opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, ease: [0.23, 1, 0.32, 1], delay: 0.2 }}
          >
            <ChatPreview />
          </motion.div>
        </div>
      </section>

      {/* ---- Feature grid ---- */}
      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.3 }}
          className="mx-auto max-w-2xl text-center"
        >
          <h2 className="text-3xl font-bold tracking-tight">Pensé pour les étudiants</h2>
          <p className="mt-3 text-muted-foreground">
            Des réponses honnêtes, ancrées dans les vraies ressources de la faculté.
          </p>
        </motion.div>

        <motion.div
          variants={stagger}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.2 }}
          className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4"
        >
          {features.map((f) => (
            <motion.div
              key={f.title}
              variants={fadeUp}
              className="rounded-2xl border border-border bg-card p-6 transition-shadow hover:shadow-lg hover:shadow-primary/5"
            >
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <f.icon className="h-5 w-5" />
              </span>
              <h3 className="mt-4 text-base font-semibold">{f.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{f.body}</p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ---- How it works ---- */}
      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.3 }}
          className="mx-auto max-w-2xl text-center"
        >
          <h2 className="text-3xl font-bold tracking-tight">Comment ça marche</h2>
          <p className="mt-3 text-muted-foreground">Trois étapes, de la question à la réponse citée.</p>
        </motion.div>

        <motion.div
          variants={stagger}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.2 }}
          className="mt-12 grid gap-6 md:grid-cols-3"
        >
          {steps.map((s, i) => (
            <motion.div key={s.title} variants={fadeUp} className="relative">
              <div className="rounded-2xl border border-border bg-card p-6">
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground">
                    {i + 1}
                  </span>
                  <s.icon className="h-5 w-5 text-primary" />
                </div>
                <h3 className="mt-4 text-base font-semibold">{s.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{s.body}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ---- CTA band ---- */}
      <section className="mx-auto max-w-6xl px-4 pb-20 sm:px-6">
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.4 }}
          className="overflow-hidden rounded-3xl bg-sidebar px-8 py-14 text-center"
        >
          <h2 className="text-3xl font-bold tracking-tight text-white">
            Prêt à poser ta première question ?
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-slate-300">
            Crée ton compte et commence à explorer la Faculté des Sciences de Bizerte avec un
            assistant qui cite ses sources.
          </p>
          <Link
            href={hasToken ? '/dashboard' : '/register'}
            className="mt-8 inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/30 transition-transform hover:scale-[1.03]"
          >
            {hasToken ? 'Aller au tableau de bord' : 'Commencer gratuitement'}
            <ArrowRight className="h-4 w-4" />
          </Link>
        </motion.div>
      </section>

      {/* ---- Footer ---- */}
      <footer className="border-t border-border/70">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 py-8 sm:flex-row sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sidebar text-xs font-bold text-white">
              DC
            </div>
            <p className="text-sm text-muted-foreground">
              Digital Campus — Faculté des Sciences de Bizerte
            </p>
          </div>
          <div className="flex items-center gap-5 text-sm text-muted-foreground">
            <Link href="/login" className="transition-colors hover:text-foreground">
              Se connecter
            </Link>
            <Link href="/register" className="transition-colors hover:text-foreground">
              Créer un compte
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
