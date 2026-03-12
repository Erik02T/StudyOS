"use client";

const LOCAL_PUBLIC_API = "http://127.0.0.1:8010";
const MISSING_API_BASE_MESSAGE =
  "StudyOS API is not configured for this deployment. Set NEXT_PUBLIC_API_BASE_URL.";
const API_UNAVAILABLE_MESSAGE =
  "Cannot reach the StudyOS API. Check backend health, CORS, and NEXT_PUBLIC_API_BASE_URL.";

function isLocalBrowserHost() {
  if (typeof window === "undefined") return false;
  return window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
}

function getDefaultApiBase() {
  const env = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (env) return env;
  return isLocalBrowserHost() ? LOCAL_PUBLIC_API : "";
}

export function isLocalApiBaseOverrideEnabled() {
  return isLocalBrowserHost();
}

export function resolveInitialApiBase({ allowOverride = isLocalApiBaseOverrideEnabled() } = {}) {
  const fallback = getDefaultApiBase();
  if (typeof window === "undefined" || !allowOverride) return fallback;

  const cached = window.localStorage.getItem("studyos_api_base");
  if (!cached) return fallback;

  const cachedLocal = cached.includes("localhost") || cached.includes("127.0.0.1");
  return !isLocalBrowserHost() && cachedLocal ? fallback : cached;
}

export class ApiRequestError extends Error {
  constructor(message, { status = 0, payload = null } = {}) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.payload = payload;
  }
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
  if (!baseUrl) {
    throw new ApiRequestError(MISSING_API_BASE_MESSAGE);
  }

  let response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(organizationId ? { "X-Organization-Id": String(organizationId) } : {}),
        ...(headers || {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (_error) {
    throw new ApiRequestError(API_UNAVAILABLE_MESSAGE);
  }

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    let payload = null;
    try {
      payload = await response.json();
      detail = payload.detail || JSON.stringify(payload);
    } catch (_err) {
      // Keep fallback detail when the body is not JSON.
    }
    throw new ApiRequestError(detail, { status: response.status, payload });
  }

  if (response.status === 204) return null;
  return response.json();
}
