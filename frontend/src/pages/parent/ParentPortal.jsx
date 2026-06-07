import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { studentsApi } from "../../api/students";
import { attendanceApi } from "../../api/attendance";
import { StatCard } from "../../components/ui/StatCard";
import { SectionHeader } from "../../components/ui/SectionHeader";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { Spinner } from "../../components/ui/Spinner";
import { cn } from "../../utils/cn";
import {
  BookOpen, CalendarCheck, MessageSquare, Star,
  TrendingUp, TrendingDown, ChevronRight, Bell,
  CheckCircle, AlertCircle, Clock,
} from "lucide-react";

// Mock child data — in production this would come from the parent-student link table
const MOCK_CHILD = {
  name:         "Emma Rodriguez",
  grade:        "Grade 10",
  student_id:   "WHS-2024-0042",
  school:       "Westlake High School",
  homeroom:     "Ms. Thompson - Room 102",
  gpa:          3.7,
  attendance:   94.2,
};

const MOCK_GRADES = [
  { subject: "English 10",      grade: "A",  score: 94, teacher: "Ms. Thompson",  trend: "up"     },
  { subject: "Mathematics 10",  grade: "B+", score: 88, teacher: "Mr. Garcia",    trend: "up"     },
  { subject: "Science 10",      grade: "A-", score: 91, teacher: "Ms. Patel",     trend: "neutral" },
  { subject: "History 10",      grade: "B",  score: 85, teacher: "Mr. Williams",  trend: "down"   },
  { subject: "Physical Ed",     grade: "A",  score: 97, teacher: "Coach Davis",   trend: "up"     },
];

const MOCK_ATTENDANCE = [
  { date: "Jun 6, 2026",  day: "Friday",    status: "present" },
  { date: "Jun 5, 2026",  day: "Thursday",  status: "present" },
  { date: "Jun 4, 2026",  day: "Wednesday", status: "late"    },
  { date: "Jun 3, 2026",  day: "Tuesday",   status: "present" },
  { date: "Jun 2, 2026",  day: "Monday",    status: "present" },
  { date: "May 30, 2026", day: "Friday",    status: "absent"  },
  { date: "May 29, 2026", day: "Thursday",  status: "present" },
];

const MOCK_ANNOUNCEMENTS = [
  { id: 1, title: "End of Year Ceremonies",       body: "Graduation ceremonies scheduled for June 20th at 10 AM in the main gymnasium.",  date: "Jun 5", type: "info"    },
  { id: 2, title: "Final Exam Schedule Released", body: "Final exams begin June 15. Please review the schedule on the school website.",   date: "Jun 3", type: "alert"   },
  { id: 3, title: "Summer School Registration",   body: "Registration for summer school programs is now open through June 10th.",         date: "May 30", type: "info"   },
];

const GRADE_COLORS = {
  "A":  "text-emerald-700 bg-emerald-50 ring-emerald-200",
  "A-": "text-emerald-700 bg-emerald-50 ring-emerald-200",
  "B+": "text-sky-700     bg-sky-50     ring-sky-200",
  "B":  "text-sky-700     bg-sky-50     ring-sky-200",
  "B-": "text-sky-700     bg-sky-50     ring-sky-200",
  "C+": "text-amber-700   bg-amber-50   ring-amber-200",
  "C":  "text-amber-700   bg-amber-50   ring-amber-200",
  "D":  "text-red-700     bg-red-50     ring-red-200",
  "F":  "text-red-700     bg-red-50     ring-red-200",
};

