import { getApiBaseUrl, httpClient } from "@/shared/api/httpClient";

export const practiceApi = {
  listScenarios: async () => {
    const { data } = await httpClient.get("/scenarios");
    return data;
  },
  getScenario: async (scenarioId) => {
    const { data } = await httpClient.get(`/scenarios/${scenarioId}`);
    return data;
  },
  getApiBaseUrl,
};
