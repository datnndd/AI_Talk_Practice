import { httpClient } from "@/shared/api/httpClient";

export const adminPaymentsApi = {
  getOverview: async () => {
    const { data } = await httpClient.get("/admin/payments/overview");
    return data;
  },
  listPlans: async () => {
    const { data } = await httpClient.get("/admin/payments/plans");
    return data;
  },
  updatePlan: async (code, payload) => {
    const { data } = await httpClient.put(`/admin/payments/plans/${code}`, payload);
    return data;
  },
  listPromotions: async () => {
    const { data } = await httpClient.get("/admin/payments/promotions");
    return data;
  },
  createPromotion: async (payload) => {
    const { data } = await httpClient.post("/admin/payments/promotions", payload);
    return data;
  },
  updatePromotion: async (code, payload) => {
    const { data } = await httpClient.put(`/admin/payments/promotions/${code}`, payload);
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
