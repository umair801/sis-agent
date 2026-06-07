import client from "./client";

export const studentsApi = {
  list:   (params = {}) => client.get("/students/",   { params }),
  get:    (id)           => client.get(`/students/${id}`),
  create: (data)         => client.post("/students/",  data),
  update: (id, data)     => client.put(`/students/${id}`, data),
  delete: (id)           => client.delete(`/students/${id}`),
};
