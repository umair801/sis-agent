import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { cn } from "../../utils/cn";
import {
  LayoutDashboard, Users, CalendarCheck, BookOpen, Brain,
  GraduationCap, DollarSign, MessageSquare, FileText,
  ShieldCheck, Settings, LogOut, ChevronLeft, ChevronRight,
} from "lucide-react";

const NAV_BY_ROLE = {
  SuperAdmin: [
    { label: "Dashboard",  icon: LayoutDashboard, to: "/superadmin" },
    { label: "Tenants",    icon: ShieldCheck,     to: "/superadmin/tenants" },
    { label: "Users",      icon: Users,           to: "/superadmin/users" },
    { label: "AI Queries", icon: Brain,           to: "/superadmin/ai" },
    { label: "Settings",   icon: Settings,        to: "/superadmin/settings" },
  ],
  DistrictAdmin: [
    { label: "Dashboard",  icon: LayoutDashboard, to: "/districtadmin" },
    { label: "Students",   icon: GraduationCap,   to: "/districtadmin/students" },
    { label: "Staff",      icon: Users,           to: "/districtadmin/staff" },
    { label: "Budget",     icon: DollarSign,      to: "/districtadmin/budget" },
    { label: "Reports",    icon: FileText,        to: "/districtadmin/reports" },
    { label: "AI Queries", icon: Brain,           to: "/districtadmin/ai" },
    { label: "Settings",   icon: Settings,        to: "/districtadmin/settings" },
  ],
  Principal: [
    { label: "Dashboard",  icon: LayoutDashboard, to: "/principal" },
    { label: "Students",   icon: GraduationCap,   to: "/principal/students" },
    { label: "Attendance", icon: CalendarCheck,   to: "/principal/attendance" },
    { label: "Scheduling", icon: BookOpen,        to: "/principal/scheduling" },
    { label: "Reports",    icon: FileText,        to: "/principal/reports" },
    { label: "AI Queries", icon: Brain,           to: "/principal/ai" },
  ],
  Teacher: [
    { label: "Dashboard",  icon: LayoutDashboard, to: "/teacher" },
    { label: "Attendance", icon: CalendarCheck,   to: "/teacher/attendance" },
    { label: "Gradebook",  icon: BookOpen,        to: "/teacher/gradebook" },
    { label: "Schedule",   icon: CalendarCheck,   to: "/teacher/schedule" },
    { label: "Messages",   icon: MessageSquare,   to: "/teacher/messages" },
    { label: "AI Queries", icon: Brain,           to: "/teacher/ai" },
  ],
  SpEdCoordinator: [
    { label: "Dashboard",   icon: LayoutDashboard, to: "/sped" },
    { label: "IEP Tracker", icon: FileText,        to: "/sped/iep" },
    { label: "Students",    icon: GraduationCap,   to: "/sped/students" },
    { label: "Compliance",  icon: ShieldCheck,     to: "/sped/compliance" },
    { label: "AI Queries",  icon: Brain,           to: "/sped/ai" },
  ],
  Parent: [
    { label: "Dashboard",  icon: LayoutDashboard, to: "/parent" },
    { label: "Grades",     icon: BookOpen,        to: "/parent/grades" },
    { label: "Attendance", icon: CalendarCheck,   to: "/parent/attendance" },
    { label: "Messages",   icon: MessageSquare,   to: "/parent/messages" },
  ],
};

export function Sidebar({ collapsed, onToggle }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const navItems = NAV_BY_ROLE[user?.role] || [];

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <aside
      className={cn(
        "flex flex-col h-screen bg-sidebar-bg shrink-0",
        "transition-all duration-300 ease-in-out",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Logo */}
      <div className={cn(
        "flex items-center h-16 border-b border-white/10",
        collapsed ? "justify-center px-0" : "gap-3 px-4"
      )}>
        <div className="w-9 h-9 rounded-xl bg-primary-500 flex items-center justify-center shrink-0 shadow-lg">
          <GraduationCap size={18} className="text-white" />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <p className="font-display text-sm font-bold text-white leading-none">SIS Portal</p>
            <p className="text-[10px] text-sidebar-muted mt-0.5 truncate">Westlake Unified</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-0.5">
        {navItems.map(({ label, icon: Icon, to }) => (
          <NavLink
            key={to}
            to={to}
            end={to.split("/").length === 2}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-150",
                collapsed && "justify-center",
                isActive
                  ? "bg-primary-600 text-white font-medium shadow-sm"
                  : "text-sidebar-text hover:bg-white/10"
              )
            }
            title={collapsed ? label : undefined}
          >
            <Icon size={17} className="shrink-0" />
            {!collapsed && <span className="truncate">{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-white/10 p-3 space-y-1">
        {!collapsed && user && (
          <div className="px-3 py-2 mb-1 rounded-xl bg-white/5">
            <p className="text-xs font-semibold text-white truncate">
              {user.full_name || user.email}
            </p>
            <p className="text-[10px] text-sidebar-muted">{user.role}</p>
          </div>
        )}
        <button
          onClick={onToggle}
          className={cn(
            "w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-sidebar-text hover:bg-white/10 transition-all",
            collapsed && "justify-center"
          )}
          title={collapsed ? "Expand" : "Collapse"}
        >
          {collapsed
            ? <ChevronRight size={16} className="shrink-0" />
            : <><ChevronLeft size={16} className="shrink-0" /><span>Collapse</span></>
          }
        </button>
        <button
          onClick={handleLogout}
          className={cn(
            "w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-all",
            "text-red-300 hover:bg-red-500/20 hover:text-red-200",
            collapsed && "justify-center"
          )}
          title={collapsed ? "Sign Out" : undefined}
        >
          <LogOut size={16} className="shrink-0" />
          {!collapsed && <span>Sign Out</span>}
        </button>
      </div>
    </aside>
  );
}
