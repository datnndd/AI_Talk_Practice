import { httpClient } from "@/shared/api/httpClient";

const requestData = async (request) => {
  const { data } = await request;
  return data;
};

export const createCheckoutSession = async (payload) => {
  return requestData(httpClient.post("/payments/checkout", payload));
};

export const listSubscriptionPlans = async () => {
  return requestData(httpClient.get("/payments/plans"));
};

export const getCheckoutStatus = async (orderCode) => {
  return requestData(httpClient.get(`/payments/transactions/${orderCode}`));
};
