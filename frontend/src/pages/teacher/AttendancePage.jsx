import { useState, useEffect } from "react";
import { studentsApi } from "../../api/students";
import { schedulingApi } from "../../api/scheduling";
import { attendanceApi } from "../../api/attendance";
import { Spinner } from "../../components/ui/Spinner";
import { cn } from "../../utils/cn";
import {
  CheckCircle, XCircle, Clock, FileCheck,
  ChevronDown, Save, AlertCircle, CheckCheck,
} from "lucide-react";
import toast from "react-hot-toast";

const STATUS_OPTIONS = [
  { value: "present", label: "Present",  icon: CheckCircle, color: "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100" },
  { value: "absent",  label: "Absent",   icon: XCircle,     color: "bg-red-50    text-red-700    border-red-200    hover:bg-red-100"    },
  { value: "late",    label: "Late",     icon: Clock,       color: "bg-amber-50  text-amber-700  border-amber-200  hover:bg-amber-100"  },
  { value: "excused", label: "Excused",  icon: FileCheck,   color: "bg-sky-50    text-sky-700    border-sky-200    hover:bg-sky-100"    },
];

const ACTIVE_STATUS = {
  present: "bg-emerald-500 text-white border-emerald-500",
  absent:  "bg-red-500    text-white border-red-500",
  late:    "bg-amber-500  text-white border-amber-500",
  excused: "bg-sky-500    text-white border-sky-500",
};

