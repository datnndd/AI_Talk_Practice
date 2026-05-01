import { httpClient } from "@/shared/api/httpClient";

export const gamificationApi = {
  getDashboard: async () => {
    const { data } = await httpClient.get("/gamification/me");
    return data;
  },
  checkIn: async () => {
    const { data } = await httpClient.post("/gamification/check-in");
    return data;
  },
  autoCheckIn: async () => {
    const { data } = await httpClient.post("/gamification/check-in/auto");
    return data;
  },
  getShop: async () => {
    const { data } = await httpClient.get("/gamification/shop");
    return data;
  },
  redeemShopProduct: async (payload) => {
    const { data } = await httpClient.post("/gamification/shop/redeem", payload);
    return data;
  },
};
