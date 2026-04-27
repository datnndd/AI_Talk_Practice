import { httpClient } from "@/shared/api/httpClient";

export const curriculumApi = {
  getCurriculum: async () => {
    const { data } = await httpClient.get("/curriculum");
    return data;
  },
  getLesson: async (lessonId) => {
    const { data } = await httpClient.get(`/lessons/${lessonId}`);
    return data;
  },
  attemptExercise: async (exerciseId, payload) => {
    const { data } = await httpClient.post(`/exercises/${exerciseId}/attempt`, payload);
    return data;
  },
  startConversationExercise: async (exerciseId, payload = {}) => {
    const { data } = await httpClient.post(`/exercises/${exerciseId}/start-conversation`, payload);
    return data;
  },
};

export const adminCurriculumApi = {
  listLevels: async () => {
    const { data } = await httpClient.get("/admin/curriculum/levels");
    return data;
  },
  createLevel: async (payload) => {
    const { data } = await httpClient.post("/admin/curriculum/levels", payload);
    return data;
  },
  updateLevel: async (levelId, payload) => {
    const { data } = await httpClient.put(`/admin/curriculum/levels/${levelId}`, payload);
    return data;
  },
  createLesson: async (payload) => {
    const { data } = await httpClient.post("/admin/curriculum/lessons", payload);
    return data;
  },
  updateLesson: async (lessonId, payload) => {
    const { data } = await httpClient.put(`/admin/curriculum/lessons/${lessonId}`, payload);
    return data;
  },
  createExercise: async (payload) => {
    const { data } = await httpClient.post("/admin/curriculum/exercises", payload);
    return data;
  },
  updateExercise: async (exerciseId, payload) => {
    const { data } = await httpClient.put(`/admin/curriculum/exercises/${exerciseId}`, payload);
    return data;
  },
  previewDictionary: async (words) => {
    const { data } = await httpClient.post("/admin/curriculum/dictionary/preview", { words });
    return data;
  },
};
