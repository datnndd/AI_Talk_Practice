import { httpClient } from "@/shared/api/httpClient";

const requestData = async (request) => {
  const { data } = await request;
  return data;
};

export const adminSiteApi = {
  uploadLogo: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return requestData(httpClient.post("/admin/site/logo", formData));
  },
};
