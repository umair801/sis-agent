import client from "./client";

export const attendanceApi = {
  listDaily:  (params = {}) => client.get("/attendance/daily",  { params }),
  listPeriod: (params = {}) => client.get("/attendance/period", { params }),
  report:     (params = {}) => client.get("/attendance/report", { params }),
};
