/**
 * Large, faint wireframe globe (thin longitude + latitude lines) sitting behind
 * the hero content. Orthographic-style graticule — elegant, not distracting.
 */
const R = 150;
const C = 160; // center (viewBox 320x320)

export default function HeroGlobe() {
  // meridians (longitude): vertical ellipses of varying width
  const meridians = [];
  for (let k = 1; k < 6; k++) {
    const rx = Math.abs(R * Math.cos((k * Math.PI) / 6));
    meridians.push(rx);
  }
  // parallels (latitude): flattened horizontal ellipses
  const parallels = [-60, -30, 0, 30, 60].map((lat) => {
    const rad = (lat * Math.PI) / 180;
    return { y: R * Math.sin(rad), rx: R * Math.cos(rad) };
  });

  return (
    <svg
      viewBox="0 0 320 320"
      className="pointer-events-none absolute left-1/2 top-1/2 -z-10 h-[120vmin] w-[120vmin] max-w-none -translate-x-1/2 -translate-y-1/2 text-amber-400/70 opacity-[0.09] dark:opacity-[0.10]"
      aria-hidden="true"
    >
      <g fill="none" stroke="currentColor" strokeWidth="0.6">
        <circle cx={C} cy={C} r={R} strokeWidth="0.9" />
        {meridians.map((rx, i) => (
          <ellipse key={`m${i}`} cx={C} cy={C} rx={rx} ry={R} />
        ))}
        <line x1={C} y1={C - R} x2={C} y2={C + R} />
        {parallels.map((p, i) => (
          <ellipse key={`p${i}`} cx={C} cy={C - p.y} rx={p.rx} ry={p.rx * 0.16} />
        ))}
      </g>
    </svg>
  );
}
