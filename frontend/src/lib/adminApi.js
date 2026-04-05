import { api } from "../contexts/AuthContext";

export const adminApi = {
  listScenarios: async (params = {}) => {
    const { data } = await api.get("/admin/scenarios", { params });
    return data;
  },
  getScenario: async (scenarioId) => {
    const { data } = await api.get(`/admin/scenarios/${scenarioId}`);
    return data;
  },
  createScenario: async (payload) => {
    const { data } = await api.post("/admin/scenarios", payload);
    return data;
  },
  updateScenario: async (scenarioId, payload) => {
    const { data } = await api.put(`/admin/scenarios/${scenarioId}`, payload);
    return data;
  },
  deleteScenario: async (scenarioId) => {
    const { data } = await api.delete(`/admin/scenarios/${scenarioId}`);
    return data;
  },
  restoreScenario: async (scenarioId) => {
    const { data } = await api.post(`/admin/scenarios/${scenarioId}/restore`);
    return data;
  },
  toggleScenario: async (scenarioId) => {
    const { data } = await api.post(`/admin/scenarios/${scenarioId}/toggle-active`);
    return data;
  },
  suggestSkills: async (payload) => {
    const { data } = await api.post("/admin/scenarios/suggest-skills", payload);
    return data;
  },
  bulkAction: async (payload) => {
    const { data } = await api.post("/admin/scenarios/bulk-actions", payload);
    return data;
  },
  getPromptHistory: async (scenarioId) => {
    const { data } = await api.get(`/admin/scenarios/${scenarioId}/prompt-history`);
    return data;
  },
  generateVariations: async (scenarioId, payload) => {
    const { data } = await api.post(`/admin/scenarios/${scenarioId}/generate-variations`, payload);
    return data;
  },
  getGenerationTask: async (taskId) => {
    const { data } = await api.get(`/admin/generation-tasks/${taskId}`);
    return data;
  },
  listVariations: async (scenarioId, search = "") => {
    const { data } = await api.get("/admin/scenario-variations", {
      params: { scenario_id: scenarioId, search: search || undefined },
    });
    return data;
  },
  createVariation: async (payload) => {
    const { data } = await api.post("/admin/scenario-variations", payload);
    return data;
  },
  updateVariation: async (variationId, payload) => {
    const { data } = await api.put(`/admin/scenario-variations/${variationId}`, payload);
    return data;
  },
  deleteVariation: async (variationId) => {
    const { data } = await api.delete(`/admin/scenario-variations/${variationId}`);
    return data;
  },
};
