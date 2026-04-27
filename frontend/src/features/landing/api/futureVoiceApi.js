import { httpClient } from "@/shared/api/httpClient";

export const futureVoiceApi = {
  getConfig: async () => {
    const { data } = await httpClient.get("/landing/future-voice");
    return data;
  },
  generate: async ({ audioBase64, fingerprint }) => {
    const { data } = await httpClient.post("/landing/future-voice/generate", {
      audio_base64: audioBase64,
      fingerprint,
    });
    return data;
  },
};

