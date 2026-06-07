import client from "./client";

export const communicationApi = {
  listAnnouncements: (params = {}) => client.get("/communication/announcements", { params }),
  listMessages:      (params = {}) => client.get("/communication/messages",      { params }),
  sendMessage:       (data)        => client.post("/communication/messages",     data),
};
