import { useMemo } from "react";

/**
 * Cinematic, travel-themed backdrop: deep gradient, a slowly-rotating dotted
 * globe, glowing flight arcs with comet trails, pulsing pins and ambient glows.
 * Subtle by design so foreground text/cards stay readable. Theme-aware.
 */

const VB_W = 1440;
const VB_H = 900;
const CX = 1140;
const CY = 360;
const R = 440;

const PINS = [
  { x: 250, y: 300 }, { x: 470, y: 560 }, { x: 720, y: 230 },
  { x: 1000, y: 600 }, { x: 1240, y: 330 }, { x: 620, y: 720 },
  { x: 920, y: 330 },
];
const ARC_PAIRS: [number, number][] = [
  [0, 2], [2, 4], [1, 3], [5, 3], [0, 1], [6, 4],
];

function arcPath(a: { x: number; y: number }, b: { x: number; y: number }) {
  const mx = (a.x + b.x) / 2;
  const my = (a.y + b.y) / 2 - Math.hypot(b.x - a.x, b.y - a.y) * 0.3;
  return `M ${a.x} ${a.y} Q ${mx} ${my} ${b.x} ${b.y}`;
}

export default function Background({ dark }: { dark: boolean }) {
  const dots = useMemo(() => {
    const N = 460;
    const out: { x: number; y: number; z: number }[] = [];
    for (let i = 0; i < N; i++) {
      const y = 1 - (i / (N - 1)) * 2;
      const r = Math.sqrt(Math.max(0, 1 - y * y));
      const theta = i * 2.399963; // golden angle
      out.push({ x: Math.cos(theta) * r, y, z: Math.sin(theta) * r });
    }
    return out;
  }, []);

  const dotColor = dark ? "96, 165, 250" : "100, 116, 139";
  const arcA = dark ? "#38bdf8" : "#60a5fa";
  const arcB = dark ? "#818cf8" : "#93c5fd";
  const pinColor = dark ? "#22d3ee" : "#3b82f6";
  const base = dark
    ? "radial-gradient(1100px 620px at 72% -12%, rgba(37,99,235,0.20), transparent 60%)," +
      "radial-gradient(900px 700px at 8% 112%, rgba(56,189,248,0.10), transparent 60%)," +
      "linear-gradient(160deg, #05070a 0%, #0a0f17 55%, #0d141d 100%)"
    : "radial-gradient(1000px 600px at 80% -10%, rgba(59,130,246,0.12), transparent 60%)," +
      "radial-gradient(800px 640px at 0% 110%, rgba(56,189,248,0.08), transparent 60%)," +
      "linear-gradient(160deg, #f8fafc 0%, #eef2f7 100%)";

  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden" style={{ background: base }}>
      <svg
        className="h-full w-full"
        viewBox={`0 0 ${VB_W} ${VB_H}`}
        preserveAspectRatio="xMidYMid slice"
        aria-hidden="true"
      >
        <defs>
          <filter id="vm-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          {ARC_PAIRS.map(([i, j], k) => (
            <linearGradient id={`vm-arc-${k}`} key={k} gradientUnits="userSpaceOnUse"
              x1={PINS[i].x} y1={PINS[i].y} x2={PINS[j].x} y2={PINS[j].y}>
              <stop offset="0" stopColor={arcA} stopOpacity="0" />
              <stop offset="0.5" stopColor={arcA} stopOpacity={dark ? 0.55 : 0.4} />
              <stop offset="1" stopColor={arcB} stopOpacity="0" />
            </linearGradient>
          ))}
        </defs>

        {/* dotted globe */}
        <g className="vm-globe" opacity={dark ? 0.55 : 0.4}>
          {dots.map((d, i) => (
            <circle
              key={i}
              cx={CX + d.x * R}
              cy={CY - d.y * R}
              r={d.z > 0 ? 1.5 : 1}
              fill={`rgba(${dotColor}, ${(0.12 + ((d.z + 1) / 2) * 0.5).toFixed(2)})`}
            />
          ))}
          <circle cx={CX} cy={CY} r={R} fill="none"
            stroke={`rgba(${dotColor},0.18)`} strokeWidth="1" />
        </g>

        {/* flight arcs + comet trails */}
        <g filter="url(#vm-glow)">
          {ARC_PAIRS.map(([i, j], k) => {
            const d = arcPath(PINS[i], PINS[j]);
            return (
              <g key={k}>
                <path id={`vm-path-${k}`} d={d} fill="none"
                  stroke={`url(#vm-arc-${k})`} strokeWidth="1.6" />
                <circle r="3" fill={pinColor}>
                  <animateMotion dur={`${6 + k}s`} repeatCount="indefinite" rotate="auto">
                    <mpath xlinkHref={`#vm-path-${k}`} />
                  </animateMotion>
                </circle>
              </g>
            );
          })}
        </g>

        {/* location pins */}
        {PINS.map((p, i) => (
          <g key={i}>
            <circle className="vm-ping" cx={p.x} cy={p.y} r="6"
              fill="none" stroke={pinColor} strokeWidth="1.5"
              style={{ animationDelay: `${i * 0.5}s` }} />
            <circle cx={p.x} cy={p.y} r="3" fill={pinColor} filter="url(#vm-glow)" />
          </g>
        ))}

        {/* faint network nodes */}
        {dots.slice(0, 26).map((_d, i) => (
          <circle
            key={`n${i}`}
            className="vm-twinkle"
            cx={(i * 137) % VB_W}
            cy={(i * 263) % VB_H}
            r="1.4"
            fill={`rgba(${dotColor},0.5)`}
            style={{ animationDelay: `${(i % 7) * 0.6}s` }}
          />
        ))}
      </svg>
    </div>
  );
}
