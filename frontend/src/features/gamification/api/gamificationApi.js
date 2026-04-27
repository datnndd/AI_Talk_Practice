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
  getShop: async () => {
    const { data } = await httpClient.get("/gamification/shop");
    return data;
  },
  purchaseShopItem: async (itemCode) => {
    const { data } = await httpClient.post("/gamification/shop/purchase", { item_code: itemCode });
    return data;
  },
};
