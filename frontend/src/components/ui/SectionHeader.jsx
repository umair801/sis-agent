export function SectionHeader({ title, subtitle, action, actionLabel }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div>
        <h2 className="text-sm font-semibold text-text-primary">{title}</h2>
        {subtitle && <p className="text-xs text-text-muted mt-0.5">{subtitle}</p>}
      </div>
      {action && (
        <button
          onClick={action}
          className="text-xs text-primary-600 hover:text-primary-700 font-semibold transition-colors"
        >
          {actionLabel || "View all"}
        </button>
      )}
    </div>
  );
}
