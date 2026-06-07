import client from "./client";

export const budgetApi = {
  list:      (params = {}) => client.get("/budget/",           { params }),
  summary:   (params = {}) => client.get("/budget/summary",    { params }),
  forecasts: (params = {}) => client.get("/forecasts/budget",  { params }),
};