export default function AttendancePage() {
  const today = new Date().toISOString().split("T")[0];

  const [sections,    setSections]    = useState([]);
  const [students,   setStudents]    = useState([]);
  const [sectionId,   setSectionId]   = useState("");
  const [date,        setDate]        = useState(today);
  const [attendance,  setAttendance]  = useState({});
  const [loading,     setLoading]     = useState(true);
  const [loadingStu,  setLoadingStu]  = useState(false);
  const [saving,      setSaving]      = useState(false);
  const [saved,       setSaved]       = useState(false);

  // Load sections
  useEffect(() => {
    schedulingApi.listSections({ limit: 20 })
      .then((res) => {
        const d = res.data;
        const list = Array.isArray(d) ? d : (d?.sections || d?.items || []);
        setSections(list);
        if (list.length > 0) setSectionId(list[0].id);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // Load students when section changes
  useEffect(() => {
    if (!sectionId) return;
    setLoadingStu(true);
    setAttendance({});
    setSaved(false);
    studentsApi.list({ limit: 50 })
      .then((res) => {
        const d = res.data;
        const list = Array.isArray(d) ? d : (d?.students || d?.items || []);
        setStudents(list);
        // Default everyone to present
        const defaults = {};
        list.forEach((s) => { defaults[s.id] = "present"; });
        setAttendance(defaults);
      })
      .catch(() => {})
      .finally(() => setLoadingStu(false));
  }, [sectionId]);

  const setStatus = (studentId, status) => {
    setAttendance((prev) => ({ ...prev, [studentId]: status }));
    setSaved(false);
  };

  const markAll = (status) => {
    const next = {};
    students.forEach((s) => { next[s.id] = status; });
    setAttendance(next);
    setSaved(false);
  };

  const handleSave = async () => {
    if (!sectionId || students.length === 0) {
      toast.error("Select a section first.");
      return;
    }
    setSaving(true);
    try {
      // Build payload — one record per student
      const records = students.map((s) => ({
        student_id:  s.id,
        section_id:  sectionId,
        date,
        status:      attendance[s.id] || "present",
        notes:       "",
      }));
      await attendanceApi.createDaily({ records });
      setSaved(true);
      toast.success("Attendance saved successfully!");
    } catch (err) {
      const msg = err.response?.data?.detail || "Failed to save attendance.";
      toast.error(typeof msg === "string" ? msg : "Failed to save attendance.");
    } finally {
      setSaving(false);
    }
  };

  // Summary counts
  const counts = Object.values(attendance).reduce((acc, s) => {
    acc[s] = (acc[s] || 0) + 1;
    return acc;
  }, {});

  const selectedSection = sections.find((s) => s.id === sectionId);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner className="w-7 h-7" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-5 pb-8">

      {/* Section + Date selectors */}
      <div className="card p-4 space-y-3">
        <div>
          <label className="block text-xs font-bold text-text-secondary uppercase tracking-wider mb-1.5">
            Section
          </label>
          <div className="relative">
            <select
              value={sectionId}
              onChange={(e) => setSectionId(e.target.value)}
              className="w-full appearance-none bg-white border border-surface-border rounded-xl
                         px-4 py-2.5 text-sm text-text-primary
                         focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100
                         pr-10 cursor-pointer"
            >
              {sections.length === 0 && (
                <option value="">No sections available</option>
              )}
              {sections.map((sec) => (
                <option key={sec.id} value={sec.id}>
                  Period {sec.period_number || sec.period || "?"} —{" "}
                  {sec.course_name || sec.course_code || "Section"}{" "}
                  ({sec.room_name || sec.room || "Room TBD"})
                </option>
              ))}
            </select>
            <ChevronDown size={15} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" />
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-text-secondary uppercase tracking-wider mb-1.5">
            Date
          </label>
          <input
            type="date"
            value={date}
            onChange={(e) => { setDate(e.target.value); setSaved(false); }}
            max={today}
            className="w-full bg-white border border-surface-border rounded-xl px-4 py-2.5
                       text-sm text-text-primary focus:outline-none focus:border-primary-400
                       focus:ring-2 focus:ring-primary-100"
          />
        </div>
      </div>

      {/* Summary bar */}
      {students.length > 0 && (
        <div className="grid grid-cols-4 gap-2">
          {STATUS_OPTIONS.map(({ value, label }) => (
            <div
              key={value}
              className={cn(
                "text-center py-2.5 rounded-xl border text-xs font-semibold",
                value === "present" ? "bg-emerald-50 text-emerald-700 border-emerald-200" :
                value === "absent"  ? "bg-red-50    text-red-700    border-red-200"    :
                value === "late"    ? "bg-amber-50  text-amber-700  border-amber-200"  :
                                      "bg-sky-50    text-sky-700    border-sky-200"
              )}
            >
              <p className="text-xl font-display font-bold">{counts[value] || 0}</p>
              <p>{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Mark all buttons */}
      {students.length > 0 && (
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-text-secondary">Mark all:</span>
          {STATUS_OPTIONS.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => markAll(value)}
              className={cn(
                "text-xs px-3 py-1.5 rounded-lg border font-medium transition-all",
                value === "present" ? "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100" :
                value === "absent"  ? "bg-red-50    text-red-700    border-red-200    hover:bg-red-100"    :
                value === "late"    ? "bg-amber-50  text-amber-700  border-amber-200  hover:bg-amber-100"  :
                                      "bg-sky-50    text-sky-700    border-sky-200    hover:bg-sky-100"
              )}
            >
              {label}
            </button>
          ))}
        </div>
      )}

      {/* Student list */}
      <div className="card overflow-hidden">
        {loadingStu ? (
          <div className="flex items-center justify-center py-16">
            <Spinner className="w-6 h-6" />
          </div>
        ) : students.length === 0 ? (
          <div className="text-center py-16">
            <AlertCircle size={28} className="text-text-muted mx-auto mb-2" />
            <p className="text-sm text-text-muted">No students found.</p>
          </div>
        ) : (
          <div className="divide-y divide-surface-border">
            {students.map((student, idx) => {
              const status = attendance[student.id] || "present";
              return (
                <div
                  key={student.id}
                  className="flex items-center gap-3 px-4 py-3 hover:bg-surface-muted transition-colors"
                >
                  {/* Index + avatar */}
                  <span className="text-xs text-text-muted w-5 shrink-0">{idx + 1}</span>
                  <div className="w-9 h-9 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
                    <span className="text-xs font-bold text-primary-700">
                      {(student.first_name?.[0] || "S")}{(student.last_name?.[0] || "")}
                    </span>
                  </div>

                  {/* Name */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-text-primary truncate">
                      {student.first_name} {student.last_name}
                    </p>
                    <p className="text-[10px] text-text-muted">{student.student_id || student.id?.slice(0, 8)}</p>
                  </div>

                  {/* Status toggle buttons — compact on mobile */}
                  <div className="flex gap-1 shrink-0">
                    {STATUS_OPTIONS.map(({ value, label, icon: Icon }) => (
                      <button
                        key={value}
                        onClick={() => setStatus(student.id, value)}
                        title={label}
                        className={cn(
                          "w-9 h-9 rounded-xl border flex items-center justify-center transition-all",
                          status === value
                            ? ACTIVE_STATUS[value]
                            : "bg-white border-surface-border text-text-muted hover:bg-surface-muted"
                        )}
                      >
                        <Icon size={15} />
                      </button>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Save button — sticky on mobile */}
      {students.length > 0 && (
        <div className="sticky bottom-4">
          <button
            onClick={handleSave}
            disabled={saving || saved}
            className={cn(
              "w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl font-semibold text-sm",
              "transition-all duration-150 active:scale-95",
              saved
                ? "bg-emerald-500 text-white cursor-default"
                : "bg-primary-600 hover:bg-primary-700 text-white disabled:opacity-60"
            )}
            style={{ boxShadow: "0 8px 25px rgb(79 70 229 / 0.35)" }}
          >
            {saving ? (
              <><Spinner className="w-4 h-4 border-white/30 border-t-white" /> Saving...</>
            ) : saved ? (
              <><CheckCheck size={17} /> Attendance Saved</>
            ) : (
              <><Save size={17} /> Save Attendance ({students.length} students)</>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
