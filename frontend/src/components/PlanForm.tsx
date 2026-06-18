interface Props {
  query: string;
  setQuery: (v: string) => void;
  onSubmit: () => void;
  running: boolean;
}

const EXAMPLES = [
  "5-night trip from Mumbai to Tokyo for 2, budget $3000, love food and culture",
  "Beach holiday from London for a family of 4, 6 nights, budget $2500",
  "Adventure trip with hiking and nature, 4 nights, budget $1200",
];

export default function PlanForm({ query, setQuery, onSubmit, running }: Props) {
  return (
    <section className="rounded-md border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
      <label className="mb-2 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
        Describe your trip
      </label>
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        rows={3}
        placeholder="e.g. 5-night trip from Mumbai to Tokyo for 2, budget $3000, love food and culture"
        className="w-full resize-none rounded-md border border-zinc-300 bg-white p-2.5 text-sm text-zinc-900 outline-none placeholder:text-zinc-400 focus:border-blue-500 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100"
      />

      <div className="mt-3 space-y-1">
        <p className="text-xs text-zinc-500 dark:text-zinc-500">Try:</p>
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => setQuery(ex)}
            disabled={running}
            className="block w-full truncate rounded border border-zinc-200 px-2.5 py-1.5 text-left text-xs text-zinc-600 hover:bg-zinc-50 disabled:opacity-40 dark:border-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-800"
          >
            {ex}
          </button>
        ))}
      </div>

      <button
        onClick={onSubmit}
        disabled={running || !query.trim()}
        className="mt-4 w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {running ? "Planning…" : "Plan my trip"}
      </button>
    </section>
  );
}
