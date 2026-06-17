interface Props {
  query: string;
  setQuery: (v: string) => void;
  onSubmit: () => void;
  running: boolean;
}

const EXAMPLES = [
  "Plan a 5-night trip from Mumbai to Tokyo for 2 people, budget $3000, love food and culture",
  "Beach holiday for a family of 4, 6 nights, budget $2500, from London",
  "Adventure trip with hiking and nature, 4 nights, budget $1200",
];

export default function PlanForm({ query, setQuery, onSubmit, running }: Props) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur">
      <label className="mb-2 block text-sm font-medium text-slate-300">
        Describe your trip
      </label>
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        rows={3}
        placeholder="e.g. Plan a 5-night trip from Mumbai to Tokyo for 2, budget $3000, love food & culture"
        className="w-full resize-none rounded-xl border border-white/10 bg-slate-900/60 p-3 text-sm text-slate-100 outline-none placeholder:text-slate-500 focus:border-indigo-400/60"
      />
      <div className="mt-3 flex flex-wrap gap-2">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => setQuery(ex)}
            disabled={running}
            className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-400 transition hover:border-indigo-400/50 hover:text-slate-200 disabled:opacity-40"
          >
            {ex.length > 42 ? ex.slice(0, 42) + "…" : ex}
          </button>
        ))}
      </div>
      <button
        onClick={onSubmit}
        disabled={running || !query.trim()}
        className="mt-4 w-full rounded-xl bg-gradient-to-r from-indigo-500 to-fuchsia-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {running ? "Agents working…" : "Plan my trip ✦"}
      </button>
    </div>
  );
}
