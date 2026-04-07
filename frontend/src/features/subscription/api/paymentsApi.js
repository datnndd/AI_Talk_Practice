import { httpClient } from "@/shared/api/httpClient";

export const createCheckoutSession = async (payload) => {
  const response = await httpClient.post("/payments/checkout", payload);
  return response.data;
};
