import { ImageOff } from "lucide-react";

/**
 * Neutral product placeholder.
 * Per project requirement, NO product images are generated — every
 * product slot renders this clean placeholder instead.
 */
export default function ProductPlaceholder({ label }: { label?: string }) {
  return (
    <div className="grid h-28 w-24 shrink-0 place-items-center self-start rounded-xl border border-dashed border-slate-200 bg-slate-50 text-center">
      <div className="flex flex-col items-center gap-1 px-1">
        <ImageOff className="h-5 w-5 text-slate-300" />
        <span className="text-[9px] font-medium leading-tight text-slate-400">
          {label ?? "Product"}
        </span>
      </div>
    </div>
  );
}
