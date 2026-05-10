import { httpClient } from "@/shared/api/httpClient";

export const gamificationApi = {
  getDashboard: async () => {
    const { data } = await httpClient.get("/gamification/me");
    return data;
  },
  getShop: async () => {
    const { data } = await httpClient.get("/gamification/shop");
    return data;
  },
  getShopRedemptions: async () => {
    const { data } = await httpClient.get("/gamification/shop/redemptions");
    return data;
  },
  redeemShopProduct: async (payload) => {
    const { data } = await httpClient.post("/gamification/shop/redeem", payload);
    return data;
  },
};
