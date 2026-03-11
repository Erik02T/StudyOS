const API_BASE = "http://127.0.0.1:8010";

function defaultDashboard() {
  return {
    user_email: "tester@studyos.dev",
    window_days: 30,
    summary: {
      window_days: 30,
      entries: 7,
      avg_completed_tasks: 2.4,
      avg_study_minutes: 58.2,
      avg_focus_score: 76.4,
      avg_productivity_index: 73.2,
    },
    consistency: {
      active_days: 6,
      consistency_rate: 85.7,
      current_streak: 3,
      best_streak: 9,
    },
    progress: {
      total_tasks: 12,
      completed_tasks: 7,
      completion_rate: 58.3,
      evolution_score: 74.4,
    },
    heatmap: {
      best_time_bucket: "evening",
      heatmap: [
        { bucket: "morning", sessions: 2, avg_productivity_index: 58, avg_focus_score: 63 },
        { bucket: "late_morning", sessions: 1, avg_productivity_index: 62, avg_focus_score: 66 },
        { bucket: "afternoon", sessions: 1, avg_productivity_index: 60, avg_focus_score: 64 },
        { bucket: "evening", sessions: 4, avg_productivity_index: 83, avg_focus_score: 86 },
        { bucket: "late_night", sessions: 1, avg_productivity_index: 49, avg_focus_score: 54 },
      ],
    },
    trend: [
      { date: "2026-03-01", completed_tasks: 2, study_minutes: 40, focus_score: 68, productivity_index: 64 },
      { date: "2026-03-02", completed_tasks: 1, study_minutes: 35, focus_score: 66, productivity_index: 60 },
      { date: "2026-03-03", completed_tasks: 3, study_minutes: 70, focus_score: 80, productivity_index: 78 },
      { date: "2026-03-04", completed_tasks: 2, study_minutes: 55, focus_score: 74, productivity_index: 72 },
      { date: "2026-03-05", completed_tasks: 4, study_minutes: 95, focus_score: 88, productivity_index: 90 },
    ],
    insight: "Seu melhor bloco recente e evening. Consistencia em 85.7% nos ultimos 30 dias.",
  };
}

function defaultSubscription() {
  return {
    organization_id: 1,
    plan: "free",
    status: "active",
    current_period_start: "2026-03-01",
    current_period_end: "2026-03-31",
    usage: [
      { metric: "tasks_created", used: 4, limit: 100, remaining: 96 },
      { metric: "sessions_finalized", used: 10, limit: 120, remaining: 110 },
      { metric: "reviews_answered", used: 7, limit: 120, remaining: 113 },
    ],
    stripe_customer_id: null,
    stripe_subscription_id: null,
  };
}

function withCorsHeaders() {
  return {
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
    "access-control-allow-headers": "Authorization,Content-Type,X-Organization-Id,Idempotency-Key",
    "content-type": "application/json",
  };
}

function jsonResponse(route, payload, status = 200) {
  return route.fulfill({
    status,
    headers: withCorsHeaders(),
    body: JSON.stringify(payload),
  });
}

function emptyResponse(route, status = 204) {
  return route.fulfill({ status, headers: withCorsHeaders(), body: "" });
}

function bearerToken(headers) {
  const authorization = headers.authorization || headers.Authorization || "";
  return authorization.startsWith("Bearer ") ? authorization.slice(7) : "";
}

function shouldRejectExpiredAccessToken(path, accessToken, expiredAccessToken) {
  if (!expiredAccessToken || accessToken !== expiredAccessToken) return false;
  return path !== "/auth/login" && path !== "/auth/register" && path !== "/auth/refresh";
}

function paginateMembers(rows, params) {
  const search = (params.get("search") || "").trim().toLowerCase();
  const role = (params.get("role") || "").trim().toLowerCase();
  const page = Math.max(1, Number(params.get("page") || 1));
  const pageSize = Math.min(100, Math.max(1, Number(params.get("page_size") || 10)));
  const sortBy = params.get("sort_by") || "created_at";
  const sortDir = params.get("sort_dir") === "asc" ? "asc" : "desc";

  let filtered = [...rows];
  if (role) filtered = filtered.filter((member) => member.role === role);
  if (search) {
    filtered = filtered.filter((member) => {
      const userId = String(member.user_id);
      return member.email.toLowerCase().includes(search) || member.role.toLowerCase().includes(search) || userId.includes(search);
    });
  }

  filtered.sort((a, b) => {
    let result = 0;
    if (sortBy === "email") result = a.email.localeCompare(b.email);
    else if (sortBy === "role") result = a.role.localeCompare(b.role);
    else result = a.created_at - b.created_at;
    return sortDir === "asc" ? result : result * -1;
  });

  const total = filtered.length;
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const offset = (page - 1) * pageSize;
  const items = filtered.slice(offset, offset + pageSize).map(({ user_id, email, role }) => ({ user_id, email, role }));

  return { items, total, page, page_size: pageSize, pages };
}

