const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const DEFAULT_GET_CACHE_TTL_MS = 12_000;
const getRequestCache = new Map();

const buildUrl = (path, params) => {
  const normalizedPath = path.startsWith("http")
    ? path
    : `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;

  const url = new URL(normalizedPath);

  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });

  return url.toString();
};

const parseResponse = async (response) => {
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  const text = await response.text();
  return text ? { detail: text } : null;
};

export const formatApiErrorDetail = (detail) => {
  if (!detail) {
    return "";
  }

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }

        if (!item || typeof item !== "object") {
          return String(item);
        }

        const field = Array.isArray(item.loc)
          ? item.loc.filter((part) => part !== "body" && part !== "query" && part !== "path").join(".")
          : "";
        const message = item.msg || item.message || item.detail || JSON.stringify(item);

        return field ? `${field}: ${message}` : message;
      })
      .join(" ");
  }

  if (typeof detail === "object") {
    return detail.message || detail.msg || detail.detail || JSON.stringify(detail);
  }

  return String(detail);
};

export const getApiErrorMessage = (error, fallback = "Request failed.") =>
  formatApiErrorDetail(error?.response?.data?.detail) || error?.message || fallback;

const createHttpError = (status, data) => {
  const message = formatApiErrorDetail(data?.detail) || `Request failed with status ${status}`;
  const error = new Error(message);

  error.response = {
    status,
    data,
  };

  return error;
};

const refreshAccessToken = async () => {
  const refreshToken = localStorage.getItem("refresh_token");

  if (!refreshToken) {
    return null;
  }

  const response = await fetch(buildUrl("/auth/refresh"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      refresh_token: refreshToken,
    }),
  });

  const data = await parseResponse(response);

  if (!response.ok) {
    throw createHttpError(response.status, data);
  }

  const accessToken = data?.access_token;

  if (accessToken) {
    localStorage.setItem("access_token", accessToken);
  }

  return accessToken;
};

const stableCacheKey = ({ method, path, params }) => `${method}:${buildUrl(path, params)}`;

export const clearHttpCache = (prefix = "") => {
  if (!prefix) {
    getRequestCache.clear();
    return;
  }
  for (const key of getRequestCache.keys()) {
    if (key.includes(prefix)) {
      getRequestCache.delete(key);
    }
  }
};

const cachePrefixForPath = (path) => path.split("/").slice(0, 3).join("/");

const request = async ({ method = "GET", path, params, data, headers = {}, cacheTtlMs, _retry = false }) => {
  const accessToken = localStorage.getItem("access_token");
  const isFormData = typeof FormData !== "undefined" && data instanceof FormData;
  const requestHeaders = {
    ...headers,
  };

  if (data !== undefined && !isFormData) {
    requestHeaders["Content-Type"] = "application/json; charset=utf-8";
  }

  if (accessToken) {
    requestHeaders.Authorization = `Bearer ${accessToken}`;
  }

  const cacheKey = method === "GET" && cacheTtlMs !== 0 ? stableCacheKey({ method, path, params }) : null;
  if (cacheKey) {
    const cached = getRequestCache.get(cacheKey);
    if (cached && cached.expiresAt > Date.now()) {
      return cached.promise;
    }
  }

  const executeRequest = async () => {
    const response = await fetch(buildUrl(path, params), {
      method,
      headers: requestHeaders,
      body: data !== undefined ? (isFormData ? data : JSON.stringify(data)) : undefined,
    });

    const responseData = await parseResponse(response);

    if (response.status === 401 && !_retry && path !== "/auth/refresh") {
      try {
        const refreshedToken = await refreshAccessToken();

        if (refreshedToken) {
          return request({
            method,
            path,
            params,
            data,
            headers,
            cacheTtlMs,
            _retry: true,
          });
        }
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/login";
      }
    }

    if (!response.ok) {
      throw createHttpError(response.status, responseData);
    }

    return { data: responseData };
  };

  const promise = executeRequest().catch((error) => {
    if (cacheKey) {
      getRequestCache.delete(cacheKey);
    }
    throw error;
  });

  if (cacheKey) {
    getRequestCache.set(cacheKey, {
      promise,
      expiresAt: Date.now() + (cacheTtlMs ?? DEFAULT_GET_CACHE_TTL_MS),
    });
  }

  return promise;
};

export const httpClient = {
  defaults: {
    baseURL: API_BASE_URL,
  },
  get: (path, config = {}) => request({ method: "GET", path, params: config.params, headers: config.headers, cacheTtlMs: config.cacheTtlMs }),
  post: (path, data, config = {}) => {
    clearHttpCache(cachePrefixForPath(path));
    return request({ method: "POST", path, data, params: config.params, headers: config.headers });
  },
  patch: (path, data, config = {}) => {
    clearHttpCache(cachePrefixForPath(path));
    return request({ method: "PATCH", path, data, params: config.params, headers: config.headers });
  },
  put: (path, data, config = {}) => {
    clearHttpCache(cachePrefixForPath(path));
    return request({ method: "PUT", path, data, params: config.params, headers: config.headers });
  },
  delete: (path, config = {}) => {
    clearHttpCache(cachePrefixForPath(path));
    return request({ method: "DELETE", path, params: config.params, headers: config.headers });
  },
};

export const getApiBaseUrl = () => httpClient.defaults.baseURL;