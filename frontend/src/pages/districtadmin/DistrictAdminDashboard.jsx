import { useState, useEffect } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { studentsApi } from "../../api/students";
import { StatCard } from "../../components/ui/StatCard";
import { SectionHeader } from "../../components/ui/SectionHeader";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { Spinner } from "../../components/ui/Spinner";
import {
  GraduationCap, CalendarCheck, DollarSign,
  Users, AlertCircle,
} from "lucide-react";

export default function DistrictAdminDashboard() {
  const { user }                          = useAuth();
  const [students,     setStudents]       = useState([]);
  const [statsLoading, setStatsLoading]   = useState(true);
  const [error,        setError]          = useState(null);

  useEffect(() => {
    studentsApi.list({ limit: 5, skip: 0 })
      .then((res) => {
        const data = res.data;
        setStudents(Array.isArray(data) ? data : (data?.students || []));
      })
      .catch(() => setError("Could not load student data from backend."))
      .finally(() => setStatsLoading(false));
  }, []);

  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long", year: "numeric", month: "long", day: "numeric",
  });

  return (
    <div className="space-y-8 max-w-7xl">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-display text-xl font-bold text-text-primary">District Overview</h2>
          <p className="text-sm text-text-secondary mt-1">{today}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-text-muted">Signed in as</p>
          <p className="text-sm font-semibold text-text-primary">{user?.full_name || user?.email}</p>
          <span className="badge bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200 text-[10px]">{user?.role}</span>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-700 text-sm">
          <AlertCircle size={15} className="shrink-0" />
          {error}
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Students"    value={statsLoading ? null : (students.length > 0 ? `${students.length}+` : "0")} subtitle="Enrolled" icon={GraduationCap} color="primary" loading={statsLoading} />
        <StatCard title="Attendance Rate"   value="94.2%" subtitle="This week"  icon={CalendarCheck} color="green"  trend={1.3} />
        <StatCard title="Budget Used"       value="67%"   subtitle="FY 2024-25" icon={DollarSign}    color="yellow" />
        <StatCard title="Active Staff"      value="42"    subtitle="All roles"  icon={Users}         color="blue" />
      </div>

      {/* Content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Students table — 2 cols */}
        <div className="card p-5 lg:col-span-2">
          <SectionHeader title="Recent Student Enrollments" subtitle="Latest additions to the district" />
          {statsLoading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner className="w-6 h-6" />
            </div>
          ) : students.length === 0 ? (
            <div className="text-center py-12">
              <GraduationCap size={32} className="text-text-muted mx-auto mb-3" />
              <p className="text-sm text-text-muted">No students found.</p>
              <p className="text-xs text-text-muted mt-1">Seed the database to populate this view.</p>
            </div>
          ) : (
            <div className="space-y-1">
              {students.map((s) => (
                <div
                  key={s.id}
                  className="flex items-center justify-between px-4 py-3 rounded-xl hover:bg-surface-muted transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
                      <span className="text-xs font-bold text-primary-700">
                        {(s.first_name?.[0] || "S")}{(s.last_name?.[0] || "")}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-text-primary">
                        {s.first_name} {s.last_name}
                      </p>
                      <p className="text-[10px] text-text-muted">
                        ID: {s.student_id || s.id?.slice(0, 8)} · {s.grade_level || "Grade N/A"}
                      </p>
                    </div>
                  </div>
                  <StatusBadge status={s.enrollment_status || "active"} />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right sidebar */}
        <div className="space-y-4">
          <div className="card p-5">
            <SectionHeader title="Active Alerts" />
            <div className="space-y-2">
              {[
                { label: "IEP deadlines this week", count: 3, bg: "bg-red-50    border-red-100",    text: "text-red-600    font-bold" },
                { label: "Unexcused absences today", count: 7, bg: "bg-amber-50  border-amber-100",  text: "text-amber-600  font-bold" },
                { label: "Scheduling conflicts",    count: 2, bg: "bg-primary-50 border-primary-100", text: "text-primary-600 font-bold" },
              ].map((a) => (
                <div key={a.label} className={`flex items-center justify-between px-3 py-2.5 rounded-xl border ${a.bg}`}>
                  <span className="text-xs text-text-secondary">{a.label}</span>
                  <span className={`text-sm ${a.text}`}>{a.count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card p-5">
            <SectionHeader title="Academic Year" />
            <div className="space-y-2.5">
              {[
                { label: "Year",     value: "2024-25" },
                { label: "School",   value: "Westlake High" },
                { label: "Periods",  value: "6" },
                { label: "Courses",  value: "8" },
                { label: "Rooms",    value: "5" },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between items-center text-sm">
                  <span className="text-text-secondary">{label}</span>
                  <span className="font-semibold text-text-primary">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
