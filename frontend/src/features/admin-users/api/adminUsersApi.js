import { httpClient } from "@/shared/api/httpClient";

export const adminUsersApi = {
  listUsers: async (params = {}) => {
    const { data } = await httpClient.get("/admin/users", { params });
    return data;
  },
  getUser: async (userId) => {
    const { data } = await httpClient.get(`/admin/users/${userId}`);
    return data;
  },
  updateUser: async (userId, payload) => {
    const { data } = await httpClient.put(`/admin/users/${userId}`, payload);
    return data;
  },
  toggleAdmin: async (userId) => {
    const { data } = await httpClient.post(`/admin/users/${userId}/toggle-admin`);
    return data;
  },
  deactivateUser: async (userId) => {
    const { data } = await httpClient.post(`/admin/users/${userId}/deactivate`);
    return data;
  },
  restoreUser: async (userId) => {
    const { data } = await httpClient.post(`/admin/users/${userId}/restore`);
    return data;
  },
};
