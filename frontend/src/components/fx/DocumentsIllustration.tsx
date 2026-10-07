/**
 * The app's purpose in one picture: a stack of official documents with
 * bookmark tabs, the line that answers your question highlighted, and a
 * magnifier landing on it. Original artwork; pure SVG, themed by the parent's
 * `color` (ink) plus the brand red and amber. Decorative.
 */
export function DocumentsIllustration({ className = '' }: { className?: string }) {
  const lines = (x: number, y: number, widths: number[], gap = 17) =>
    widths.map((w, i) => <rect key={i} x={x} y={y + i * gap} width={w} height={6} rx={3} fill="currentColor" opacity={0.18} />);

  return (
    <svg viewBox="0 0 520 440" aria-hidden className={`docs-illustration ${className}`} fill="none">
      {/* back pages, fanned */}
      <g transform="rotate(-8 250 230)">
        <rect x="118" y="62" width="250" height="320" rx="10" fill="var(--ill-page-2)" stroke="currentColor" strokeOpacity=".18" strokeWidth="2" />
        <rect x="350" y="112" width="34" height="46" rx="4" fill="var(--amber)" />
      </g>
      <g transform="rotate(5 250 230)">
        <rect x="136" y="52" width="250" height="320" rx="10" fill="var(--ill-page-1)" stroke="currentColor" strokeOpacity=".2" strokeWidth="2" />
        <rect x="370" y="182" width="34" height="46" rx="4" fill="currentColor" opacity=".55" />
      </g>

      {/* front page */}
      <g className="ill-front">
        <rect x="150" y="40" width="252" height="330" rx="10" fill="var(--ill-page-0)" stroke="currentColor" strokeOpacity=".28" strokeWidth="2" />
        {/* bookmark tab */}
        <path d="M352 40h30v58l-15-12-15 12z" fill="var(--red)" />
        {/* heading + paragraphs */}
        <rect x="176" y="70" width="128" height="12" rx="4" fill="currentColor" opacity=".55" />
        {lines(176, 100, [196, 176, 188, 120])}
        {lines(176, 186, [190, 168])}
        {/* the answer line */}
        <rect className="ill-highlight" x="170" y="222" width="190" height="20" rx="4" fill="var(--amber)" opacity=".45" />
        <rect x="176" y="229" width="178" height="6" rx="3" fill="currentColor" opacity=".7" />
        {lines(176, 256, [184, 192, 150, 172])}
        {/* page footer: "p. 12" */}
        <rect x="176" y="340" width="40" height="6" rx="3" fill="currentColor" opacity=".25" />
      </g>

      {/* magnifier over the answer */}
      <g className="ill-lens">
        <circle cx="330" cy="236" r="58" fill="var(--ill-lens)" stroke="currentColor" strokeWidth="7" />
        <clipPath id="ill-lens-clip">
          <circle cx="330" cy="236" r="54" />
        </clipPath>
        <g clipPath="url(#ill-lens-clip)">
          <rect x="262" y="218" width="150" height="34" rx="6" fill="var(--amber)" opacity=".5" />
          <rect x="270" y="229" width="130" height="11" rx="5" fill="currentColor" opacity=".8" />
          <rect x="270" y="268" width="90" height="10" rx="5" fill="currentColor" opacity=".22" />
          <rect x="270" y="194" width="110" height="10" rx="5" fill="currentColor" opacity=".22" />
        </g>
        <path d="M371 279l52 52" stroke="currentColor" strokeWidth="16" strokeLinecap="round" />
        <path d="M371 279l52 52" stroke="var(--red)" strokeWidth="8" strokeLinecap="round" />
      </g>

      {/* the ticket stub the answer comes with */}
      <g className="ill-ticket" transform="rotate(-6 120 330)">
        <rect x="48" y="302" width="150" height="56" rx="6" fill="var(--ill-page-0)" stroke="currentColor" strokeOpacity=".35" strokeWidth="2" />
        <rect x="48" y="302" width="40" height="56" rx="6" fill="currentColor" />
        <text x="68" y="338" textAnchor="middle" fontSize="22" fontWeight="700" fill="var(--ill-page-0)">1</text>
        <path d="M88 306v48" stroke="currentColor" strokeOpacity=".4" strokeWidth="2" strokeDasharray="4 4" />
        <rect x="100" y="318" width="80" height="7" rx="3.5" fill="currentColor" opacity=".55" />
        <rect x="100" y="334" width="40" height="6" rx="3" fill="currentColor" opacity=".25" />
      </g>
    </svg>
  );
}
