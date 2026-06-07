import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { studentsApi } from "../../api/students";
import { schedulingApi } from "../../api/scheduling";
import { attendanceApi } from "../../api/attendance";
import { StatCard } from "../../components/ui/StatCard";
import { SectionHeader } from "../../components/ui/SectionHeader";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { Spinner } from "../../components/ui/Spinner";
import { cn } from "../../utils/cn";
import {
  GraduationCap, CalendarCheck, BookOpen, Users,
  TrendingUp, TrendingDown, AlertCircle, ChevronRight,
  BarChart2, FileText, ShieldCheck,
} from "lucide-react";

// Mock attendance trend data for the chart
const ATTENDANCE_TREND = [
  { day: "Mon", rate: 96.2 },
  { day: "Tue", rate: 94.8 },
  { day: "Wed", rate: 95.5 },
  { day: "Thu", rate: 93.1 },
  { day: "Fri", rate: 91.4 },
  { day: "Mon", rate: 95.8 },
  { day: "Tue", rate: 94.2 },
];

const GRADE_BREAKDOWN = [
  { grade: "Grade 9",  enrolled: 124, present: 118, rate: 95.2 },
  { grade: "Grade 10", enrolled: 118, present: 110, rate: 93.2 },
  { grade: "Grade 11", enrolled: 112, present: 108, rate: 96.4 },
  { grade: "Grade 12", enrolled: 98,  present: 90,  rate: 91.8 },
];

const MAX_BAR = Math.max(...ATTENDANCE_TREND.map(d => d.rate));

