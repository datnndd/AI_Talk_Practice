import { httpClient } from "@/shared/api/httpClient";

export const adminShopApi = {
  createProductWithImage: async (payload, imageFile) => {
    const formData = new FormData();
    Object.entries(payload).forEach(([key, value]) => {
      if (value !== undefined && value !== null) formData.append(key, value);
    });
    if (imageFile) formData.append("image", imageFile);
    const { data } = await httpClient.post("/admin/gamification/shop/products/with-image", formData);
    return data;
  },
  updateProductWithImage: async (productId, payload, imageFile) => {
    const formData = new FormData();
    Object.entries(payload).forEach(([key, value]) => {
      if (value !== undefined && value !== null) formData.append(key, value);
    });
    if (imageFile) formData.append("image", imageFile);
    const { data } = await httpClient.put(`/admin/gamification/shop/products/${productId}/with-image`, formData);
    return data;
  },
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
