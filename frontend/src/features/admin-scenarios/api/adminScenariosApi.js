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
  createScenarioWithImage: async (payload, imageFile) => {
    const formData = new FormData();
    Object.entries(payload).forEach(([key, value]) => {
      if (value === undefined || value === null) return;
      formData.append(key, Array.isArray(value) ? JSON.stringify(value) : value);
    });
    if (imageFile) formData.append("image", imageFile);
    const { data } = await httpClient.post("/admin/scenarios", formData);
    return data;
  },
  updateScenario: async (scenarioId, payload) => {
    const { data } = await httpClient.put(`/admin/scenarios/${scenarioId}`, payload);
    return data;
  },
  updateScenarioWithImage: async (scenarioId, payload, imageFile) => {
    const formData = new FormData();
    Object.entries(payload).forEach(([key, value]) => {
      if (value === undefined || value === null) return;
      formData.append(key, Array.isArray(value) ? JSON.stringify(value) : value);
    });
    if (imageFile) formData.append("image", imageFile);
    const { data } = await httpClient.put(`/admin/scenarios/${scenarioId}/with-image`, formData);
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
  bulkAction: async (payload) => {
    const { data } = await httpClient.post("/admin/scenarios/bulk-actions", payload);
    return data;
  },
};
