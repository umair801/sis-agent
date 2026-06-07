import client from "./client";

export const spedApi = {
  listIeps:     (params = {}) => client.get("/sped/ieps",              { params }),
  getIep:       (id)          => client.get(`/sped/ieps/${id}`),
  listStudents: (params = {}) => client.get("/sped/students",          { params }),
  compliance:   (params = {}) => client.get("/compliance/alerts",      { params }),
  conflicts:    (params = {}) => client.get("/conflicts/iep-deadlines",{ params }),
};
