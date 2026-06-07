import { cn } from "../../utils/cn";

export function Spinner({ className }) {
  return (
    <div
      className={cn(
        "w-5 h-5 rounded-full border-2 border-surface-border border-t-primary-500 animate-spin",
        className
      )}
    />
  );
}
