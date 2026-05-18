import { httpClient } from "@/shared/api/httpClient";

const characterPath = (characterId, suffix = "") => `/admin/characters/${characterId}${suffix}`;
const requestData = async (request) => {
  const { data } = await request;
  return data;
};

export const adminCharactersApi = {
  listCharacters: (params = {}) => requestData(httpClient.get("/admin/characters", { params })),
  createCharacter: (payload) => requestData(httpClient.post("/admin/characters", payload)),
  updateCharacter: (characterId, payload) => requestData(httpClient.put(characterPath(characterId), payload)),
  deleteCharacter: (characterId) => requestData(httpClient.delete(characterPath(characterId))),
  restoreCharacter: (characterId) => requestData(httpClient.post(characterPath(characterId, "/restore"))),
  toggleCharacter: (characterId) => requestData(httpClient.post(characterPath(characterId, "/toggle-active"))),
};
