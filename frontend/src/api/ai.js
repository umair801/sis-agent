import client from "./client";

export const aiApi = {
  query:    (question, context = {}) =>
    client.post("/nl-query/query", { question, context }),
  reports:  (type, params = {}) =>
    client.post("/reports/generate", { report_type: type, ...params }),
  forecast: (type, params = {}) =>
    client.post("/forecasts/generate", { forecast_type: type, ...params }),
};
