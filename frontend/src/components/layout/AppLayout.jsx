import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { AiQueryPanel } from "../ai/AiQueryPanel";

const TITLE_MAP = {
  "/superadmin":              "Super Admin",
  "/superadmin/tenants":      "Tenants",
  "/superadmin/users":        "Users",
  "/superadmin/ai":           "AI Queries",
  "/superadmin/settings":     "Settings",
  "/districtadmin":           "District Dashboard",
  "/districtadmin/students":  "Students",
  "/districtadmin/budget":    "Budget",
  "/districtadmin/reports":   "Reports",
  "/districtadmin/ai":        "AI Queries",
  "/districtadmin/settings":  "Settings",
  "/principal":               "Principal Dashboard",
  "/principal/students":      "Students",
  "/principal/attendance":    "Attendance Overview",
  "/principal/scheduling":    "Scheduling",
  "/principal/reports":       "Reports",
  "/teacher":                 "Teacher Dashboard",
  "/teacher/attendance":      "Attendance Entry",
  "/teacher/gradebook":       "Gradebook",
  "/teacher/schedule":        "My Schedule",
  "/teacher/messages":        "Messages",
  "/sped":                    "SpEd Dashboard",
  "/sped/iep":                "IEP Tracker",
  "/sped/students":           "SpEd Students",
  "/sped/compliance":         "Compliance",
  "/sped/ai":                 "AI Queries",
  "/parent":                  "Parent Portal",
  "/parent/grades":           "My Child's Grades",
  "/parent/attendance":       "Attendance Record",
  "/parent/messages":         "Messages",
};

export function AppLayout() {
  const [collapsed,  setCollapsed]  = useState(false);
  const [aiOpen,     setAiOpen]     = useState(false);
  const location = useLocation();
  const title    = TITLE_MAP[location.pathname] || "Dashboard";

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <TopBar title={title} onAiOpen={() => setAiOpen(true)} />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
      <AiQueryPanel isOpen={aiOpen} onClose={() => setAiOpen(false)} />
    </div>
  );
}
