import { cn } from "../../utils/cn";

const STATUS_STYLES = {
  active:   "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
  inactive: "bg-gray-100   text-gray-500   ring-1 ring-gray-200",
  pending:  "bg-amber-50   text-amber-700  ring-1 ring-amber-200",
  present:  "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
  absent:   "bg-red-50     text-red-700    ring-1 ring-red-200",
  late:     "bg-amber-50   text-amber-700  ring-1 ring-amber-200",
  excused:  "bg-sky-50     text-sky-700    ring-1 ring-sky-200",
  open:     "bg-primary-50 text-primary-700 ring-1 ring-primary-200",
  closed:   "bg-gray-100   text-gray-500   ring-1 ring-gray-200",
  overdue:  "bg-red-50     text-red-700    ring-1 ring-red-200",
};

export function StatusBadge({ status, label }) {
  const key = (status || "").toLowerCase();
  return (
    <span className={cn("badge capitalize font-medium", STATUS_STYLES[key] || "bg-gray-100 text-gray-500 ring-1 ring-gray-200")}>
      {label || status}
    </span>
  );
}
