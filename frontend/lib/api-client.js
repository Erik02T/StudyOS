"use client";

const DEFAULT_PUBLIC_API = "https://studyos-api-staging.up.railway.app";

function getDefaultApiBase() {
  const env = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (env) return env;
  if (typeof window === "undefined") return DEFAULT_PUBLIC_API;
  const local = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
  return local ? "http://127.0.0.1:8010" : DEFAULT_PUBLIC_API;
}

export function resolveInitialApiBase() {
  if (typeof window === "undefined") return getDefaultApiBase();
  const cached = window.localStorage.getItem("studyos_api_base");
  const fallback = getDefaultApiBase();
  if (!cached) return fallback;
  const local = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
  const cachedLocal = cached.includes("localhost") || cached.includes("127.0.0.1");
  return !local && cachedLocal ? fallback : cached;
}

export async function apiRequest({
  baseUrl,
  token,
  organizationId,
  path,
  method = "GET",
  body,
  headers,
}) {
  const response = await fetch(`${baseUrl}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(organizationId ? { "X-Organization-Id": String(organizationId) } : {}),
      ...(headers || {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const payload = await response.json();
      detail = payload.detail || JSON.stringify(payload);
    } catch (_err) {
      // keep fallback detail
    }
    throw new Error(detail);
  }
  if (response.status === 204) return null;
  return response.json();
}
