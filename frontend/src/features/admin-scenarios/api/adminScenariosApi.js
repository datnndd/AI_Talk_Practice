import { httpClient } from "@/shared/api/httpClient";

export const adminApi = {
  listScenarios: async (params = {}) => {
    const { data } = await httpClient.get("/admin/scenarios", { params });
    return data;
  },
  createScenario: async (payload) => {
    const { data } = await httpClient.post("/admin/scenarios", payload);
    return data;
  },
  updateScenario: async (scenarioId, payload) => {
    const { data } = await httpClient.put(`/admin/scenarios/${scenarioId}`, payload);
    return data;
  },
  deleteScenario: async (scenarioId) => {
    const { data } = await httpClient.delete(`/admin/scenarios/${scenarioId}`);
    return data;
  },
  restoreScenario: async (scenarioId) => {
    const { data } = await httpClient.post(`/admin/scenarios/${scenarioId}/restore`);
    return data;
  },
  toggleScenario: async (scenarioId) => {
    const { data } = await httpClient.post(`/admin/scenarios/${scenarioId}/toggle-active`);
    return data;
  },
  generateDefaultPrompt: async (payload) => {
    const { data } = await httpClient.post("/admin/scenarios/generate-default-prompt", payload);
    return data;
  },
  bulkAction: async (payload) => {
    const { data } = await httpClient.post("/admin/scenarios/bulk-actions", payload);
    return data;
  },
};
