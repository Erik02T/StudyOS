"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { apiRequest, resolveInitialApiBase } from "../../lib/api-client";

const StudyOSContext = createContext(null);

function parseStoredOrg(value) {
  if (!value) return null;
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) return null;
  return parsed;
}

export function StudyOSProvider({ children }) {
  const [apiBase, setApiBase] = useState(resolveInitialApiBase());
  const [token, setToken] = useState("");
  const [refreshToken, setRefreshToken] = useState("");
  const [email, setEmail] = useState("");
  const [organizations, setOrganizations] = useState([]);
  const [activeOrgId, setActiveOrgId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const cachedToken = window.localStorage.getItem("studyos_token") || "";
    const cachedRefreshToken = window.localStorage.getItem("studyos_refresh_token") || "";
    const cachedEmail = window.localStorage.getItem("studyos_email") || "";
    const cachedOrg = parseStoredOrg(window.localStorage.getItem("studyos_org_id"));
    setToken(cachedToken);
    setRefreshToken(cachedRefreshToken);
    setEmail(cachedEmail);
    setActiveOrgId(cachedOrg);
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem("studyos_api_base", apiBase);
  }, [apiBase]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem("studyos_token", token);
  }, [token]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem("studyos_refresh_token", refreshToken);
  }, [refreshToken]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem("studyos_email", email);
  }, [email]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (activeOrgId) {
      window.localStorage.setItem("studyos_org_id", String(activeOrgId));
      return;
    }
    window.localStorage.removeItem("studyos_org_id");
  }, [activeOrgId]);

  async function refreshOrganizations(nextToken = token) {
    if (!nextToken) {
      setOrganizations([]);
      setActiveOrgId(null);
      return [];
    }
    const rows = await apiRequest({ baseUrl: apiBase, token: nextToken, path: "/organizations/" });
    setOrganizations(rows);
    if (!rows.length) {
      setActiveOrgId(null);
      return rows;
    }
    setActiveOrgId((prev) => (rows.some((org) => org.id === prev) ? prev : rows[0].id));
    return rows;
  }

  async function login({ userEmail, password }) {
    setLoading(true);
    try {
      const payload = await apiRequest({
        baseUrl: apiBase,
        method: "POST",
        path: "/auth/login",
        body: { email: userEmail, password },
      });
      setToken(payload.access_token);
      setRefreshToken(payload.refresh_token || "");
      setEmail(userEmail);
      await refreshOrganizations(payload.access_token);
      return payload;
    } finally {
      setLoading(false);
    }
  }

  async function register({ userEmail, password }) {
    setLoading(true);
    try {
      const payload = await apiRequest({
        baseUrl: apiBase,
        method: "POST",
        path: "/auth/register",
        body: { email: userEmail, password },
      });
      setToken(payload.access_token);
      setRefreshToken(payload.refresh_token || "");
      setEmail(userEmail);
      await refreshOrganizations(payload.access_token);
      return payload;
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    if (refreshToken) {
      apiRequest({
        baseUrl: apiBase,
        token,
        method: "POST",
        path: "/auth/logout",
        body: { refresh_token: refreshToken },
      }).catch(() => {
        // Local cleanup still happens even if remote logout fails.
      });
    }
    setToken("");
    setRefreshToken("");
    setEmail("");
    setOrganizations([]);
    setActiveOrgId(null);
  }

  useEffect(() => {
    if (!token || !hydrated) return;
    refreshOrganizations(token).catch(() => {
      // keep session but avoid crash in layout
    });
  }, [token, apiBase, hydrated]);

  const value = useMemo(
    () => ({
      apiBase,
      setApiBase,
      token,
      refreshToken,
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
      apiRequest: (params) => apiRequest({ ...params, baseUrl: apiBase, token, organizationId: activeOrgId }),
    }),
    [apiBase, token, refreshToken, email, organizations, activeOrgId, loading, hydrated]
  );

  return <StudyOSContext.Provider value={value}>{children}</StudyOSContext.Provider>;
}

export function useStudyOS() {
  const context = useContext(StudyOSContext);
  if (!context) throw new Error("useStudyOS must be used within StudyOSProvider");
  return context;
}
