"use client";

import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import {
  ApiRequestError,
  apiRequest as sendApiRequest,
  isLocalApiBaseOverrideEnabled,
  resolveInitialApiBase,
} from "../../lib/api-client";

const StudyOSContext = createContext(null);

function parseStoredOrg(value) {
  if (!value) return null;
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) return null;
  return parsed;
}

function isRefreshablePath(path) {
  return path !== "/auth/login" && path !== "/auth/register" && path !== "/auth/refresh";
}

export function StudyOSProvider({ children }) {
  const [apiBase, setApiBaseState] = useState(resolveInitialApiBase);
  const [token, setToken] = useState("");
  const [refreshTokenState, setRefreshTokenState] = useState("");
  const [email, setEmail] = useState("");
  const [organizations, setOrganizations] = useState([]);
  const [activeOrgId, setActiveOrgIdState] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const [canEditApiBase, setCanEditApiBase] = useState(false);

  const tokenRef = useRef("");
  const refreshTokenRef = useRef("");
  const apiBaseRef = useRef(apiBase);
  const activeOrgIdRef = useRef(activeOrgId);
  const refreshPromiseRef = useRef(null);

  useEffect(() => {
    tokenRef.current = token;
  }, [token]);

  useEffect(() => {
    refreshTokenRef.current = refreshTokenState;
  }, [refreshTokenState]);

  useEffect(() => {
    apiBaseRef.current = apiBase;
  }, [apiBase]);

  useEffect(() => {
    activeOrgIdRef.current = activeOrgId;
  }, [activeOrgId]);

  function syncStoredString(key, value) {
    if (typeof window === "undefined") return;
    if (value) {
      window.localStorage.setItem(key, value);
      return;
    }
    window.localStorage.removeItem(key);
  }

  function clearAuthState() {
    tokenRef.current = "";
    refreshTokenRef.current = "";
    activeOrgIdRef.current = null;
    refreshPromiseRef.current = null;
    setToken("");
    setRefreshTokenState("");
    setEmail("");
    setOrganizations([]);
    setActiveOrgIdState(null);
  }

  function applySession(payload, nextEmail = email) {
    const nextAccessToken = payload.access_token || "";
    const nextRefreshToken = payload.refresh_token || "";
    tokenRef.current = nextAccessToken;
    refreshTokenRef.current = nextRefreshToken;
    setToken(nextAccessToken);
    setRefreshTokenState(nextRefreshToken);
    setEmail(nextEmail);
  }

  function syncOrganizations(rows) {
    setOrganizations(rows);
    if (!rows.length) {
      activeOrgIdRef.current = null;
      setActiveOrgIdState(null);
      return rows;
    }
    setActiveOrgIdState((prev) => {
      const nextOrgId = rows.some((org) => org.id === prev) ? prev : rows[0].id;
      activeOrgIdRef.current = nextOrgId;
      return nextOrgId;
    });
    return rows;
  }

  function setActiveOrgId(nextOrgId) {
    activeOrgIdRef.current = nextOrgId;
    setActiveOrgIdState(nextOrgId);
  }

  async function loadOrganizations(accessToken, baseUrl = apiBaseRef.current) {
    if (!accessToken) {
      return syncOrganizations([]);
    }
    const rows = await sendApiRequest({
      baseUrl,
      token: accessToken,
      path: "/organizations/",
    });
    return syncOrganizations(rows);
  }

  async function refreshAccessToken() {
    if (refreshPromiseRef.current) {
      return refreshPromiseRef.current;
    }

    refreshPromiseRef.current = (async () => {
      const currentRefreshToken = refreshTokenRef.current;
      if (!currentRefreshToken) {
        clearAuthState();
        throw new Error("Session expired");
      }

      try {
        const payload = await sendApiRequest({
          baseUrl: apiBaseRef.current,
          method: "POST",
          path: "/auth/refresh",
          body: { refresh_token: currentRefreshToken },
        });
        applySession(payload);
        return payload.access_token || "";
      } catch (requestError) {
        clearAuthState();
        throw requestError;
      } finally {
        refreshPromiseRef.current = null;
      }
    })();

    return refreshPromiseRef.current;
  }

  async function requestWithAuth(params, { allowRefresh = true } = {}) {
    const requestToken = params.token ?? tokenRef.current;
    const requestParams = {
      ...params,
      baseUrl: params.baseUrl || apiBaseRef.current,
      token: requestToken,
      organizationId: params.organizationId ?? activeOrgIdRef.current,
    };

    try {
      return await sendApiRequest(requestParams);
    } catch (requestError) {
      if (
        !(requestError instanceof ApiRequestError) ||
        requestError.status !== 401 ||
        !allowRefresh ||
        !requestToken ||
        !refreshTokenRef.current ||
        !isRefreshablePath(requestParams.path)
      ) {
        throw requestError;
      }

      if (tokenRef.current && tokenRef.current !== requestToken) {
        return sendApiRequest({ ...requestParams, token: tokenRef.current });
      }

      const refreshedAccessToken = await refreshAccessToken();
      return sendApiRequest({ ...requestParams, token: refreshedAccessToken });
    }
  }

  async function refreshOrganizations(nextToken) {
    const accessToken = nextToken ?? tokenRef.current;
    if (!accessToken) {
      return syncOrganizations([]);
    }
    if (nextToken) {
      return loadOrganizations(nextToken);
    }
    const rows = await requestWithAuth({ path: "/organizations/" });
    return syncOrganizations(rows);
  }

  function setApiBase(nextBase) {
    if (!canEditApiBase) return;
    setApiBaseState(nextBase);
  }

  async function login({ userEmail, password }) {
    setLoading(true);
    try {
      const payload = await sendApiRequest({
        baseUrl: apiBaseRef.current,
        method: "POST",
        path: "/auth/login",
        body: { email: userEmail, password },
      });
      applySession(payload, userEmail);
      try {
        await loadOrganizations(payload.access_token, apiBaseRef.current);
      } catch (requestError) {
        clearAuthState();
        throw requestError;
      }
      return payload;
    } finally {
      setLoading(false);
    }
  }

  async function register({ userEmail, password }) {
    setLoading(true);
    try {
      const payload = await sendApiRequest({
        baseUrl: apiBaseRef.current,
        method: "POST",
        path: "/auth/register",
        body: { email: userEmail, password },
      });
      applySession(payload, userEmail);
      try {
        await loadOrganizations(payload.access_token, apiBaseRef.current);
      } catch (requestError) {
        clearAuthState();
        throw requestError;
      }
      return payload;
    } finally {
      setLoading(false);
    }
  }

  async function logout({ revokeAllSessions = false } = {}) {
    const requestLogout = () =>
      sendApiRequest({
        baseUrl: apiBaseRef.current,
        token: tokenRef.current,
        method: "POST",
        path: "/auth/logout",
        body: {
          ...(refreshTokenRef.current ? { refresh_token: refreshTokenRef.current } : {}),
          revoke_all_sessions: revokeAllSessions,
        },
      });

    try {
      if (!tokenRef.current && !refreshTokenRef.current) return;

      try {
        await requestLogout();
      } catch (requestError) {
        if (
          requestError instanceof ApiRequestError &&
          requestError.status === 401 &&
          refreshTokenRef.current
        ) {
          try {
            await refreshAccessToken();
            await requestLogout();
          } catch (_refreshError) {
            // Fall back to local cleanup if the session cannot be revoked remotely.
          }
        }
      }
    } finally {
      clearAuthState();
    }
  }

  useEffect(() => {
    if (typeof window === "undefined") return;

    const allowOverride = isLocalApiBaseOverrideEnabled();
    const cachedToken = window.localStorage.getItem("studyos_token") || "";
    const cachedRefreshToken = window.localStorage.getItem("studyos_refresh_token") || "";
    const cachedEmail = window.localStorage.getItem("studyos_email") || "";
    const cachedOrg = parseStoredOrg(window.localStorage.getItem("studyos_org_id"));

    tokenRef.current = cachedToken;
    refreshTokenRef.current = cachedRefreshToken;
    activeOrgIdRef.current = cachedOrg;

    setCanEditApiBase(allowOverride);
    setApiBaseState(resolveInitialApiBase({ allowOverride }));
    setToken(cachedToken);
    setRefreshTokenState(cachedRefreshToken);
    setEmail(cachedEmail);
    setActiveOrgIdState(cachedOrg);
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    if (typeof window === "undefined") return;
    if (canEditApiBase) {
      window.localStorage.setItem("studyos_api_base", apiBase);
      return;
    }
    window.localStorage.removeItem("studyos_api_base");
  }, [apiBase, canEditApiBase, hydrated]);

  useEffect(() => {
    if (!hydrated) return;
    syncStoredString("studyos_token", token);
  }, [hydrated, token]);

  useEffect(() => {
    if (!hydrated) return;
    syncStoredString("studyos_refresh_token", refreshTokenState);
  }, [hydrated, refreshTokenState]);

  useEffect(() => {
    if (!hydrated) return;
    syncStoredString("studyos_email", email);
  }, [email, hydrated]);

  useEffect(() => {
    if (!hydrated) return;
    if (typeof window === "undefined") return;
    if (activeOrgId) {
      window.localStorage.setItem("studyos_org_id", String(activeOrgId));
      return;
    }
    window.localStorage.removeItem("studyos_org_id");
  }, [activeOrgId, hydrated]);

  useEffect(() => {
    if (!token || !hydrated) return;
    refreshOrganizations().catch(() => {
      // Auth state is cleared centrally if refresh cannot recover.
    });
  }, [token, apiBase, hydrated]);

  const value = useMemo(
    () => ({
      apiBase,
      canEditApiBase,
      setApiBase,
      token,
      email,
      organizations,
      activeOrgId,
      setActiveOrgId,
      loading,
      hydrated,
      login,
      register,
      logout,
      refreshOrganizations,
      apiRequest: (params) =>
        requestWithAuth({
          ...params,
          baseUrl: apiBase,
          organizationId: params.organizationId ?? activeOrgId,
        }),
    }),
    [apiBase, canEditApiBase, token, email, organizations, activeOrgId, loading, hydrated]
  );

  return <StudyOSContext.Provider value={value}>{children}</StudyOSContext.Provider>;
}

export function useStudyOS() {
  const context = useContext(StudyOSContext);
  if (!context) throw new Error("useStudyOS must be used within StudyOSProvider");
  return context;
}
