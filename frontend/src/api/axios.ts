import axios, {
  type AxiosError,
  type InternalAxiosRequestConfig,
} from "axios";
import { getAccessToken, setAccessToken } from "../auth/tokenStore";
import type { TokenResponse } from "../types";

const configuredUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
const normalizedUrl = configuredUrl.replace(/\/+$/, "");
const baseURL = normalizedUrl.endsWith("/api/v1")
  ? normalizedUrl
  : `${normalizedUrl}/api/v1`;

export const api = axios.create({
  baseURL,
  withCredentials: true,
  headers: { "Content-Type": "application/json", Accept: "application/json" },
});

const refreshClient = axios.create({ baseURL, withCredentials: true });
let refreshInFlight: Promise<TokenResponse> | null = null;

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean };

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetriableConfig | undefined;
    const url = config?.url ?? "";
    if (
      error.response?.status !== 401 ||
      !config ||
      config._retry ||
      url.startsWith("/auth/")
    ) {
      return Promise.reject(error);
    }

    config._retry = true;
    try {
      refreshInFlight ??= refreshClient
        .post<TokenResponse>("/auth/refresh")
        .then(({ data }) => data)
        .finally(() => {
          refreshInFlight = null;
        });
      const data = await refreshInFlight;
      setAccessToken(data.access_token);
      config.headers.Authorization = `Bearer ${data.access_token}`;
      return await api(config);
    } catch (refreshError) {
      setAccessToken(null);
      window.dispatchEvent(new Event("subastagro:session-expired"));
      return Promise.reject(refreshError);
    }
  },
);

export function getApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail: unknown = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) =>
          typeof item?.msg === "string" ? item.msg : "Datos no válidos",
        )
        .join(". ");
    }
    if (!error.response) return "No fue posible conectar con el servidor.";
    return `Error HTTP ${error.response.status}. Intenta nuevamente.`;
  }
  return error instanceof Error ? error.message : "Ocurrió un error inesperado.";
}
