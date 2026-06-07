import client from "./client";

export const gradebookApi = {
  listGrades:      (params = {}) => client.get("/gradebook/grades",      { params }),
  listAssignments: (params = {}) => client.get("/gradebook/assignments",  { params }),
  createGrade:     (data)        => client.post("/gradebook/grades",      data),
  updateGrade:     (id, data)    => client.put(`/gradebook/grades/${id}`, data),
};
