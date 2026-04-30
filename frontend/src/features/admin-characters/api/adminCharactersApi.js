import { httpClient } from "@/shared/api/httpClient";

export const adminCharactersApi = {
  listCharacters: async (params = {}) => {
    const { data } = await httpClient.get("/admin/characters", { params });
    return data;
  },
  createCharacter: async (payload) => {
    const { data } = await httpClient.post("/admin/characters", payload);
    return data;
  },
  updateCharacter: async (characterId, payload) => {
    const { data } = await httpClient.put(`/admin/characters/${characterId}`, payload);
    return data;
  },
  deleteCharacter: async (characterId) => {
    const { data } = await httpClient.delete(`/admin/characters/${characterId}`);
    return data;
  },
  restoreCharacter: async (characterId) => {
    const { data } = await httpClient.post(`/admin/characters/${characterId}/restore`);
    return data;
  },
  toggleCharacter: async (characterId) => {
    const { data } = await httpClient.post(`/admin/characters/${characterId}/toggle-active`);
    return data;
  },
};
