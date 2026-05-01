import { getApiBaseUrl, httpClient } from "@/shared/api/httpClient";

const scenarioListCache = {
  data: null,
  promise: null,
};

const scenarioDetailCache = new Map();

const getScenarioCacheKey = (scenarioId) => String(scenarioId);

export const practiceApi = {
  listScenarios: async ({ force = false } = {}) => {
    if (!force && scenarioListCache.data) {
      return scenarioListCache.data;
    }
    if (!force && scenarioListCache.promise) {
      return scenarioListCache.promise;
    }

    scenarioListCache.promise = httpClient.get("/scenarios").then(({ data }) => {
      scenarioListCache.data = data;
      scenarioListCache.promise = null;
      if (Array.isArray(data)) {
        data.forEach((scenario) => {
          if (scenario?.id) {
            const key = getScenarioCacheKey(scenario.id);
            const existing = scenarioDetailCache.get(key) || {};
            scenarioDetailCache.set(key, { ...existing, data: { ...scenario, ...existing.data } });
          }
        });
      }
      return data;
    }).catch((error) => {
      scenarioListCache.promise = null;
      throw error;
    });

    return scenarioListCache.promise;
  },
  refreshScenarios: async () => {
    const { data } = await httpClient.get("/scenarios");
    scenarioListCache.data = data;
    return data;
  },
  getCachedScenarios: () => scenarioListCache.data,
  getCachedScenario: (scenarioId) => scenarioDetailCache.get(getScenarioCacheKey(scenarioId))?.data || null,
  getScenario: async (scenarioId, { force = false } = {}) => {
    const key = getScenarioCacheKey(scenarioId);
    const cached = scenarioDetailCache.get(key);
    if (!force && cached?.data?.ai_system_prompt) {
      return cached.data;
    }
    if (!force && cached?.promise) {
      return cached.promise;
    }

    const promise = httpClient.get(`/scenarios/${scenarioId}`).then(({ data }) => {
      scenarioDetailCache.set(key, { data });
      return data;
    }).catch((error) => {
      const current = scenarioDetailCache.get(key);
      if (current?.data) {
        scenarioDetailCache.set(key, { data: current.data });
      } else {
        scenarioDetailCache.delete(key);
      }
      throw error;
    });

    scenarioDetailCache.set(key, { ...(cached || {}), promise });
    return promise;
  },
  prefetchScenario: (scenarioId) => {
    if (!scenarioId) {
      return Promise.resolve(null);
    }
    return practiceApi.getScenario(scenarioId).catch(() => null);
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
