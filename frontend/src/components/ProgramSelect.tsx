'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useT } from '@/lib/i18n';
import type { Program } from '@/lib/types';
import { inputClass } from './ui';

const LEVEL_LABEL = { licence: 'Licence', master_recherche: 'Mastère de recherche', master_pro: 'Mastère professionnel' };

/** FSB programmes grouped by department, as a native select. */
export function ProgramSelect({ id, value, onChange }: { id: string; value: string; onChange: (id: string) => void }) {
  const t = useT();
  const [programs, setPrograms] = useState<Program[]>([]);
  useEffect(() => {
    api<Program[]>('programs').then(setPrograms).catch(() => {});
  }, []);

  const departments = [...new Set(programs.map((p) => p.department ?? ''))];
  return (
    <select id={id} value={value} onChange={(e) => onChange(e.target.value)} className={inputClass}>
      <option value="">{t.onboarding.programNone}</option>
      {departments.map((dept) => (
        <optgroup key={dept} label={dept}>
          {programs
            .filter((p) => (p.department ?? '') === dept)
            .map((p) => (
              <option key={p.id} value={p.id}>
                {p.level ? `${LEVEL_LABEL[p.level]} · ` : ''}
                {p.name}
              </option>
            ))}
        </optgroup>
      ))}
    </select>
  );
}

/** "data, robotique" -> ["data", "robotique"] */
export const splitTags = (text: string) =>
  text
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
    .slice(0, 15);
