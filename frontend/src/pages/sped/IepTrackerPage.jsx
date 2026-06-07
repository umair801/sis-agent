import { useState, useEffect } from "react";
import { spedApi } from "../../api/sped";
import { studentsApi } from "../../api/students";
import { Spinner } from "../../components/ui/Spinner";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { cn } from "../../utils/cn";
import {
  FileText, Search, Filter, AlertTriangle,
  Clock, CheckCircle, ChevronDown, ExternalLink,
} from "lucide-react";

const URGENCY_CONFIG = {
  overdue:    { label: "Overdue",    bg: "bg-red-50    border-red-200",    text: "text-red-700",    dot: "bg-red-500",     badge: "bg-red-50    text-red-700    ring-1 ring-red-200"    },
  this_week:  { label: "This Week",  bg: "bg-amber-50  border-amber-200",  text: "text-amber-700",  dot: "bg-amber-500",   badge: "bg-amber-50  text-amber-700  ring-1 ring-amber-200"  },
  this_month: { label: "This Month", bg: "bg-primary-50 border-primary-200", text: "text-primary-700", dot: "bg-primary-500", badge: "bg-primary-50 text-primary-700 ring-1 ring-primary-200" },
  ok:         { label: "On Track",   bg: "bg-white      border-surface-border", text: "text-text-primary", dot: "bg-emerald-500", badge: "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200" },
};

function getUrgency(dueDateStr) {
  if (!dueDateStr) return "ok";
  const diff = (new Date(dueDateStr) - new Date()) / (1000 * 60 * 60 * 24);
  if (diff < 0)   return "overdue";
  if (diff <= 7)  return "this_week";
  if (diff <= 30) return "this_month";
  return "ok";
}

function daysUntil(dueDateStr) {
  if (!dueDateStr) return null;
  const diff = Math.round((new Date(dueDateStr) - new Date()) / (1000 * 60 * 60 * 24));
  if (diff < 0)  return `${Math.abs(diff)}d overdue`;
  if (diff === 0) return "Due today";
  return `${diff}d left`;
}

const MOCK_IEPS = [
  { id: "1", student_name: "Emma Rodriguez",  grade: "Grade 10", iep_type: "Learning Disability",  review_date: "2026-06-08", last_review: "2025-06-08", coordinator: "Maria Garcia", status: "active", accommodations: 4 },
  { id: "2", student_name: "James Wilson",    grade: "Grade 9",  iep_type: "Speech-Language",      review_date: "2026-06-12", last_review: "2025-06-12", coordinator: "Maria Garcia", status: "active", accommodations: 3 },
  { id: "3", student_name: "Aisha Patel",     grade: "Grade 11", iep_type: "Emotional Behavioral", review_date: "2026-06-25", last_review: "2025-06-25", coordinator: "Maria Garcia", status: "active", accommodations: 6 },
  { id: "4", student_name: "Carlos Mendez",   grade: "Grade 12", iep_type: "Autism Spectrum",      review_date: "2026-07-15", last_review: "2025-07-15", coordinator: "Maria Garcia", status: "active", accommodations: 5 },
  { id: "5", student_name: "Sofia Nguyen",    grade: "Grade 10", iep_type: "Physical Disability",  review_date: "2026-08-01", last_review: "2025-08-01", coordinator: "Maria Garcia", status: "active", accommodations: 2 },
];

const FILTER_OPTIONS = ["All", "Overdue", "This Week", "This Month", "On Track"];

