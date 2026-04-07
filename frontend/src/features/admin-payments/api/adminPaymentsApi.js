import { httpClient } from "@/shared/api/httpClient";

export const adminPaymentsApi = {
  getOverview: async () => {
    const { data } = await httpClient.get("/admin/payments/overview");
    return data;
  },
  listTransactions: async (params = {}) => {
    const { data } = await httpClient.get("/admin/payments/transactions", { params });
    return data;
  },
  getTransaction: async (paymentId) => {
    const { data } = await httpClient.get(`/admin/payments/transactions/${paymentId}`);
    return data;
  },
  approveTransaction: async (paymentId, payload = {}) => {
    const { data } = await httpClient.post(`/admin/payments/transactions/${paymentId}/approve`, payload);
    return data;
  },
  cancelTransaction: async (paymentId, payload = {}) => {
    const { data } = await httpClient.post(`/admin/payments/transactions/${paymentId}/cancel`, payload);
    return data;
  },
};
