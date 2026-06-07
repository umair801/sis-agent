import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { spedApi } from "../../api/sped";
import { studentsApi } from "../../api/students";
import { StatCard } from "../../components/ui/StatCard";
import { SectionHeader } from "../../components/ui/SectionHeader";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { Spinner } from "../../components/ui/Spinner";
import {
  FileText, ShieldCheck, AlertTriangle, Clock,
  CheckCircle, ChevronRight, Users, AlertCircle,
} from "lucide-react";
import { cn } from "../../utils/cn";

const URGENCY = {
  overdue:   { label: "Overdue",     color: "bg-red-50    border-red-200    text-red-700",    dot: "bg-red-500"     },
  this_week: { label: "This Week",   color: "bg-amber-50  border-amber-200  text-amber-700",  dot: "bg-amber-500"   },
  this_month:{ label: "This Month",  color: "bg-primary-50 border-primary-200 text-primary-700", dot: "bg-primary-500" },
  ok:        { label: "On Track",    color: "bg-emerald-50 border-emerald-200 text-emerald-700", dot: "bg-emerald-500" },
};

function getUrgency(dueDateStr) {
  if (!dueDateStr) return "ok";
  const due  = new Date(dueDateStr);
  const now  = new Date();
  const diff = (due - now) / (1000 * 60 * 60 * 24);
  if (diff < 0)   return "overdue";
  if (diff <= 7)  return "this_week";
  if (diff <= 30) return "this_month";
  return "ok";
}

// Mock IEP data — will be replaced with real data once backend IEPs are seeded
const MOCK_IEPS = [
  { id: "1", student_name: "Emma Rodriguez", grade: "Grade 10", iep_type: "Learning Disability", review_date: "2026-06-08", coordinator: "Maria Garcia", status: "active" },
  { id: "2", student_name: "James Wilson",   grade: "Grade 9",  iep_type: "Speech-Language",     review_date: "2026-06-12", coordinator: "Maria Garcia", status: "active" },
  { id: "3", student_name: "Aisha Patel",    grade: "Grade 11", iep_type: "Emotional Behavioral", review_date: "2026-06-25", coordinator: "Maria Garcia", status: "active" },
  { id: "4", student_name: "Carlos Mendez",  grade: "Grade 12", iep_type: "Autism Spectrum",     review_date: "2026-07-15", coordinator: "Maria Garcia", status: "active" },
  { id: "5", student_name: "Sofia Nguyen",   grade: "Grade 10", iep_type: "Physical Disability", review_date: "2026-08-01", coordinator: "Maria Garcia", status: "active" },
];