async function setupApiMock(page, options = {}) {
  const auth = {
    expiredAccessToken: options.auth?.expiredAccessToken || "",
    validRefreshToken: options.auth?.validRefreshToken || "seed-refresh-token",
    refreshedAccessToken: options.auth?.refreshedAccessToken || "refreshed-token",
    refreshedRefreshToken: options.auth?.refreshedRefreshToken || "refreshed-refresh-token",
    failRefresh: options.auth?.failRefresh || false,
  };
  let currentValidRefreshToken = auth.validRefreshToken;

  const state = {
    organizations: options.organizations || [{ id: 1, name: "Acme Workspace", slug: "acme-workspace", role: "owner" }],
    dashboard: options.dashboard || defaultDashboard(),
    reviews: options.reviews || [],
    subscription: options.subscription || defaultSubscription(),
    members:
      options.members ||
      [
        { user_id: 1, email: "owner@acme.com", role: "owner", created_at: 1 },
        { user_id: 2, email: "member@acme.com", role: "member", created_at: 2 },
      ],
    captured: {
      sessionsFinalize: [],
      reviewsAnswer: [],
      authRegister: [],
      authLogin: [],
      authRefresh: [],
      membersInvite: [],
      membersRole: [],
      membersRemove: [],
    },
  };

  await page.route(`${API_BASE}/**`, async (route) => {
    const request = route.request();
    const method = request.method();
    const url = new URL(request.url());
    const path = url.pathname;

    if (method === "OPTIONS") {
      return emptyResponse(route, 204);
    }

    const accessToken = bearerToken(request.headers());
    if (shouldRejectExpiredAccessToken(path, accessToken, auth.expiredAccessToken)) {
      return jsonResponse(route, { detail: "Could not validate credentials" }, 401);
    }

    if (method === "POST" && path === "/auth/register") {
      const payload = request.postDataJSON() || {};
      state.captured.authRegister.push(payload);
      return jsonResponse(route, { access_token: "register-token", refresh_token: "register-refresh", token_type: "bearer" }, 201);
    }

    if (method === "POST" && path === "/auth/login") {
      const payload = request.postDataJSON() || {};
      state.captured.authLogin.push(payload);
      return jsonResponse(route, { access_token: "login-token", refresh_token: "login-refresh", token_type: "bearer" });
    }

    if (method === "POST" && path === "/auth/refresh") {
      const payload = request.postDataJSON() || {};
      state.captured.authRefresh.push(payload);
      if (auth.failRefresh || payload.refresh_token !== currentValidRefreshToken) {
        return jsonResponse(route, { detail: "Invalid refresh token" }, 401);
      }
      currentValidRefreshToken = auth.refreshedRefreshToken;
      return jsonResponse(route, {
        access_token: auth.refreshedAccessToken,
        refresh_token: auth.refreshedRefreshToken,
        token_type: "bearer",
      });
    }

    if (method === "POST" && path === "/auth/request-email-verification") {
      return jsonResponse(route, { message: "verification requested", action_token: "verify-token" });
    }

    if (method === "POST" && path === "/auth/verify-email") {
      return jsonResponse(route, { message: "Email verified successfully" });
    }

    if (method === "POST" && path === "/auth/request-password-reset") {
      return jsonResponse(route, { message: "If your account exists, a reset token has been issued.", action_token: "reset-token" });
    }

    if (method === "POST" && path === "/auth/logout") {
      return jsonResponse(route, { message: "Logged out" });
    }

    if (method === "GET" && path === "/organizations/") {
      return jsonResponse(route, state.organizations);
    }

    if (method === "GET" && path === "/analytics/dashboard") {
      return jsonResponse(route, state.dashboard);
    }

    if (method === "GET" && path === "/analytics/events") {
      return jsonResponse(route, { items: [], total: 0, page: 1, page_size: 10, pages: 1 });
    }

    if (method === "GET" && path === "/reviews/due") {
      return jsonResponse(route, state.reviews);
    }

    if (method === "POST" && path === "/reviews/answer") {
      const payload = request.postDataJSON() || {};
      state.captured.reviewsAnswer.push(payload);
      return jsonResponse(route, {
        task_id: payload.task_id || 1,
        quality: payload.quality || 4,
        previous_interval: 1,
        new_interval: 3,
        previous_ease_factor: 2.5,
        new_ease_factor: 2.6,
        previous_mastery_level: 40,
        new_mastery_level: 54,
        next_review_date: "2026-03-09",
      });
    }

    if (method === "POST" && path === "/sessions/finalize") {
      const payload = request.postDataJSON() || {};
      state.captured.sessionsFinalize.push(payload);
      return jsonResponse(route, {
        message: "Session finalized and analytics updated",
        source: payload.source || "manual",
        performance_id: 99,
        date: "2026-03-06",
        completed_tasks: payload.completed_tasks ?? 1,
        study_minutes: payload.study_minutes ?? 25,
        focus_score: payload.focus_score ?? 80,
        productivity_index: payload.productivity_index ?? 75,
        time_block: payload.time_block ?? "19:00-21:00",
      });
    }

    if (method === "GET" && path === "/billing/subscription") {
      return jsonResponse(route, state.subscription);
    }

    if (method === "PATCH" && path === "/billing/subscription") {
      const payload = request.postDataJSON() || {};
      state.subscription.plan = payload.plan || state.subscription.plan;
      return jsonResponse(route, state.subscription);
    }

    if (path === "/organizations/1/members" && method === "GET") {
      const data = paginateMembers(state.members, url.searchParams);
      return jsonResponse(route, data);
    }

    if (path === "/organizations/1/members/invite" && method === "POST") {
      const payload = request.postDataJSON() || {};
      state.captured.membersInvite.push(payload);
      const exists = state.members.find((member) => member.email.toLowerCase() === String(payload.email || "").toLowerCase());
      if (!exists) {
        const nextId = Math.max(...state.members.map((member) => member.user_id), 0) + 1;
        state.members.push({
          user_id: nextId,
          email: payload.email,
          role: payload.role || "member",
          created_at: Date.now(),
        });
      }
      const created = state.members.find((member) => member.email.toLowerCase() === String(payload.email || "").toLowerCase());
      return jsonResponse(route, { user_id: created.user_id, email: created.email, role: created.role });
    }

    if (path.startsWith("/organizations/1/members/") && path.endsWith("/role") && method === "PATCH") {
      const payload = request.postDataJSON() || {};
      const memberUserId = Number(path.split("/")[4]);
      state.captured.membersRole.push({ memberUserId, ...payload });
      const member = state.members.find((item) => item.user_id === memberUserId);
      if (!member) return jsonResponse(route, { detail: "Membership not found" }, 404);
      member.role = payload.role || member.role;
      return jsonResponse(route, { user_id: member.user_id, email: member.email, role: member.role });
    }

    if (path.startsWith("/organizations/1/members/") && method === "DELETE") {
      const memberUserId = Number(path.split("/")[4]);
      state.captured.membersRemove.push({ memberUserId });
      state.members = state.members.filter((item) => item.user_id !== memberUserId);
      return emptyResponse(route, 204);
    }

    return jsonResponse(route, { detail: `Unmocked route: ${method} ${path}` }, 404);
  });

  return state;
}

async function seedAuthenticatedStorage(page, options = {}) {
  const {
    token = "seed-token",
    refreshToken = "seed-refresh-token",
    email = "owner@acme.com",
    orgId = 1,
    apiBase = API_BASE,
  } = options;

  await page.addInitScript(
    ({ tokenValue, refreshTokenValue, emailValue, orgIdValue, apiBaseValue }) => {
      window.localStorage.setItem("studyos_token", tokenValue);
      window.localStorage.setItem("studyos_refresh_token", refreshTokenValue);
      window.localStorage.setItem("studyos_email", emailValue);
      window.localStorage.setItem("studyos_org_id", String(orgIdValue));
      window.localStorage.setItem("studyos_api_base", apiBaseValue);
    },
    {
      tokenValue: token,
      refreshTokenValue: refreshToken,
      emailValue: email,
      orgIdValue: orgId,
      apiBaseValue: apiBase,
    }
  );
}

module.exports = {
  API_BASE,
  defaultDashboard,
  defaultSubscription,
  setupApiMock,
  seedAuthenticatedStorage,
};
