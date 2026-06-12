export default function RefineSidebar() {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-card">
      <div className="flex items-center justify-between px-5 pt-5">
        <h3 className="text-sm font-bold text-ink">Refine your search</h3>
      </div>
      <div className="px-5 pb-5 pt-3">
        <p className="text-sm leading-relaxed text-slate-500">
          Filter options will appear when live search metadata is available.
        </p>
      </div>
    </div>
  );
}
