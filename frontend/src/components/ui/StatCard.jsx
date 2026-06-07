import { cn } from "../../utils/cn";
import { Spinner } from "./Spinner";

const COLOR_MAP = {
  primary: { icon: "text-primary-600 bg-primary-50",  value: "text-primary-700" },
  green:   { icon: "text-emerald-600 bg-emerald-50",  value: "text-emerald-700" },
  yellow:  { icon: "text-amber-600   bg-amber-50",    value: "text-amber-700"   },
  red:     { icon: "text-red-600     bg-red-50",      value: "text-red-700"     },
  blue:    { icon: "text-sky-600     bg-sky-50",      value: "text-sky-700"     },
  purple:  { icon: "text-violet-600  bg-violet-50",   value: "text-violet-700"  },
  indigo:  { icon: "text-indigo-600  bg-indigo-50",   value: "text-indigo-700"  },
};

export function StatCard({ title, value, subtitle, icon: Icon, trend, color = "primary", loading }) {
  const colors = COLOR_MAP[color] || COLOR_MAP.primary;

  return (
    <div className="card-hover p-5 flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider">{title}</p>
        {Icon && (
          <span className={cn("w-9 h-9 rounded-xl flex items-center justify-center shrink-0", colors.icon)}>
            <Icon size={17} />
          </span>
        )}
      </div>
      {loading ? (
        <Spinner className="w-5 h-5 border-surface-border border-t-primary-500" />
      ) : (
        <>
          <p className={cn("text-2xl font-display font-bold", colors.value)}>{value ?? "--"}</p>
          {(subtitle || trend !== undefined) && (
            <div className="flex items-center gap-2">
              {trend !== undefined && (
                <span className={cn(
                  "text-xs font-semibold px-1.5 py-0.5 rounded-md",
                  trend > 0
                    ? "text-emerald-700 bg-emerald-50"
                    : trend < 0
                    ? "text-red-700 bg-red-50"
                    : "text-text-muted bg-surface-muted"
                )}>
                  {trend > 0 ? "+" : ""}{trend}%
                </span>
              )}
              {subtitle && <p className="text-xs text-text-muted">{subtitle}</p>}
            </div>
          )}
        </>
      )}
    </div>
  );
}