export default function IepTrackerPage() {
  const [ieps,      setIeps]      = useState(MOCK_IEPS);
  const [loading,   setLoading]   = useState(true);
  const [search,    setSearch]    = useState("");
  const [filter,    setFilter]    = useState("All");
  const [expanded,  setExpanded]  = useState(null);

  useEffect(() => {
    spedApi.listIeps({ limit: 50 })
      .then((res) => {
        const d    = res.data;
        const list = Array.isArray(d) ? d : (d?.ieps || d?.items || []);
        if (list.length > 0) setIeps(list);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = ieps.filter((iep) => {
    const name    = (iep.student_name || "").toLowerCase();
    const type    = (iep.iep_type || iep.disability_category || "").toLowerCase();
    const matchSearch = !search || name.includes(search.toLowerCase()) || type.includes(search.toLowerCase());
    const urgency = getUrgency(iep.review_date);
    const matchFilter =
      filter === "All"        ? true :
      filter === "Overdue"    ? urgency === "overdue" :
      filter === "This Week"  ? urgency === "this_week" :
      filter === "This Month" ? urgency === "this_month" :
      filter === "On Track"   ? urgency === "ok" : true;
    return matchSearch && matchFilter;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner className="w-7 h-7" />
      </div>
    );
  }

  const overdueCount  = ieps.filter(i => getUrgency(i.review_date) === "overdue").length;
  const thisWeekCount = ieps.filter(i => getUrgency(i.review_date) === "this_week").length;

  return (
    <div className="space-y-5 max-w-5xl">

      {/* Alert banner */}
      {(overdueCount > 0 || thisWeekCount > 0) && (
        <div className="flex items-center gap-3 px-5 py-3.5 rounded-2xl bg-red-50 border border-red-200">
          <AlertTriangle size={18} className="text-red-600 shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-red-700">
              Compliance action required
            </p>
            <p className="text-xs text-red-600 mt-0.5">
              {overdueCount > 0 && `${overdueCount} IEP${overdueCount > 1 ? "s" : ""} overdue. `}
              {thisWeekCount > 0 && `${thisWeekCount} review${thisWeekCount > 1 ? "s" : ""} due this week.`}
            </p>
          </div>
        </div>
      )}

      {/* Search + filter bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by student name or IEP type..."
            className="w-full pl-9 pr-4 py-2.5 bg-white border border-surface-border rounded-xl text-sm
                       focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
            style={{ color: "#111827" }}
          />
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {FILTER_OPTIONS.map((opt) => (
            <button
              key={opt}
              onClick={() => setFilter(opt)}
              className={cn(
                "px-3 py-2 rounded-xl text-xs font-semibold border transition-all",
                filter === opt
                  ? "bg-primary-600 text-white border-primary-600"
                  : "bg-white text-text-secondary border-surface-border hover:border-primary-300"
              )}
            >
              {opt}
              {opt === "Overdue"   && overdueCount  > 0 && (
                <span className="ml-1.5 bg-red-500 text-white rounded-full px-1.5 py-0.5 text-[9px]">{overdueCount}</span>
              )}
              {opt === "This Week" && thisWeekCount > 0 && (
                <span className="ml-1.5 bg-amber-500 text-white rounded-full px-1.5 py-0.5 text-[9px]">{thisWeekCount}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Results count */}
      <p className="text-xs text-text-muted">
        Showing {filtered.length} of {ieps.length} IEPs
      </p>

      {/* IEP Cards */}
      {filtered.length === 0 ? (
        <div className="text-center py-16 card">
          <FileText size={32} className="text-text-muted mx-auto mb-3" />
          <p className="text-sm text-text-muted">No IEPs match your filter.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered
            .sort((a, b) => new Date(a.review_date) - new Date(b.review_date))
            .map((iep) => {
              const urgency = getUrgency(iep.review_date);
              const cfg     = URGENCY_CONFIG[urgency];
              const isOpen  = expanded === iep.id;
              const dueStr  = iep.review_date
                ? new Date(iep.review_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
                : "No date set";
              const remaining = daysUntil(iep.review_date);
              const student = iep.student_name || "Unknown Student";

              return (
                <div
                  key={iep.id}
                  className={cn("rounded-2xl border transition-all duration-200", cfg.bg)}
                >
                  {/* Card header — always visible */}
                  <div
                    className="flex items-center gap-4 px-5 py-4 cursor-pointer"
                    onClick={() => setExpanded(isOpen ? null : iep.id)}
                  >
                    {/* Urgency dot */}
                    <span className={cn("w-2.5 h-2.5 rounded-full shrink-0 mt-0.5", cfg.dot)} />

                    {/* Avatar */}
                    <div className="w-10 h-10 rounded-full bg-violet-100 flex items-center justify-center shrink-0">
                      <span className="text-xs font-bold text-violet-700">
                        {student.split(" ").map(n => n[0]).join("").slice(0, 2)}
                      </span>
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="text-sm font-semibold text-text-primary">{student}</p>
                        <span className="text-[10px] text-text-muted">{iep.grade}</span>
                      </div>
                      <p className="text-xs text-text-secondary mt-0.5">
                        {iep.iep_type || iep.disability_category || "IEP"}
                      </p>
                    </div>

                    {/* Due date */}
                    <div className="text-right shrink-0">
                      <p className="text-xs font-medium text-text-secondary">{dueStr}</p>
                      {remaining && (
                        <span className={cn("badge text-[10px] mt-0.5", cfg.badge)}>
                          {remaining}
                        </span>
                      )}
                    </div>

                    {/* Expand */}
                    <ChevronDown
                      size={15}
                      className={cn("text-text-muted shrink-0 transition-transform", isOpen && "rotate-180")}
                    />
                  </div>

                  {/* Expanded detail */}
                  {isOpen && (
                    <div className="px-5 pb-5 pt-1 border-t border-surface-border/60">
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-3">
                        <div>
                          <p className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">Review Date</p>
                          <p className="text-sm font-medium text-text-primary mt-0.5">{dueStr}</p>
                        </div>
                        <div>
                          <p className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">Last Review</p>
                          <p className="text-sm font-medium text-text-primary mt-0.5">
                            {iep.last_review
                              ? new Date(iep.last_review).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
                              : "N/A"}
                          </p>
                        </div>
                        <div>
                          <p className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">Coordinator</p>
                          <p className="text-sm font-medium text-text-primary mt-0.5">{iep.coordinator || "N/A"}</p>
                        </div>
                        <div>
                          <p className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">Accommodations</p>
                          <p className="text-sm font-medium text-text-primary mt-0.5">{iep.accommodations ?? "N/A"}</p>
                        </div>
                      </div>
                      <div className="flex gap-2 mt-4">
                        <button className="btn-primary text-xs py-2 px-4">
                          Schedule Review
                        </button>
                        <button className="px-4 py-2 rounded-xl border border-surface-border text-xs font-semibold text-text-secondary hover:bg-surface-muted transition-colors">
                          View Full IEP
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
        </div>
      )}
    </div>
  );
}
