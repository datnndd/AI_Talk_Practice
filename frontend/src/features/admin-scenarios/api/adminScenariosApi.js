import { httpClient } from "@/shared/api/httpClient";

const scenarioPath = (scenarioId, suffix = "") => `/admin/scenarios/${scenarioId}${suffix}`;
const requestData = async (request) => {
  const { data } = await request;
  return data;
};

const toScenarioFormData = (payload, imageFile) => {
  const formData = new FormData();
  Object.entries(payload).forEach(([key, value]) => {
    if (value === undefined || value === null) return;
    formData.append(key, Array.isArray(value) ? JSON.stringify(value) : value);
  });
  if (imageFile) formData.append("image", imageFile);
  return formData;
};

export const adminApi = {
  listScenarios: (params = {}) => requestData(httpClient.get("/admin/scenarios", { params })),
  createScenario: (payload) => requestData(httpClient.post("/admin/scenarios", payload)),
  createScenarioWithImage: (payload, imageFile) => requestData(httpClient.post("/admin/scenarios", toScenarioFormData(payload, imageFile))),
  updateScenario: (scenarioId, payload) => requestData(httpClient.put(scenarioPath(scenarioId), payload)),
  updateScenarioWithImage: (scenarioId, payload, imageFile) => requestData(httpClient.put(scenarioPath(scenarioId, "/with-image"), toScenarioFormData(payload, imageFile))),
  deleteScenario: (scenarioId) => requestData(httpClient.delete(scenarioPath(scenarioId))),
  restoreScenario: (scenarioId) => requestData(httpClient.post(scenarioPath(scenarioId, "/restore"))),
  toggleScenario: (scenarioId) => requestData(httpClient.post(scenarioPath(scenarioId, "/toggle-active"))),
  bulkAction: (payload) => requestData(httpClient.post("/admin/scenarios/bulk-actions", payload)),
};
