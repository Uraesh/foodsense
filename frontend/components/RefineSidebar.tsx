import {
  categoryFilters,
  dietaryFilters,
  healthGoals,
} from "@/lib/data";

type FilterItem = { label: string; count: string; checked: boolean };

function FilterGroup({
  title,
  items,
  showMore = true,
}: {
  title: string;
  items: FilterItem[];
  showMore?: boolean;
}) {
  return (
    <div className="border-t border-slate-100 px-5 py-4 first:border-t-0">
      <h4 className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-500">
        {title}
      </h4>
      <ul className="space-y-2.5">
        {items.map((item) => (
          <li
            key={item.label}
            className="flex items-center justify-between text-sm"
          >
            <label className="flex cursor-pointer items-center gap-2 text-slate-600">
              <input
                type="checkbox"
                defaultChecked={item.checked}
                className="h-4 w-4 rounded border-slate-300 text-brand accent-brand"
              />
              {item.label}
            </label>
            <span className="text-xs text-slate-400">{item.count}</span>
          </li>
        ))}
      </ul>
      {showMore && (
        <button className="mt-3 text-xs font-semibold text-brand hover:underline">
          + Show more
        </button>
      )}
    </div>
  );
}

export default function RefineSidebar() {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-card">
      <div className="flex items-center justify-between px-5 pt-5">
        <h3 className="text-sm font-bold text-ink">Refine your search</h3>
        <button className="text-xs font-semibold text-brand hover:underline">
          Clear all
        </button>
      </div>
      <div className="mt-3">
        <FilterGroup title="Category" items={categoryFilters} />
        <FilterGroup title="Dietary preferences" items={dietaryFilters} />
        <FilterGroup title="Health goals" items={healthGoals} />
      </div>
    </div>
  );
}
