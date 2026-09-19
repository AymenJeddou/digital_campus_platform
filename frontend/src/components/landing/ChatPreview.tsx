'use client';

import { motion, useReducedMotion } from 'framer-motion';
import { FileText, Sparkles } from 'lucide-react';

// A mock chat card that "streams" a cited answer — purely decorative, no network.
// Reuses the citation-chip look from the real chat page so the hero previews the product.
const answer =
  "Pour la Licence en Informatique de Gestion, il faut un score au bac d'au moins 120, " +
  'avec une priorité aux sections Mathématiques et Sciences expérimentales.';

const citations = [
  { document: 'Guide des études 2025', page: 12 },
  { document: 'Conditions d’admission', page: 3 },
];

export default function ChatPreview() {
  const reduce = useReducedMotion();

  // Reveal the answer word-by-word for a lightweight "streaming" feel.
  const words = answer.split(' ');

  return (
    <div className="relative w-full max-w-md">
      {/* Soft glow behind the card */}
      <div
        aria-hidden
        className="absolute -inset-6 -z-10 rounded-[2rem] bg-primary/20 blur-3xl"
      />

      <div className="rounded-3xl border border-border bg-card/90 p-5 shadow-2xl shadow-primary/10 backdrop-blur">
        <div className="flex items-center gap-2 border-b border-border pb-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <Sparkles className="h-4 w-4" />
          </span>
          <div>
            <p className="text-sm font-semibold text-card-foreground">Assistant FSB</p>
            <p className="text-xs text-muted-foreground">En ligne</p>
          </div>
        </div>

        {/* User bubble */}
        <div className="mt-4 flex justify-end">
          <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-primary px-4 py-2 text-sm text-primary-foreground">
            Quelles sont les conditions pour la Licence en Informatique de Gestion ?
          </div>
        </div>

        {/* Assistant bubble — streamed */}
        <div className="mt-3 flex justify-start">
          <div className="max-w-[92%] rounded-2xl rounded-bl-sm bg-secondary px-4 py-3 text-sm leading-relaxed text-secondary-foreground">
            <span>
              {words.map((word, i) => (
                <motion.span
                  key={i}
                  initial={reduce ? false : { opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: reduce ? 0 : 0.6 + i * 0.06, duration: 0.2 }}
                >
                  {word}{' '}
                </motion.span>
              ))}
              {!reduce && (
                <motion.span
                  aria-hidden
                  className="inline-block h-4 w-[2px] translate-y-[2px] bg-primary"
                  animate={{ opacity: [1, 0, 1] }}
                  transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
                />
              )}
            </span>

            {/* Citation chips */}
            <motion.div
              className="mt-3 flex flex-wrap gap-2"
              initial={reduce ? false : { opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: reduce ? 0 : 0.6 + words.length * 0.06 + 0.3, duration: 0.3 }}
            >
              {citations.map((c) => (
                <span
                  key={c.document}
                  className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-2.5 py-1 text-xs font-medium text-primary"
                >
                  <FileText className="h-3 w-3" />
                  {c.document} · p.{c.page}
                </span>
              ))}
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}
