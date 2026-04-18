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
  generateLesson: async ({ sessionId, scenarioId, level, regenerate = false }) => {
    const { data } = await httpClient.post("/lessons/generate", {
      session_id: sessionId,
      scenario_id: scenarioId,
      level,
      regenerate,
    });
    return data;
  },
  getLessonHint: async ({ sessionId, lessonId, objectiveId }) => {
    const { data } = await httpClient.post("/lessons/hint", {
      session_id: sessionId,
      lesson_id: lessonId,
      objective_id: objectiveId,
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
