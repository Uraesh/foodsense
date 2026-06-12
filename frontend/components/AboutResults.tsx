export default function AboutResults() {
  return (
    <div className="rounded-2xl border border-slate-100 bg-slate-50/60 p-5 shadow-card">
      <h3 className="text-sm font-bold text-ink">About our results</h3>
      <p className="mt-2 text-xs leading-relaxed text-slate-500">
        Our AI analyzes ingredients, nutrition facts, and user reviews to rank
        products by relevance and quality.
      </p>
      <a
        href="#"
        className="mt-3 inline-block text-xs font-semibold text-brand hover:underline"
      >
        Learn more about our process →
      </a>
    </div>
  );
}
