import { getApiBaseUrl } from "@/shared/api/httpClient";

export const absoluteAudioUrl = (url) => {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  return `${getApiBaseUrl()}${url.startsWith("/") ? url : `/${url}`}`;
};
