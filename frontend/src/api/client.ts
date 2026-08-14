const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

const ACCESS_KEY = "mrpc_access";
const REFRESH_KEY = "mrpc_refresh";
const EMAIL_KEY = "mrpc_email";

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

export function getUserEmail(): string | null {
  return localStorage.getItem(EMAIL_KEY);
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(EMAIL_KEY);
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    const detail = extractMessage(body);
    super(detail || `Request failed with status ${status}`);
    this.status = status;
    this.body = body;
  }
}

function extractMessage(body: unknown): string | null {
  if (!body || typeof body !== "object") return null;
  const obj = body as Record<string, unknown>;
  if (typeof obj.detail === "string") return obj.detail;
  // DRF field errors: { field: ["message", ...] }
  const firstKey = Object.keys(obj)[0];
  if (firstKey) {
    const value = obj[firstKey];
    if (Array.isArray(value) && typeof value[0] === "string") {
      return `${firstKey}: ${value[0]}`;
    }
  }
  return null;
}

async function refreshAccessToken(): Promise<string> {
  const refresh = getRefreshToken();
  if (!refresh) throw new ApiError(401, { detail: "Not authenticated." });

  const res = await fetch(`${API_BASE_URL}/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  if (!res.ok) {
    clearTokens();
    throw new ApiError(res.status, await safeJson(res));
  }

  const data = await res.json();
  localStorage.setItem(ACCESS_KEY, data.access);
  return data.access;
}

async function safeJson(res: Response): Promise<unknown> {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const doRequest = async (accessToken: string | null): Promise<Response> => {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
    return fetch(`${API_BASE_URL}${path}`, {
      method: options.method || "GET",
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    });
  };

  let res = await doRequest(getAccessToken());

  if (res.status === 401 && getRefreshToken()) {
    try {
      const newAccess = await refreshAccessToken();
      res = await doRequest(newAccess);
    } catch {
      clearTokens();
      window.location.href = "/login";
      throw new ApiError(401, { detail: "Session expired. Please log in again." });
    }
  }

  if (res.status === 204) return undefined as T;

  const data = await safeJson(res);
  if (!res.ok) throw new ApiError(res.status, data);
  return data as T;
}

export async function login(email: string, password: string) {
  const res = await fetch(`${API_BASE_URL}/auth/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await safeJson(res);
  if (!res.ok) throw new ApiError(res.status, data);
  const { access, refresh } = data as { access: string; refresh: string };
  setTokens(access, refresh);
  localStorage.setItem(EMAIL_KEY, email);
}

export async function register(email: string, password: string) {
  const res = await fetch(`${API_BASE_URL}/auth/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await safeJson(res);
  if (!res.ok) throw new ApiError(res.status, data);
  const { access, refresh } = data as { access: string; refresh: string };
  setTokens(access, refresh);
  localStorage.setItem(EMAIL_KEY, email);
}

export function logout() {
  clearTokens();
}

export async function fetchCurrentUser(): Promise<{ id: number; email: string }> {
  return apiFetch<{ id: number; email: string }>("/auth/me/");
}
