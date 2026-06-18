import { useEffect, useState } from "react";

const MESSAGES = [
  "Planning your trip…",
  "Checking the weather…",
  "Finding places to stay…",
  "Mapping out your days…",
  "Working out the budget…",
];

export default function Loader() {
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((p) => (p + 1) % MESSAGES.length), 1800);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="flex flex-col items-center gap-3 py-20">
      <div className="flex gap-1.5">
        {[0, 1, 2].map((d) => (
          <span
            key={d}
            className="h-2.5 w-2.5 animate-bounce rounded-full bg-blue-600"
            style={{ animationDelay: `${d * 0.15}s` }}
          />
        ))}
      </div>
      <p className="text-sm text-zinc-500">{MESSAGES[i]}</p>
    </div>
  );
}
