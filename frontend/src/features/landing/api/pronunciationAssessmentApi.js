import { httpClient } from "@/shared/api/httpClient";

export const pronunciationAssessmentApi = {
  getConfig: async () => {
    const response = await httpClient.get("/landing/pronunciation-assessment");
    return response.data;
  },
  score: async ({ audioBase64 }) => {
    const response = await httpClient.post("/landing/pronunciation-assessment/score", {
      audio_base64: audioBase64,
    });
    return response.data;
  },
};
