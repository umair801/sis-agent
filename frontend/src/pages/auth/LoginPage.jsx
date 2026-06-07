import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth, ROLE_ROUTES } from "../../contexts/AuthContext";
import { Spinner } from "../../components/ui/Spinner";
import { GraduationCap, Eye, EyeOff, AlertCircle } from "lucide-react";
import toast from "react-hot-toast";

export default function LoginPage() {
  const { login }   = useAuth();
  const navigate    = useNavigate();
  const location    = useLocation();

  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [showPw,   setShowPw]   = useState(false);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState("");

  const from = location.state?.from?.pathname || null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!email.trim() || !password.trim()) {
      setError("Please enter your email and password.");
      return;
    }
    setLoading(true);
    try {
      const user = await login(email.trim(), password, "westlake");
      toast.success(`Welcome, ${user.full_name || user.email}!`);
      navigate(from || ROLE_ROUTES[user.role] || "/", { replace: true });
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg =
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
          ? detail.map((d) => d.msg).join(", ")
          : "Invalid credentials. Please try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  // Base input style — no WebkitTextFillColor so placeholder shows correctly
  const inputStyle = {
    color: "#111827",
    backgroundColor: "#ffffff",
  };

  const inputClass =
    "w-full px-4 py-3 rounded-xl border border-gray-200 text-sm " +
    "focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100 " +
    "transition-all";

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-900 via-primary-800 to-indigo-900 flex items-center justify-center p-4">

      {/* Left panel */}
      <div className="hidden lg:flex flex-col justify-between w-96 text-white pr-16">
        <div>
          <div className="flex items-center gap-3 mb-12">
            <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center">
              <GraduationCap size={20} className="text-white" />
            </div>
            <span className="font-display text-lg font-bold">SIS Portal</span>
          </div>
          <h1 className="font-display text-4xl font-bold leading-tight mb-4">
            Smarter school management starts here.
          </h1>
          <p className="text-primary-200 text-sm leading-relaxed">
            AI-powered Student Information System for Westlake Unified School District.
            Attendance, grades, IEPs, budgets, and compliance, all in one place.
          </p>
        </div>
        <div className="flex gap-8 text-sm mt-12">
          <div><p className="text-2xl font-display font-bold">6</p><p className="text-primary-300">Role-scoped dashboards</p></div>
          <div><p className="text-2xl font-display font-bold">AI</p><p className="text-primary-300">Claude-powered insights</p></div>
          <div><p className="text-2xl font-display font-bold">37</p><p className="text-primary-300">Data modules</p></div>
        </div>
      </div>

      {/* Login card */}
      <div className="w-full max-w-md">
        <div className="bg-white rounded-3xl p-8" style={{ boxShadow: "0 25px 60px rgb(0 0 0 / 0.25)" }}>

          {/* Mobile logo */}
          <div className="flex items-center gap-3 mb-8 lg:hidden">
            <div className="w-10 h-10 rounded-xl bg-primary-600 flex items-center justify-center">
              <GraduationCap size={20} className="text-white" />
            </div>
            <div>
              <p className="font-display font-bold text-gray-900 text-base leading-none">SIS Portal</p>
              <p className="text-xs text-gray-400">Westlake Unified</p>
            </div>
          </div>

          <h2 className="font-display text-2xl font-bold text-gray-900 mb-1">Sign in</h2>
          <p className="text-sm text-gray-500 mb-7">Access your role-specific dashboard</p>

          {error && (
            <div className="flex items-center gap-2 mb-5 px-4 py-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
              <AlertCircle size={15} className="shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            <div>
              <label htmlFor="email" className="block text-xs font-bold text-gray-500 mb-1.5 uppercase tracking-wider">
                Email address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={inputStyle}
                className={inputClass}
                placeholder="your.email@school.edu"
                autoComplete="email"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-xs font-bold text-gray-500 mb-1.5 uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPw ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={inputStyle}
                  className={inputClass + " pr-11"}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPw((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors p-1"
                >
                  {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl
                         bg-primary-600 hover:bg-primary-700 text-white font-semibold text-sm
                         transition-all duration-150 active:scale-95
                         disabled:opacity-60 disabled:cursor-not-allowed mt-2"
            >
              {loading && <Spinner className="w-4 h-4 border-white/30 border-t-white" />}
              {loading ? "Signing in..." : "Sign in to Portal"}
            </button>
          </form>

          {/* Demo hint */}
          <div className="mt-6 pt-5 border-t border-gray-100">
            <p className="text-center text-xs text-gray-400 mb-2">Demo credentials</p>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => { setEmail("admin@westlake.edu"); setPassword("admin123"); }}
                className="flex-1 py-2 rounded-lg bg-primary-50 hover:bg-primary-100 text-primary-700
                           text-xs font-semibold transition-colors text-center"
              >
                SuperAdmin
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
