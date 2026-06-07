import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { studentsApi } from "../../api/students";
import { schedulingApi } from "../../api/scheduling";
import { StatCard } from "../../components/ui/StatCard";
import { SectionHeader } from "../../components/ui/SectionHeader";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { Spinner } from "../../components/ui/Spinner";
import {
  CalendarCheck, BookOpen, Users, Clock,
  ChevronRight, CheckCircle, AlertCircle,
} from "lucide-react";

const TODAY = new Date().toLocaleDateString("en-US", {
  weekday: "long", month: "long", day: "numeric",
});

const PERIOD_TIMES = {
  1: "8:00 - 8:55 AM",
  2: "9:00 - 9:55 AM",
  3: "10:00 - 10:55 AM",
  4: "11:00 - 11:55 AM",
  5: "12:00 - 12:55 PM",
  6: "1:00 - 1:55 PM",
};

export default function TeacherDashboard() {
  const { user }                        = useAuth();
  const navigate                        = useNavigate();
  const [sections,  setSections]        = useState([]);
  const [students,  setStudents]        = useState([]);
  const [loading,   setLoading]         = useState(true);
  const [error,     setError]           = useState(null);

  useEffect(() => {
    Promise.allSettled([
      schedulingApi.listSections({ limit: 20 }),
      studentsApi.list({ limit: 5 }),
    ]).then(([secRes, stuRes]) => {
      if (secRes.status === "fulfilled") {
        const d = secRes.value.data;
        setSections(Array.isArray(d) ? d : (d?.sections || d?.items || []));
      }
      if (stuRes.status === "fulfilled") {
        const d = stuRes.value.data;
        setStudents(Array.isArray(d) ? d : (d?.students || d?.items || []));
      }
    }).catch(() => setError("Could not load data."))
      .finally(() => setLoading(false));
  }, []);

  const now        = new Date();
  const currentHr  = now.getHours() + now.getMinutes() / 60;
  // Periods run 8-15; map to period number
  const currentPeriod = currentHr >= 8 && currentHr < 15
    ? Math.min(6, Math.floor(currentHr - 8) + 1)
    : null;

  return (
    <div className="space-y-7 max-w-5xl">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-display text-xl font-bold text-text-primary">
            Good {currentHr < 12 ? "morning" : currentHr < 17 ? "afternoon" : "evening"},{" "}
            {user?.full_name?.split(" ")[0] || "Teacher"}
          </h2>
          <p className="text-sm text-text-secondary mt-1">{TODAY}</p>
        </div>
        {currentPeriod && (
          <div className="text-right">
            <p className="text-xs text-text-muted">Current period</p>
            <p className="text-lg font-display font-bold text-primary-600">Period {currentPeriod}</p>
            <p className="text-xs text-text-muted">{PERIOD_TIMES[currentPeriod]}</p>
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-700 text-sm">
          <AlertCircle size={15} className="shrink-0" />
          {error} Data shown may be incomplete.
        </div>
      )}

      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard
          title="My Sections"
          value={loading ? null : sections.length || "0"}
          subtitle="This semester"
          icon={BookOpen}
          color="primary"
          loading={loading}
        />
        <StatCard
          title="Students"
          value={loading ? null : students.length > 0 ? `${students.length}+` : "0"}
          subtitle="Enrolled"
          icon={Users}
          color="blue"
          loading={loading}
        />
        <StatCard
          title="Attendance Due"
          value={loading ? null : sections.length || "0"}
          subtitle="Today"
          icon={CalendarCheck}
          color="yellow"
          loading={loading}
        />
        <StatCard
          title="Current Period"
          value={currentPeriod ? `P${currentPeriod}` : "--"}
          subtitle={currentPeriod ? PERIOD_TIMES[currentPeriod] : "No class now"}
          icon={Clock}
          color="green"
        />
      </div>

      {/* Quick action — Take Attendance */}
      <div
        onClick={() => navigate("/teacher/attendance")}
        className="card-hover p-5 cursor-pointer flex items-center justify-between
                   bg-gradient-to-r from-primary-600 to-primary-700 border-primary-500
                   hover:from-primary-700 hover:to-primary-800"
        style={{ color: "white" }}
      >
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center">
            <CalendarCheck size={22} className="text-white" />
          </div>
          <div>
            <p className="font-semibold text-white text-base">Take Attendance</p>
            <p className="text-primary-200 text-sm">
              {sections.length > 0
                ? `${sections.length} section${sections.length > 1 ? "s" : ""} need attendance today`
                : "Mark today's attendance for your classes"}
            </p>
          </div>
        </div>
        <ChevronRight size={20} className="text-white/70" />
      </div>

      {/* My Sections */}
      <div className="card p-5">
        <SectionHeader
          title="My Sections"
          subtitle="Your assigned classes this semester"
          action={() => navigate("/teacher/schedule")}
          actionLabel="Full schedule"
        />
        {loading ? (
          <div className="flex items-center justify-center py-10">
            <Spinner className="w-6 h-6" />
          </div>
        ) : sections.length === 0 ? (
          <div className="text-center py-10">
            <BookOpen size={28} className="text-text-muted mx-auto mb-2" />
            <p className="text-sm text-text-muted">No sections assigned yet.</p>
          </div>
        ) : (
          <div className="divide-y divide-surface-border">
            {sections.slice(0, 6).map((sec) => (
              <div
                key={sec.id}
                className="flex items-center justify-between py-3.5 hover:bg-surface-muted -mx-2 px-2 rounded-xl transition-colors cursor-pointer"
                onClick={() => navigate("/teacher/attendance")}
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-primary-50 flex items-center justify-center shrink-0">
                    <span className="text-xs font-bold text-primary-700">
                      P{sec.period_number || sec.period || "?"}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-text-primary">
                      {sec.course_name || sec.course_code || `Section ${sec.section_number || sec.id?.slice(0,4)}`}
                    </p>
                    <p className="text-xs text-text-muted">
                      {sec.room_name || sec.room || "Room TBD"} · Period {sec.period_number || sec.period || "?"}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-text-muted">
                    {sec.student_count ?? sec.enrolled ?? "--"} students
                  </span>
                  <StatusBadge status={sec.is_active ? "active" : "inactive"} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent students */}
      <div className="card p-5">
        <SectionHeader
          title="Recent Students"
          subtitle="Students in your classes"
          action={() => navigate("/teacher/gradebook")}
          actionLabel="Open gradebook"
        />
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Spinner className="w-5 h-5" />
          </div>
        ) : students.length === 0 ? (
          <p className="text-sm text-text-muted text-center py-8">No student data available.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {students.map((s) => (
              <div key={s.id} className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-surface-muted transition-colors">
                <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
                  <span className="text-xs font-bold text-primary-700">
                    {(s.first_name?.[0] || "S")}{(s.last_name?.[0] || "")}
                  </span>
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-text-primary truncate">
                    {s.first_name} {s.last_name}
                  </p>
                  <p className="text-[10px] text-text-muted">{s.grade_level || "Grade N/A"}</p>
                </div>
                <CheckCircle size={14} className="text-emerald-500 shrink-0 ml-auto" />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
