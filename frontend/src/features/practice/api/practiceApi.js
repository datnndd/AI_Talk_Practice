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
  getSession: async (sessionId) => {
    const { data } = await httpClient.get(`/sessions/${sessionId}`);
    return data;
  },
  endSession: async (sessionId, payload = {}) => {
    const { data } = await httpClient.post(`/sessions/${sessionId}/end`, payload);
    return data;
  },
  getLessonHint: async ({ sessionId, text, messageId }) => {
    const { data } = await httpClient.post(`/sessions/${sessionId}/hint`, {
      ...(messageId ? { message_id: messageId } : {}),
      ...(text ? { text } : {}),
    });
    return data;
  },
  translate: async ({ text, targetLanguage }) => {
    const { data } = await httpClient.post("/translations/translate", {
      text,
      target_language: targetLanguage,
    });
    return data;
  },
  getApiBaseUrl,
};
