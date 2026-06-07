import client from "./client";

export const schedulingApi = {
  listSections:  (params = {}) => client.get("/scheduling/sections",  { params }),
  listSchedules: (params = {}) => client.get("/scheduling/schedules", { params }),
  getSection:    (id)          => client.get(`/scheduling/sections/${id}`),
};
