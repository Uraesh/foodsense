import { Sparkles, Search, ArrowRight } from "lucide-react";

type HeroProps = {
  query: string;
  isLoading: boolean;
  onQueryChange: (value: string) => void;
  onSearch: () => void;
};

export default function Hero({
  query,
  isLoading,
  onQueryChange,
  onSearch,
}: HeroProps) {
  return (
    <section className="mx-auto max-w-3xl px-6 pb-10 pt-6 text-center">
      <div className="mb-6 inline-flex items-center gap-1.5 rounded-full bg-brand/10 px-3 py-1 text-xs font-semibold text-brand">
        <Sparkles className="h-3.5 w-3.5" />
        Smarter Food Choices
      </div>

      <h1 className="text-4xl font-extrabold leading-tight tracking-tight text-ink sm:text-5xl">
        Discover. Understand.
        <br />
        <span className="text-brand">Eat Better.</span>
      </h1>

      <p className="mx-auto mt-4 max-w-xl text-sm text-slate-500 sm:text-base">
        AI-powered search that helps you find the best food for your body and
        mind.
      </p>

      <div className="mx-auto mt-8 flex max-w-2xl items-center gap-2 rounded-full border border-slate-200 bg-white py-2 pl-5 pr-2 shadow-search">
        <Search className="h-5 w-5 shrink-0 text-slate-400" />
        <input
          type="text"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              onSearch();
            }
          }}
          className="w-full bg-transparent text-sm text-slate-700 outline-none placeholder:text-slate-400"
          placeholder="Search for any food, brand or product..."
        />
        <button
          type="button"
          disabled={isLoading}
          onClick={onSearch}
          aria-label="Search"
          className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-brand text-white transition-colors hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-50"
        >
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>

      <div className="mt-5 text-sm text-slate-500">
        Enter a search query to explore food products and nutrition insights.
      </div>
    </section>
  );
}
