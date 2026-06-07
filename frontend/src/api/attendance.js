import client from "./client";

export const attendanceApi = {
  listDaily:   (params = {}) => client.get("/attendance/daily",           { params }),
  listPeriod:  (params = {}) => client.get("/attendance/period",          { params }),
  createDaily: (data)        => client.post("/attendance/daily",          data),
  updateDaily: (id, data)    => client.put(`/attendance/daily/${id}`,     data),
  report:      (params = {}) => client.get("/attendance/report",          { params }),
};
