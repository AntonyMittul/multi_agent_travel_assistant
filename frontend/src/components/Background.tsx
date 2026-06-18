import { WORLD_PATH } from "../lib/worldPaths";

/**
 * Travel-themed backdrop: a minimal equirectangular world-map outline with an
 * ocean grid, a handful of glowing flight routes and location markers.
 * No floating particles. Theme-aware, subtle, full-bleed.
 */

const VB_W = 1000;
const VB_H = 500;
const proj = (lon: number, lat: number): [number, number] => [
  ((lon + 180) / 360) * VB_W,
  ((90 - lat) / 180) * VB_H,
];

// major hubs (lon, lat)
const HUB = {
  ny: proj(-74, 40.7), lon: proj(-0.1, 51.5), dxb: proj(55.3, 25.2),
  bom: proj(72.8, 19.1), sin: proj(103.8, 1.3), hnd: proj(139.7, 35.7),
  syd: proj(151.2, -33.9), gru: proj(-46.6, -23.5),
};
const ROUTES: [[number, number], [number, number]][] = [
  [HUB.ny, HUB.lon], [HUB.lon, HUB.dxb], [HUB.dxb, HUB.bom],
  [HUB.sin, HUB.hnd], [HUB.bom, HUB.syd],
];
const MARKERS = [HUB.ny, HUB.lon, HUB.dxb, HUB.bom, HUB.sin, HUB.hnd, HUB.syd, HUB.gru];

function arc([x1, y1]: number[], [x2, y2]: number[]) {
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2 - Math.hypot(x2 - x1, y2 - y1) * 0.2;
  return `M${x1},${y1} Q${mx},${my} ${x2},${y2}`;
}

const GRID_LON = [-150, -120, -90, -60, -30, 0, 30, 60, 90, 120, 150];
const GRID_LAT = [60, 30, 0, -30, -60];

export default function Background({ dark }: { dark: boolean }) {
  const base = dark
    ? "radial-gradient(1100px 600px at 70% -10%, rgba(37,99,235,0.12), transparent 60%)," +
      "linear-gradient(160deg, #06090e 0%, #0a0f17 60%, #0c1119 100%)"
    : "radial-gradient(1000px 600px at 80% -10%, rgba(59,130,246,0.08), transparent 60%)," +
      "linear-gradient(160deg, #f8fafc 0%, #eef2f7 100%)";

  const grid = dark ? "rgba(125,145,175,0.08)" : "rgba(100,116,139,0.10)";
  const landFill = dark ? "rgba(130,155,190,0.05)" : "rgba(100,116,139,0.06)";
  const landStroke = dark ? "rgba(140,170,210,0.22)" : "rgba(71,85,105,0.30)";
  const routeFaint = dark ? "rgba(212,175,55,0.18)" : "rgba(202,138,4,0.20)";

  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden" style={{ background: base }}>
      <svg
        className="h-full w-full"
        viewBox={`0 0 ${VB_W} ${VB_H}`}
        preserveAspectRatio="xMidYMid slice"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="vm-route" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="#F4D58D" />
            <stop offset="1" stopColor="#D4AF37" />
          </linearGradient>
          <filter id="vm-glow" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="3" result="b" />
            <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* ocean grid */}
        <g stroke={grid} strokeWidth="0.6">
          {GRID_LON.map((lo) => {
            const x = proj(lo, 0)[0];
            return <line key={`v${lo}`} x1={x} y1="0" x2={x} y2={VB_H} />;
          })}
          {GRID_LAT.map((la) => {
            const y = proj(0, la)[1];
            return <line key={`h${la}`} x1="0" y1={y} x2={VB_W} y2={y} />;
          })}
        </g>

        {/* world map outline */}
        <path d={WORLD_PATH} fill={landFill} stroke={landStroke} strokeWidth="0.6"
          fillRule="evenodd" vectorEffect="non-scaling-stroke" />

        {/* flight routes */}
        <g filter="url(#vm-glow)">
          {ROUTES.map((r, i) => {
            const d = arc(r[0], r[1]);
            return (
              <g key={i}>
                <path d={d} fill="none" stroke={routeFaint} strokeWidth="1" />
                <path d={d} fill="none" stroke="url(#vm-route)" strokeWidth="1.4"
                  strokeLinecap="round" className="vm-route"
                  style={{ animationDelay: `${i * 0.7}s` }} />
              </g>
            );
          })}
        </g>

        {/* location markers */}
        {MARKERS.map(([x, y], i) => (
          <g key={i}>
            <circle className="vm-ping" cx={x} cy={y} r="3.5" fill="none"
              stroke="#D4AF37" strokeWidth="1" style={{ animationDelay: `${i * 0.4}s` }} />
            <circle cx={x} cy={y} r="2" fill="#F4D58D" filter="url(#vm-glow)" />
          </g>
        ))}
      </svg>
    </div>
  );
}