export default function SpEdDashboard() {
  const { user }                      = useAuth();
  const navigate                      = useNavigate();
  const [students,  setStudents]      = useState([]);
  const [ieps,      setIeps]          = useState(MOCK_IEPS);
  const [loading,   setLoading]       = useState(true);
  const [error,     setError]         = useState(null);

  useEffect(() => {
    Promise.allSettled([
      spedApi.listIeps({ limit: 20 }),
      studentsApi.list({ limit: 10 }),
    ]).then(([iepRes, stuRes]) => {
      if (iepRes.status === "fulfilled") {
        const d = iepRes.value.data;
        const list = Array.isArray(d) ? d : (d?.ieps || d?.items || []);
        if (list.length > 0) setIeps(list);
      }
      if (stuRes.status === "fulfilled") {
        const d = stuRes.value.data;
        setStudents(Array.isArray(d) ? d : (d?.students || d?.items || []));
      }
    }).catch(() => setError("Some data could not be loaded."))
      .finally(() => setLoading(false));
  }, []);

  const overdue   = ieps.filter(i => getUrgency(i.review_date) === "overdue").length;
  const thisWeek  = ieps.filter(i => getUrgency(i.review_date) === "this_week").length;
  const onTrack   = ieps.filter(i => getUrgency(i.review_date) === "ok").length;

  return (
    <div className="space-y-7 max-w-6xl">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-display text-xl font-bold text-text-primary">
            SpEd Coordinator Dashboard
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            {user?.full_name} · Westlake Unified
          </p>
        </div>
        <span className="badge bg-violet-50 text-violet-700 ring-1 ring-violet-200 text-xs font-semibold px-3 py-1.5">
          SpEd Coordinator
        </span>
      </div>

      {error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-700 text-sm">
          <AlertCircle size={15} className="shrink-0" /> {error}
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Active IEPs"     value={loading ? null : ieps.length}    subtitle="This year"      icon={FileText}    color="primary" loading={loading} />
        <StatCard title="Overdue Reviews" value={loading ? null : overdue}        subtitle="Action required" icon={AlertTriangle} color="red"   loading={loading} />
        <StatCard title="Due This Week"   value={loading ? null : thisWeek}       subtitle="Upcoming"       icon={Clock}       color="yellow" loading={loading} />
        <StatCard title="Compliance"      value={overdue === 0 ? "100%" : `${Math.round((1 - overdue/ieps.length)*100)}%`} subtitle="IDEA compliant" icon={ShieldCheck} color="green" />
      </div>

      {/* Two-column tablet layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* IEP list — 2 cols */}
        <div className="card p-5 lg:col-span-2">
          <SectionHeader
            title="IEP Review Schedule"
            subtitle="Sorted by urgency"
            action={() => navigate("/sped/iep")}
            actionLabel="Full tracker"
          />
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner className="w-6 h-6" />
            </div>
          ) : (
            <div className="space-y-2">
              {ieps
                .sort((a, b) => new Date(a.review_date) - new Date(b.review_date))
                .map((iep) => {
                  const urgency = getUrgency(iep.review_date);
                  const u       = URGENCY[urgency];
                  const dueDate = iep.review_date
                    ? new Date(iep.review_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
                    : "No date";
                  const student = iep.student_name ||
                    (students.find(s => s.id === iep.student_id)
                      ? `${students.find(s => s.id === iep.student_id).first_name} ${students.find(s => s.id === iep.student_id).last_name}`
                      : "Unknown Student");

                  return (
                    <div
                      key={iep.id}
                      onClick={() => navigate("/sped/iep")}
                      className="flex items-center justify-between px-4 py-3 rounded-xl hover:bg-surface-muted transition-colors cursor-pointer group"
                    >
                      <div className="flex items-center gap-3">
                        <span className={cn("w-2 h-2 rounded-full shrink-0", u.dot)} />
                        <div className="w-9 h-9 rounded-xl bg-violet-50 flex items-center justify-center shrink-0">
                          <FileText size={14} className="text-violet-600" />
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-text-primary">{student}</p>
                          <p className="text-[10px] text-text-muted">
                            {iep.iep_type || iep.disability_category || "IEP"} · {iep.grade || ""}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <p className="text-xs font-medium text-text-secondary">{dueDate}</p>
                          <span className={cn("badge border text-[10px]", u.color)}>{u.label}</span>
                        </div>
                        <ChevronRight size={14} className="text-text-muted group-hover:text-text-secondary" />
                      </div>
                    </div>
                  );
                })}
            </div>
          )}
        </div>

        {/* Right column */}
        <div className="space-y-4">
          {/* Compliance summary */}
          <div className="card p-5">
            <SectionHeader title="Compliance Summary" />
            <div className="space-y-2.5">
              {[
                { label: "Overdue reviews",  value: overdue,   color: overdue > 0 ? "text-red-600 font-bold" : "text-emerald-600 font-bold" },
                { label: "Due this week",    value: thisWeek,  color: thisWeek > 0 ? "text-amber-600 font-bold" : "text-emerald-600 font-bold" },
                { label: "On track",         value: onTrack,   color: "text-emerald-600 font-bold" },
                { label: "Total active IEPs",value: ieps.length, color: "text-primary-600 font-bold" },
              ].map(({ label, value, color }) => (
                <div key={label} className="flex items-center justify-between text-sm py-1 border-b border-surface-border last:border-0">
                  <span className="text-text-secondary">{label}</span>
                  <span className={color}>{value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Quick actions */}
          <div className="card p-5">
            <SectionHeader title="Quick Actions" />
            <div className="space-y-2">
              {[
                { label: "View IEP Tracker",    icon: FileText,    path: "/sped/iep",        color: "text-primary-600 bg-primary-50" },
                { label: "SpEd Students",        icon: Users,       path: "/sped/students",   color: "text-violet-600  bg-violet-50" },
                { label: "Compliance Report",    icon: ShieldCheck, path: "/sped/compliance", color: "text-emerald-600 bg-emerald-50" },
              ].map(({ label, icon: Icon, path, color }) => (
                <button
                  key={path}
                  onClick={() => navigate(path)}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-surface-muted transition-colors text-left"
                >
                  <span className={cn("w-8 h-8 rounded-lg flex items-center justify-center shrink-0", color)}>
                    <Icon size={15} />
                  </span>
                  <span className="text-sm font-medium text-text-primary">{label}</span>
                  <ChevronRight size={14} className="text-text-muted ml-auto" />
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
