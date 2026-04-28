import { httpClient } from "@/shared/api/httpClient";

export const pronunciationAssessmentApi = {
  getConfig: async () => {
    const { data } = await httpClient.get("/landing/pronunciation-assessment");
    return data;
  },
  score: async ({ audioBase64 }) => {
    const { data } = await httpClient.post("/landing/pronunciation-assessment/score", {
      audio_base64: audioBase64,
    });
    return data;
  },
};
