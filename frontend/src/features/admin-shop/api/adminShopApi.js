import { httpClient } from "@/shared/api/httpClient";

export const adminShopApi = {
  listProducts: async () => {
    const { data } = await httpClient.get("/admin/gamification/shop/products");
    return data;
  },
  createProduct: async (payload) => {
    const { data } = await httpClient.post("/admin/gamification/shop/products", payload);
    return data;
  },
  updateProduct: async (productId, payload) => {
    const { data } = await httpClient.put(`/admin/gamification/shop/products/${productId}`, payload);
    return data;
  },
  hideProduct: async (productId) => {
    const { data } = await httpClient.delete(`/admin/gamification/shop/products/${productId}`);
    return data;
  },
  listRedemptions: async () => {
    const { data } = await httpClient.get("/admin/gamification/shop/redemptions");
    return data;
  },
  updateRedemptionStatus: async (redemptionId, status) => {
    const { data } = await httpClient.put(`/admin/gamification/shop/redemptions/${redemptionId}/status`, { status });
    return data;
  },
};
