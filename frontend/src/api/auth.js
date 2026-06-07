import client from "./client";

export const authApi = {
  login:  (email, password, tenant_slug = "westlake") =>
    client.post("/auth/login", { email, password, tenant_slug }),
  me:     () => client.get("/auth/me"),
  logout: () => client.post("/auth/logout"),
};
