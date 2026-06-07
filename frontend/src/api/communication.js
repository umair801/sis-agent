import client from "./client";

export const communicationApi = {
  listAnnouncements: (params = {}) => client.get("/communication/announcements",   { params }),
  getInbox:          (params = {}) => client.get("/communication/messages/inbox",  { params }),
  getSent:           (params = {}) => client.get("/communication/messages/sent",   { params }),
  sendMessage:       (data)        => client.post("/communication/messages",        data),
  markRead:          (id)          => client.patch(`/communication/messages/${id}/read`),
  getThread:         (id)          => client.get(`/communication/messages/${id}/thread`),
};
