import client from "./client";

export const reportsApi = {
  attendance: (params = {}) => client.get("/reports/attendance", { params }),
  grades:     (params = {}) => client.get("/reports/grades",     { params }),
  compliance: (params = {}) => client.get("/reports/compliance", { params }),
};

export const nlQueryApi = {
  query: (question, context = {}) =>
    client.post("/nl-query/query", { question, context }),
};