export default function PrincipalDashboard() {
  const { user }                        = useAuth();
  const navigate                        = useNavigate();
  const [students,  setStudents]        = useState([]);
  const [sections,  setSections]        = useState([]);
  const [loading,   setLoading]         = useState(true);
  const [error,     setError]           = useState(null);

  useEffect(() => {
    Promise.allSettled([
      studentsApi.list({ limit: 10 }),
      schedulingApi.listSections({ limit: 20 }),
    ]).then(([stuRes, secRes]) => {
      if (stuRes.status === "fulfilled") {
        const d = stuRes.value.data;
        setStudents(Array.isArray(d) ? d : (d?.students || d?.items || []));
      }
      if (secRes.status === "fulfilled") {
        const d = secRes.value.data;
        setSections(Array.isArray(d) ? d : (d?.sections || d?.items || []));
      }
    }).catch(() => setError("Some data could not be loaded."))
      .finally(() => setLoading(false));
  }, []);

  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long", month: "long", day: "numeric", year: "numeric",
  });

  const avgAttendance = (
    ATTENDANCE_TREND.reduce((s, d) => s + d.rate, 0) / ATTENDANCE_TREND.length
  ).toFixed(1);

  const totalEnrolled = GRADE_BREAKDOWN.reduce((s, g) => s + g.enrolled, 0);

  return (
    <div className="space-y-7 max-w-7xl">

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-display text-xl font-bold text-text-primary">
            School Analytics
          </h2>
          <p className="text-sm text-text-secondary mt-1">{today}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-text-muted">Principal</p>
          <p className="text-sm font-semibold text-text-primary">{user?.full_name || "Robert Johnson"}</p>
          <p className="text-xs text-text-muted">Westlake High School</p>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-700 text-sm">
          <AlertCircle size={15} className="shrink-0" /> {error}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Enrollment"
          value={loading ? null : (students.length > 0 ? `${totalEnrolled}` : "452")}
          subtitle="Active students"
          icon={GraduationCap}
          color="primary"
          loading={loading}
        />
        <StatCard
          title="Avg Attendance"
          value={`${avgAttendance}%`}
          subtitle="This week"
          icon={CalendarCheck}
          color="green"
          trend={0.8}
        />
        <StatCard
          title="Active Sections"
          value={loading ? null : (sections.length || "18")}
          subtitle="This semester"
          icon={BookOpen}
          color="blue"
          loading={loading}
        />
        <StatCard
          title="Teaching Staff"
          value="24"
          subtitle="Across all subjects"
          icon={Users}
          color="purple"
        />
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Attendance trend chart — 2 cols */}
        <div className="card p-5 lg:col-span-2">
          <SectionHeader
            title="Attendance Trend"
            subtitle="Last 7 school days"
            action={() => navigate("/principal/attendance")}
            actionLabel="Full report"
          />
          <div className="flex items-end gap-2 h-36 mt-2">
            {ATTENDANCE_TREND.map((d, i) => {
              const height = ((d.rate - 88) / (100 - 88)) * 100;
              const color  = d.rate >= 95 ? "bg-emerald-400" : d.rate >= 92 ? "bg-amber-400" : "bg-red-400";
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-1.5">
                  <span className="text-[9px] font-semibold text-text-muted">{d.rate}%</span>
                  <div className="w-full rounded-t-lg transition-all" style={{ height: `${height}%`, minHeight: "8px" }}>
                    <div className={cn("w-full h-full rounded-t-lg", color)} />
                  </div>
                  <span className="text-[10px] text-text-muted">{d.day}</span>
                </div>
              );
            })}
          </div>
          {/* Legend */}
          <div className="flex gap-4 mt-3 pt-3 border-t border-surface-border">
            {[
              { color: "bg-emerald-400", label: "95%+ (Excellent)" },
              { color: "bg-amber-400",   label: "92-95% (Good)" },
              { color: "bg-red-400",     label: "Below 92% (Concern)" },
            ].map(({ color, label }) => (
              <div key={label} className="flex items-center gap-1.5">
                <span className={cn("w-2.5 h-2.5 rounded-sm", color)} />
                <span className="text-[10px] text-text-muted">{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Alerts sidebar — 1 col */}
        <div className="space-y-4">
          <div className="card p-5">
            <SectionHeader title="Action Required" />
            <div className="space-y-2">
              {[
                { label: "Students below 90% attendance", count: 8,  color: "bg-red-50    border-red-100    text-red-600"    },
                { label: "IEP reviews due this week",     count: 2,  color: "bg-amber-50  border-amber-100  text-amber-600"  },
                { label: "Scheduling conflicts",          count: 3,  color: "bg-primary-50 border-primary-100 text-primary-600" },
                { label: "Unexcused absences today",      count: 12, color: "bg-red-50    border-red-100    text-red-600"    },
              ].map((a) => (
                <div key={a.label} className={cn("flex items-center justify-between px-3 py-2.5 rounded-xl border", a.color)}>
                  <span className="text-xs">{a.label}</span>
                  <span className="text-sm font-bold ml-2 shrink-0">{a.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Grade breakdown table */}
      <div className="card p-5">
        <SectionHeader
          title="Enrollment and Attendance by Grade"
          subtitle="Current academic year"
          action={() => navigate("/principal/reports")}
          actionLabel="Download report"
        />
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-border">
                {["Grade Level", "Enrolled", "Present Today", "Attendance Rate", "Trend", "Status"].map((h) => (
                  <th key={h} className="text-left text-xs font-semibold text-text-secondary uppercase tracking-wider pb-3 pr-4">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border">
              {GRADE_BREAKDOWN.map((g) => {
                const trend = g.rate >= 95 ? "up" : g.rate >= 92 ? "neutral" : "down";
                return (
                  <tr key={g.grade} className="hover:bg-surface-muted transition-colors">
                    <td className="py-3 pr-4 font-semibold text-text-primary">{g.grade}</td>
                    <td className="py-3 pr-4 text-text-secondary">{g.enrolled}</td>
                    <td className="py-3 pr-4 text-text-secondary">{g.present}</td>
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-surface-muted rounded-full max-w-20">
                          <div
                            className={cn("h-1.5 rounded-full", g.rate >= 95 ? "bg-emerald-400" : g.rate >= 92 ? "bg-amber-400" : "bg-red-400")}
                            style={{ width: `${g.rate}%` }}
                          />
                        </div>
                        <span className="font-semibold text-text-primary">{g.rate}%</span>
                      </div>
                    </td>
                    <td className="py-3 pr-4">
                      {trend === "up"
                        ? <TrendingUp  size={15} className="text-emerald-500" />
                        : trend === "down"
                        ? <TrendingDown size={15} className="text-red-500" />
                        : <span className="text-text-muted text-xs">—</span>
                      }
                    </td>
                    <td className="py-3">
                      <StatusBadge
                        status={g.rate >= 95 ? "active" : g.rate >= 92 ? "pending" : "absent"}
                        label={g.rate >= 95 ? "Excellent" : g.rate >= 92 ? "Good" : "Concern"}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { label: "Attendance Reports",  icon: CalendarCheck, path: "/principal/attendance", color: "text-emerald-600 bg-emerald-50", desc: "Daily and period-level reports" },
          { label: "Scheduling Overview", icon: BookOpen,       path: "/principal/scheduling", color: "text-primary-600 bg-primary-50", desc: "Sections, rooms, conflicts"    },
          { label: "Student Directory",   icon: GraduationCap,  path: "/principal/students",   color: "text-violet-600  bg-violet-50",  desc: "All enrolled students"         },
        ].map(({ label, icon: Icon, path, color, desc }) => (
          <button
            key={path}
            onClick={() => navigate(path)}
            className="card-hover p-5 text-left flex items-center gap-4 w-full"
          >
            <span className={cn("w-11 h-11 rounded-2xl flex items-center justify-center shrink-0", color)}>
              <Icon size={20} />
            </span>
            <div className="min-w-0">
              <p className="font-semibold text-text-primary text-sm">{label}</p>
              <p className="text-xs text-text-muted mt-0.5 truncate">{desc}</p>
            </div>
            <ChevronRight size={15} className="text-text-muted ml-auto shrink-0" />
          </button>
        ))}
      </div>
    </div>
  );
}
