import { getApiBaseUrl } from "@/shared/api/httpClient";

export const absoluteAudioUrl = (url) => {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  const apiBase = getApiBaseUrl().replace(/\/$/, "");
  const origin = apiBase.endsWith("/api") ? apiBase.slice(0, -4) : apiBase;
  return `${origin}${url.startsWith("/") ? url : `/${url}`}`;
};
