import { Bell, Search, Brain } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";

export function TopBar({ title, onAiOpen }) {
  const { user } = useAuth();
  const initial  = (user?.full_name || user?.email || "U")[0].toUpperCase();

  return (
    <header className="h-14 bg-surface-card border-b border-surface-border flex items-center justify-between px-6 shrink-0 shadow-sm">
      <h1 className="font-display text-base font-semibold text-text-primary tracking-tight">
        {title}
      </h1>
      <div className="flex items-center gap-1">
        <button className="p-2 rounded-xl text-text-muted hover:text-text-primary hover:bg-surface-muted transition-all">
          <Search size={16} />
        </button>
        <button className="p-2 rounded-xl text-text-muted hover:text-text-primary hover:bg-surface-muted transition-all relative">
          <Bell size={16} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-primary-500" />
        </button>
        {/* AI Query button */}
        <button
          onClick={onAiOpen}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-primary-50
                     hover:bg-primary-100 text-primary-700 text-xs font-semibold
                     border border-primary-200 transition-all ml-1"
          title="Ask AI"
        >
          <Brain size={14} />
          <span className="hidden sm:inline">Ask AI</span>
        </button>
        <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center ml-2 shadow-sm">
          <span className="text-xs font-bold text-white">{initial}</span>
        </div>
      </div>
    </header>
  );
}
