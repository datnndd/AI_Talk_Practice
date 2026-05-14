import { httpClient } from "@/shared/api/httpClient";

const curriculumCache = {
  data: null,
  promise: null,
};

const unitCache = new Map();
const sectionCache = new Map();

const getUnitCacheKey = (unitId) => String(unitId);

export const curriculumApi = {
  getCurriculum: async ({ force = false } = {}) => {
    if (!force && curriculumCache.data) {
      return curriculumCache.data;
    }
    if (!force && curriculumCache.promise) {
      return curriculumCache.promise;
    }

    curriculumCache.promise = httpClient.get("/curriculum").then(({ data }) => {
      curriculumCache.data = data;
      curriculumCache.promise = null;
      return data;
    }).catch((error) => {
      curriculumCache.promise = null;
      throw error;
    });

    return curriculumCache.promise;
  },
  getCachedCurriculum: () => curriculumCache.data,
  getSection: async (sectionId, { force = false } = {}) => {
    const key = String(sectionId);
    const cached = sectionCache.get(key);
    if (!force && cached?.data) {
      return cached.data;
    }
    if (!force && cached?.promise) {
      return cached.promise;
    }

    const promise = httpClient.get(`/curriculum/sections/${sectionId}`).then(({ data }) => {
      const section = data.sections?.[0] || null;
      sectionCache.set(key, { data: section });
      return section;
    }).catch((error) => {
      sectionCache.delete(key);
      throw error;
    });

    sectionCache.set(key, { promise });
    return promise;
  },
  getUnit: async (unitId, { force = false } = {}) => {
    const key = getUnitCacheKey(unitId);
    const cached = unitCache.get(key);
    if (!force && cached?.data) {
      return cached.data;
    }
    if (!force && cached?.promise) {
      return cached.promise;
    }

    const promise = httpClient.get(`/units/${unitId}`).then(({ data }) => {
      unitCache.set(key, { data });
      return data;
    }).catch((error) => {
      unitCache.delete(key);
      throw error;
    });

    unitCache.set(key, { promise });
    return promise;
  },
  getCachedUnit: (unitId) => unitCache.get(getUnitCacheKey(unitId))?.data || null,
  prefetchUnit: (unitId) => {
    if (!unitId) {
      return Promise.resolve(null);
    }
    return curriculumApi.getUnit(unitId).catch(() => null);
  },
  attemptLesson: async (lessonId, payload) => {
    const { data } = await httpClient.post(`/lessons/${lessonId}/attempt`, payload);
    return data;
  },

};

export const adminCurriculumApi = {
  listSectionSummariesPaged: async (params = {}) => {
    const { data } = await httpClient.get("/admin/curriculum/sections/summary-paged", { params });
    return data;
  },
  getSection: async (sectionId) => {
    const { data } = await httpClient.get(`/admin/curriculum/sections/${sectionId}`);
    return data;
  },
  createSection: async (payload) => {
    const { data } = await httpClient.post("/admin/curriculum/sections", payload);
    return data;
  },
  updateSection: async (sectionId, payload) => {
    const { data } = await httpClient.put(`/admin/curriculum/sections/${sectionId}`, payload);
    return data;
  },
  deleteSection: async (sectionId) => {
    const { data } = await httpClient.delete(`/admin/curriculum/sections/${sectionId}`);
    return data;
  },
  createUnit: async (payload) => {
    const { data } = await httpClient.post("/admin/curriculum/units", payload);
    return data;
  },
  updateUnit: async (unitId, payload) => {
    const { data } = await httpClient.put(`/admin/curriculum/units/${unitId}`, payload);
    return data;
  },
  deleteUnit: async (unitId) => {
    const { data } = await httpClient.delete(`/admin/curriculum/units/${unitId}`);
    return data;
  },
  createLesson: async (payload) => {
    const { data } = await httpClient.post("/admin/curriculum/lessons", payload);
    return data;
  },
  getLesson: async (lessonId) => {
    const { data } = await httpClient.get(`/admin/curriculum/lessons/${lessonId}`);
    return data;
  },
  updateLesson: async (lessonId, payload) => {
    const { data } = await httpClient.put(`/admin/curriculum/lessons/${lessonId}`, payload);
    return data;
  },
  deleteLesson: async (lessonId) => {
    const { data } = await httpClient.delete(`/admin/curriculum/lessons/${lessonId}`);
    return data;
  },
  reorderLessons: async (items) => {
    const { data } = await httpClient.post("/admin/curriculum/lessons/reorder", { items });
    return data;
  },
  createLessonAudioTts: async (payload) => {
    const { data } = await httpClient.post("/admin/curriculum/audio/tts", payload);
    return data;
  },
  uploadLessonAudio: async ({ file, lessonId, text, language }) => {
    const formData = new FormData();
    formData.append("file", file);
    if (lessonId) formData.append("lesson_id", lessonId);
    if (text) formData.append("text", text);
    if (language) formData.append("language", language);
    const { data } = await httpClient.post("/admin/curriculum/audio/upload", formData);
    return data;
  },
};
