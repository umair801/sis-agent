import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { authApi } from "../api/auth";

const AuthContext = createContext(null);

export const ROLE_ROUTES = {
  SuperAdmin:      "/superadmin",
  DistrictAdmin:   "/districtadmin",
  Principal:       "/principal",
  Teacher:         "/teacher",
  SpEdCoordinator: "/sped",
  Parent:          "/parent",
};

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("sis_user");
    const token  = localStorage.getItem("sis_token");
    if (stored && token) {
      try { setUser(JSON.parse(stored)); }
      catch { localStorage.clear(); }
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (email, password, tenantSlug = "westlake") => {
    const { data } = await authApi.login(email, password, tenantSlug);

    // Backend returns flat fields, not a nested user object — normalize here
    const userObj = {
      id:        data.user_id,
      email,
      full_name: data.full_name,
      role:      data.role,
      tenant_id: data.tenant_id,
    };

    localStorage.setItem("sis_token", data.access_token);
    localStorage.setItem("sis_refresh", data.refresh_token);
    localStorage.setItem("sis_user",  JSON.stringify(userObj));
    setUser(userObj);
    return userObj;
  }, []);

  const logout = useCallback(async () => {
    try { await authApi.logout(); } catch {}
    localStorage.removeItem("sis_token");
    localStorage.removeItem("sis_refresh");
    localStorage.removeItem("sis_user");
    setUser(null);
  }, []);

  const hasRole = useCallback((roles) => {
    if (!user) return false;
    const allowed = Array.isArray(roles) ? roles : [roles];
    return allowed.includes(user.role);
  }, [user]);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
