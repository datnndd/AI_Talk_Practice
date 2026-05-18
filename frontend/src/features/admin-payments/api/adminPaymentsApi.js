import { httpClient } from "@/shared/api/httpClient";

const paymentPath = (path) => `/admin/payments${path}`;
const transactionPath = (paymentId, suffix = "") => paymentPath(`/transactions/${paymentId}${suffix}`);
const requestData = async (request) => {
  const { data } = await request;
  return data;
};

export const adminPaymentsApi = {
  getOverview: () => requestData(httpClient.get(paymentPath("/overview"))),
  listPlans: () => requestData(httpClient.get(paymentPath("/plans"))),
  updatePlan: (code, payload) => requestData(httpClient.put(paymentPath(`/plans/${code}`), payload)),
  listTransactions: (params = {}) => requestData(httpClient.get(paymentPath("/transactions"), { params })),
  getTransaction: (paymentId) => requestData(httpClient.get(transactionPath(paymentId))),
  approveTransaction: (paymentId, payload = {}) => requestData(httpClient.post(transactionPath(paymentId, "/approve"), payload)),
  cancelTransaction: (paymentId, payload = {}) => requestData(httpClient.post(transactionPath(paymentId, "/cancel"), payload)),
};