export default function ParentPortal() {
  const { user }                  = useAuth();
  const navigate                  = useNavigate();
  const [loading, setLoading]     = useState(false);
  const [activeTab, setActiveTab] = useState("overview");

  const presentCount = MOCK_ATTENDANCE.filter(a => a.status === "present").length;
  const attendRate   = ((presentCount / MOCK_ATTENDANCE.length) * 100).toFixed(0);

  return (
    <div className="space-y-6 max-w-4xl">

      {/* Child info card */}
      <div className="card p-5 flex items-center gap-5">
        <div className="w-14 h-14 rounded-2xl bg-primary-100 flex items-center justify-center shrink-0">
          <span className="text-xl font-display font-bold text-primary-700">
            {MOCK_CHILD.name.split(" ").map(n => n[0]).join("")}
          </span>
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="font-display text-lg font-bold text-text-primary">{MOCK_CHILD.name}</h2>
          <p className="text-sm text-text-secondary">
            {MOCK_CHILD.grade} · {MOCK_CHILD.school}
          </p>
          <p className="text-xs text-text-muted mt-0.5">
            ID: {MOCK_CHILD.student_id} · {MOCK_CHILD.homeroom}
          </p>
        </div>
        <div className="text-right shrink-0">
          <p className="text-2xl font-display font-bold text-primary-600">{MOCK_CHILD.gpa}</p>
          <p className="text-xs text-text-muted">Current GPA</p>
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard title="GPA"             value={MOCK_CHILD.gpa}       subtitle="This semester" icon={Star}          color="primary" trend={0.2} />
        <StatCard title="Attendance"      value={`${MOCK_CHILD.attendance}%`} subtitle="This year"   icon={CalendarCheck} color="green"  />
        <StatCard title="Subjects"        value={MOCK_GRADES.length}   subtitle="Enrolled"      icon={BookOpen}      color="blue"    />
        <StatCard title="Unread Messages" value="2"                    subtitle="From school"   icon={MessageSquare} color="yellow"  />
      </div>

      {/* Tab navigation */}
      <div className="flex gap-1 p-1 bg-surface-muted rounded-xl w-fit">
        {[
          { id: "overview",     label: "Overview"    },
          { id: "grades",       label: "Grades"      },
          { id: "attendance",   label: "Attendance"  },
          { id: "messages",     label: "Messages"    },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "px-4 py-2 rounded-lg text-sm font-medium transition-all",
              activeTab === tab.id
                ? "bg-white text-text-primary shadow-sm"
                : "text-text-secondary hover:text-text-primary"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Overview tab */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {/* Recent grades */}
          <div className="card p-5">
            <SectionHeader
              title="Recent Grades"
              action={() => setActiveTab("grades")}
              actionLabel="All grades"
            />
            <div className="space-y-2.5">
              {MOCK_GRADES.slice(0, 4).map((g) => (
                <div key={g.subject} className="flex items-center justify-between">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-text-primary truncate">{g.subject}</p>
                    <p className="text-[10px] text-text-muted">{g.teacher}</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {g.trend === "up"   && <TrendingUp   size={13} className="text-emerald-500" />}
                    {g.trend === "down" && <TrendingDown  size={13} className="text-red-500" />}
                    <span className={cn("badge ring-1 font-bold text-xs", GRADE_COLORS[g.grade] || "bg-gray-50 text-gray-700 ring-gray-200")}>
                      {g.grade}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent attendance */}
          <div className="card p-5">
            <SectionHeader
              title="Recent Attendance"
              action={() => setActiveTab("attendance")}
              actionLabel="Full record"
            />
            <div className="space-y-2">
              {MOCK_ATTENDANCE.slice(0, 5).map((a, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-text-primary">{a.day}</p>
                    <p className="text-[10px] text-text-muted">{a.date}</p>
                  </div>
                  <StatusBadge status={a.status} />
                </div>
              ))}
            </div>
          </div>

          {/* Announcements */}
          <div className="card p-5 sm:col-span-2">
            <SectionHeader title="School Announcements" subtitle="Latest from Westlake Unified" />
            <div className="space-y-3">
              {MOCK_ANNOUNCEMENTS.map((a) => (
                <div key={a.id} className={cn(
                  "flex gap-3 px-4 py-3 rounded-xl border",
                  a.type === "alert"
                    ? "bg-amber-50 border-amber-200"
                    : "bg-surface border-surface-border"
                )}>
                  <Bell size={15} className={cn("shrink-0 mt-0.5", a.type === "alert" ? "text-amber-600" : "text-primary-500")} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-text-primary">{a.title}</p>
                    <p className="text-xs text-text-secondary mt-0.5">{a.body}</p>
                  </div>
                  <span className="text-[10px] text-text-muted shrink-0">{a.date}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Grades tab */}
      {activeTab === "grades" && (
        <div className="card p-5">
          <SectionHeader title="Academic Report" subtitle={`${MOCK_CHILD.name} · ${MOCK_CHILD.grade}`} />
          <div className="space-y-3">
            {MOCK_GRADES.map((g) => (
              <div key={g.subject} className="flex items-center gap-4 px-4 py-3.5 rounded-xl bg-surface hover:bg-surface-muted transition-colors">
                <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ring-1 font-display font-bold text-sm", GRADE_COLORS[g.grade] || "bg-gray-50 ring-gray-200")}>
                  {g.grade}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-text-primary">{g.subject}</p>
                  <p className="text-xs text-text-muted">{g.teacher}</p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-lg font-display font-bold text-text-primary">{g.score}%</p>
                  <div className="flex items-center justify-end gap-1">
                    {g.trend === "up"      && <TrendingUp   size={12} className="text-emerald-500" />}
                    {g.trend === "down"    && <TrendingDown  size={12} className="text-red-500" />}
                    <p className="text-[10px] text-text-muted">
                      {g.trend === "up" ? "Improving" : g.trend === "down" ? "Declining" : "Stable"}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          {/* GPA summary */}
          <div className="mt-4 pt-4 border-t border-surface-border flex items-center justify-between">
            <p className="text-sm text-text-secondary font-medium">Current GPA</p>
            <p className="text-xl font-display font-bold text-primary-600">{MOCK_CHILD.gpa} / 4.0</p>
          </div>
        </div>
      )}

      {/* Attendance tab */}
      {activeTab === "attendance" && (
        <div className="card p-5">
          <SectionHeader
            title="Attendance Record"
            subtitle={`${presentCount} of ${MOCK_ATTENDANCE.length} days present (${attendRate}%)`}
          />
          {/* Summary row */}
          <div className="grid grid-cols-3 gap-3 mb-5">
            {[
              { label: "Present", count: MOCK_ATTENDANCE.filter(a => a.status === "present").length, color: "bg-emerald-50 text-emerald-700 border-emerald-200" },
              { label: "Late",    count: MOCK_ATTENDANCE.filter(a => a.status === "late").length,    color: "bg-amber-50   text-amber-700   border-amber-200"   },
              { label: "Absent",  count: MOCK_ATTENDANCE.filter(a => a.status === "absent").length,  color: "bg-red-50     text-red-700     border-red-200"     },
            ].map(({ label, count, color }) => (
              <div key={label} className={cn("text-center py-3 rounded-xl border font-medium", color)}>
                <p className="text-2xl font-display font-bold">{count}</p>
                <p className="text-xs mt-0.5">{label}</p>
              </div>
            ))}
          </div>
          <div className="space-y-2">
            {MOCK_ATTENDANCE.map((a, i) => (
              <div key={i} className="flex items-center justify-between px-4 py-3 rounded-xl hover:bg-surface-muted transition-colors">
                <div className="flex items-center gap-3">
                  {a.status === "present" && <CheckCircle size={16} className="text-emerald-500 shrink-0" />}
                  {a.status === "absent"  && <AlertCircle size={16} className="text-red-500    shrink-0" />}
                  {a.status === "late"    && <Clock       size={16} className="text-amber-500  shrink-0" />}
                  <div>
                    <p className="text-sm font-medium text-text-primary">{a.day}</p>
                    <p className="text-xs text-text-muted">{a.date}</p>
                  </div>
                </div>
                <StatusBadge status={a.status} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Messages tab */}
      {activeTab === "messages" && (
        <div className="card p-5">
          <SectionHeader title="Messages" subtitle="Communication from school staff" />
          <div className="space-y-3">
            {[
              { from: "Ms. Thompson",  role: "English Teacher",    msg: "Emma is doing excellent work on her final project. Very proud of her progress!", time: "2 hours ago",  unread: true  },
              { from: "Mr. Garcia",    role: "Math Teacher",       msg: "Reminder that the final math exam is on June 15. Please ensure Emma reviews chapters 8-12.", time: "Yesterday",   unread: true  },
              { from: "Principal Johnson", role: "Principal",      msg: "End of year report cards will be available online from June 25th onwards.",            time: "Jun 3",       unread: false },
            ].map((m, i) => (
              <div key={i} className={cn(
                "flex gap-4 px-4 py-4 rounded-xl border transition-colors cursor-pointer hover:bg-surface-muted",
                m.unread ? "border-primary-200 bg-primary-50/40" : "border-surface-border bg-white"
              )}>
                <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
                  <span className="text-xs font-bold text-primary-700">
                    {m.from.split(" ").map(n => n[0]).join("").slice(0, 2)}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-text-primary">{m.from}</p>
                    <span className="text-[10px] text-text-muted shrink-0">{m.time}</span>
                  </div>
                  <p className="text-[10px] text-text-muted mb-1">{m.role}</p>
                  <p className="text-sm text-text-secondary line-clamp-2">{m.msg}</p>
                </div>
                {m.unread && <span className="w-2 h-2 rounded-full bg-primary-500 shrink-0 mt-1.5" />}
              </div>
            ))}
          </div>
          {/* Reply box */}
          <div className="mt-5 pt-4 border-t border-surface-border">
            <p className="text-xs font-semibold text-text-secondary mb-2 uppercase tracking-wider">Send a message</p>
            <textarea
              rows={3}
              placeholder="Type your message to school staff..."
              className="w-full px-4 py-3 bg-white border border-surface-border rounded-xl text-sm
                         focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100
                         resize-none placeholder-gray-400"
              style={{ color: "#111827" }}
            />
            <button className="btn-primary text-sm mt-2 px-5 py-2.5">
              Send Message
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
