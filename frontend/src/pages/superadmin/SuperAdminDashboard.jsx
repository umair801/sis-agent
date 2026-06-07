import { useState, useEffect } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { studentsApi } from "../../api/students";
import { StatCard } from "../../components/ui/StatCard";
import { SectionHeader } from "../../components/ui/SectionHeader";
import { StatusBadge } from "../../components/ui/StatusBadge";
import {
  Users, GraduationCap, ShieldCheck,
  Database, CheckCircle, AlertTriangle, Clock,
} from "lucide-react";

const MOCK_TENANTS = [
  { id: 1, name: "Westlake Unified", slug: "westlake", status: "active", since: "2024-01" },
];

const MOCK_ACTIVITY = [
  { id: 1, event: "New student enrolled",           user: "admin@westlake.edu",     time: "2 min ago",  type: "info" },
  { id: 2, event: "IEP compliance alert triggered", user: "system",                 time: "14 min ago", type: "warn" },
  { id: 3, event: "Attendance report generated",    user: "principal@westlake.edu", time: "1 hr ago",   type: "info" },
  { id: 4, event: "Budget forecast updated",        user: "admin@westlake.edu",     time: "3 hr ago",   type: "info" },
  { id: 5, event: "SpEd deadline missed",           user: "system",                 time: "5 hr ago",   type: "error" },
];

export default function SuperAdminDashboard() {
  const { user }                          = useAuth();
  const [studentCount, setStudentCount]   = useState(null);
  const [loading, setLoading]             = useState(true);

  useEffect(() => {
    studentsApi.list({ limit: 1 })
      .then((res) => {
        const data  = res.data;
        const total = data?.total ?? (Array.isArray(data) ? data.length : null);
        setStudentCount(total);
      })
      .catch(() => setStudentCount("--"))
      .finally(() => setLoading(false));
  }, []);

  const typeIcon = {
    info:  <CheckCircle  size={14} className="text-emerald-500 shrink-0" />,
    warn:  <AlertTriangle size={14} className="text-amber-500 shrink-0" />,
    error: <AlertTriangle size={14} className="text-red-500 shrink-0" />,
  };

  return (
    <div className="space-y-8 max-w-7xl">
      {/* Welcome */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-xl font-bold text-text-primary">
            Welcome back, {user?.full_name?.split(" ")[0] || "Admin"}
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            System overview for Westlake Unified School District
          </p>
        </div>
        <span className="badge bg-primary-50 text-primary-700 ring-1 ring-primary-200 text-xs font-semibold px-3 py-1.5">
          Super Admin
        </span>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Students"   value={studentCount} subtitle="Westlake Unified" icon={GraduationCap} color="primary" loading={loading} />
        <StatCard title="Active Tenants"   value="1"            subtitle="Production"        icon={Database}      color="blue" />
        <StatCard title="System Users"     value="6"            subtitle="All roles"         icon={Users}         color="purple" />
        <StatCard title="Compliance Score" value="94%"          subtitle="IDEA / FERPA"      icon={ShieldCheck}   color="green" trend={2} />
      </div>

      {/* Two-column */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tenant List */}
        <div className="card p-5">
          <SectionHeader title="Active Tenants" subtitle="Registered school districts" />
          <div className="space-y-2">
            {MOCK_TENANTS.map((t) => (
              <div key={t.id} className="flex items-center justify-between px-4 py-3 rounded-xl bg-surface hover:bg-surface-muted transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-primary-50 flex items-center justify-center">
                    <GraduationCap size={15} className="text-primary-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-text-primary">{t.name}</p>
                    <p className="text-[10px] text-text-muted">/{t.slug} · since {t.since}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-text-muted">{loading ? "..." : studentCount} students</span>
                  <StatusBadge status={t.status} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Activity Feed */}
        <div className="card p-5">
          <SectionHeader title="Recent Activity" subtitle="System-wide event log" />
          <div className="space-y-1">
            {MOCK_ACTIVITY.map((a) => (
              <div key={a.id} className="flex items-start gap-3 px-3 py-2.5 rounded-xl hover:bg-surface-muted transition-colors">
                <span className="mt-0.5">{typeIcon[a.type]}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-text-primary truncate">{a.event}</p>
                  <p className="text-[10px] text-text-muted">{a.user}</p>
                </div>
                <span className="text-[10px] text-text-muted whitespace-nowrap flex items-center gap-1">
                  <Clock size={9} />{a.time}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* System Health */}
      <div className="card p-5">
        <SectionHeader title="System Health" subtitle="Backend service status" />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "FastAPI Backend", status: "Operational" },
            { label: "Supabase DB",     status: "Operational" },
            { label: "Claude AI",       status: "Operational" },
            { label: "Pinecone RAG",    status: "Operational" },
          ].map((s) => (
            <div key={s.label} className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-emerald-50 border border-emerald-100">
              <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
              <div>
                <p className="text-xs font-semibold text-text-primary">{s.label}</p>
                <p className="text-[10px] text-emerald-600">{s.status}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
