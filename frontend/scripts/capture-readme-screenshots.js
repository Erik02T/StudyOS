const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const APP_URL = "http://127.0.0.1:4173";
const API_BASE = "http://127.0.0.1:8080";
const OUTPUT_DIR = path.resolve(__dirname, "../../docs/screenshots");

const state = {
  organizations: [
    {
      id: 1,
      name: "erik@gmail.com's Workspace",
      slug: "erik-workspace",
      role: "owner",
    },
  ],
  dashboard: {
    user_email: "erik@gmail.com",
    window_days: 30,
    summary: {
      window_days: 30,
      entries: 0,
      avg_completed_tasks: 0,
      avg_study_minutes: 0,
      avg_focus_score: 0,
      avg_productivity_index: 0,
    },
    consistency: {
      active_days: 0,
      consistency_rate: 0,
      current_streak: 0,
      best_streak: 0,
    },
    progress: {
      total_tasks: 0,
      completed_tasks: 0,
      completion_rate: 0,
      evolution_score: 0,
    },
    heatmap: {
      best_time_bucket: "morning",
      heatmap: [],
    },
    trend: [],
    insight: "",
  },
  reviews: [],
  subjects: [],
  tasks: [],
  subscription: {
    organization_id: 1,
    plan: "free",
    status: "active",
    current_period_start: "2026-03-01",
    current_period_end: "2026-03-31",
    usage: [
      { metric: "tasks_created_monthly", used: 0, limit: 150, remaining: 150 },
      { metric: "reviews_answered_monthly", used: 0, limit: 600, remaining: 600 },
      { metric: "sessions_finalized_monthly", used: 0, limit: 200, remaining: 200 },
    ],
    stripe_customer_id: null,
    stripe_subscription_id: null,
  },
  members: [
    {
      user_id: 3,
      email: "erik@gmail.com",
      role: "owner",
      created_at: 1,
    },
  ],
  events: [
    {
      id: 1,
      event_type: "auth.registered",
      entity_type: "user",
      entity_id: "3",
      user_id: 3,
      created_at: "2026-03-21T02:44:12Z",
    },
  ],
};

function withCorsHeaders() {
  return {
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
    "access-control-allow-headers": "Authorization,Content-Type,X-Organization-Id,Idempotency-Key",
    "content-type": "application/json",
  };
}

async function fulfillJson(route, payload, status = 200) {
  await route.fulfill({
    status,
    headers: withCorsHeaders(),
    body: JSON.stringify(payload),
  });
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

async function installMockApi(page) {
  await page.route(`${API_BASE}/**`, async (route) => {
    const request = route.request();
    const method = request.method();
    const url = new URL(request.url());
    const pathname = url.pathname;

    if (method === "OPTIONS") {
      await route.fulfill({ status: 204, headers: withCorsHeaders(), body: "" });
      return;
    }

    if (method === "GET" && pathname === "/organizations/") {
      await fulfillJson(route, state.organizations);
      return;
    }

    if (method === "GET" && pathname === "/analytics/dashboard") {
      await fulfillJson(route, state.dashboard);
      return;
    }

    if (method === "GET" && pathname === "/analytics/events") {
      await fulfillJson(route, {
        items: state.events,
        total: state.events.length,
        page: 1,
        page_size: 10,
        pages: 1,
      });
      return;
    }

    if (method === "GET" && pathname === "/reviews/due") {
      await fulfillJson(route, state.reviews);
      return;
    }

    if (method === "POST" && pathname === "/reviews/answer") {
      const payload = request.postDataJSON() || {};
      await fulfillJson(route, {
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
      return;
    }

    if (method === "POST" && pathname === "/sessions/finalize") {
      const payload = request.postDataJSON() || {};
      await fulfillJson(route, {
        message: "Session finalized and analytics updated",
        source: payload.source || "manual",
        performance_id: 99,
        date: "2026-03-21",
        completed_tasks: payload.completed_tasks ?? 1,
        study_minutes: payload.study_minutes ?? 25,
        focus_score: payload.focus_score ?? 80,
        productivity_index: 75,
        time_block: payload.time_block ?? "19:00-21:00",
      });
      return;
    }

    if (method === "POST" && pathname === "/planner/generate-plan") {
      const payload = request.postDataJSON() || {};
      await fulfillJson(route, {
        available_minutes: payload.available_minutes ?? 120,
        unused_minutes: 30,
        scheduled_reviews: [],
        scheduled_new_tasks: [],
        planning_context: {
          hour_focus_factor: 0.92,
          cognitive_budget: 0.78,
        },
      });
      return;
    }

    if (method === "GET" && pathname === "/subjects/") {
      await fulfillJson(route, state.subjects);
      return;
    }

    if (method === "POST" && pathname === "/subjects/") {
      const payload = request.postDataJSON() || {};
      const subject = {
        id: state.subjects.length + 1,
        name: payload.name || "Programming",
        importance_level: payload.importance_level ?? 3,
        difficulty: payload.difficulty ?? 3,
        category: payload.category || "general",
      };
      state.subjects.push(subject);
      await fulfillJson(route, subject, 201);
      return;
    }

    if (method === "GET" && pathname === "/tasks/") {
      await fulfillJson(route, state.tasks);
      return;
    }

    if (method === "POST" && pathname === "/tasks/") {
      const payload = request.postDataJSON() || {};
      const task = {
        id: state.tasks.length + 1,
        title: payload.title || "FastAPI auth hardening",
        subject_id: payload.subject_id ?? 1,
        estimated_time: payload.estimated_time ?? 30,
        mastery_level: payload.mastery_level ?? 0,
        status: payload.status || "pending",
      };
      state.tasks.push(task);
      await fulfillJson(route, task, 201);
      return;
    }

    if (method === "PUT" && pathname.startsWith("/tasks/")) {
      const taskId = Number(pathname.split("/")[2]);
      const payload = request.postDataJSON() || {};
      const task = state.tasks.find((item) => item.id === taskId);
      if (!task) {
        await fulfillJson(route, { detail: "Task not found" }, 404);
        return;
      }
      Object.assign(task, payload);
      await fulfillJson(route, task);
      return;
    }

    if (method === "GET" && pathname === "/billing/subscription") {
      await fulfillJson(route, state.subscription);
      return;
    }

    if (method === "PATCH" && pathname === "/billing/subscription") {
      const payload = request.postDataJSON() || {};
      state.subscription.plan = payload.plan || state.subscription.plan;
      await fulfillJson(route, state.subscription);
      return;
    }

    if (method === "POST" && pathname === "/auth/request-email-verification") {
      await fulfillJson(route, {
        message: "verification requested",
        action_token: "verify-token",
      });
      return;
    }

    if (method === "POST" && pathname === "/auth/verify-email") {
      await fulfillJson(route, { message: "Email verified successfully" });
      return;
    }

    if (method === "POST" && pathname === "/auth/request-password-reset") {
      await fulfillJson(route, {
        message: "If your account exists, a reset token has been issued.",
        action_token: "reset-token",
      });
      return;
    }

    if (pathname === "/organizations/1/members" && method === "GET") {
      await fulfillJson(route, paginateMembers(state.members, url.searchParams));
      return;
    }

    if (pathname === "/organizations/1/members/invite" && method === "POST") {
      const payload = request.postDataJSON() || {};
      const nextId = Math.max(...state.members.map((member) => member.user_id), 0) + 1;
      const member = {
        user_id: nextId,
        email: payload.email || "member@email.com",
        role: payload.role || "member",
        created_at: Date.now(),
      };
      state.members.push(member);
      await fulfillJson(route, member);
      return;
    }

    if (pathname.startsWith("/organizations/1/members/") && pathname.endsWith("/role") && method === "PATCH") {
      const payload = request.postDataJSON() || {};
      const memberId = Number(pathname.split("/")[4]);
      const member = state.members.find((item) => item.user_id === memberId);
      if (!member) {
        await fulfillJson(route, { detail: "Membership not found" }, 404);
        return;
      }
      member.role = payload.role || member.role;
      await fulfillJson(route, member);
      return;
    }

    if (pathname.startsWith("/organizations/1/members/") && method === "DELETE") {
      const memberId = Number(pathname.split("/")[4]);
      const index = state.members.findIndex((item) => item.user_id === memberId);
      if (index >= 0) {
        state.members.splice(index, 1);
      }
      await route.fulfill({ status: 204, headers: withCorsHeaders(), body: "" });
      return;
    }

    await fulfillJson(route, { detail: `Unmocked route: ${method} ${pathname}` }, 404);
  });
}

async function seedSession(context) {
  await context.addInitScript(
    ({ apiBase }) => {
      window.localStorage.setItem("studyos_token", "seed-token");
      window.localStorage.setItem("studyos_refresh_token", "seed-refresh-token");
      window.localStorage.setItem("studyos_email", "erik@gmail.com");
      window.localStorage.setItem("studyos_org_id", "1");
      window.localStorage.setItem("studyos_api_base", apiBase);
      window.localStorage.setItem("studyos_goals", "[]");
    },
    { apiBase: API_BASE }
  );
}

async function capture(page, pathname, fileName, waitForText) {
  await page.goto(`${APP_URL}${pathname}`, { waitUntil: "networkidle" });
  if (waitForText) {
    await page.getByRole("heading", { name: waitForText, exact: true }).waitFor({ timeout: 15000 });
  }
  await page.evaluate(() => {
    const labels = Array.from(document.querySelectorAll("label"));
    const apiLabel = labels.find((element) => element.textContent?.trim().toLowerCase() === "api base");
    const wrapper = apiLabel?.parentElement;
    if (wrapper) wrapper.remove();
  });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: path.join(OUTPUT_DIR, fileName),
    type: "png",
  });
}

async function main() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1820, height: 920 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();

  await seedSession(context);
  await installMockApi(page);

  await capture(page, "/dashboard", "dashboard.png", "Dashboard");
  await capture(page, "/planner", "planner.png", "Planner");
  await capture(page, "/library", "library.png", "Library");
  await capture(page, "/study-session", "study-session.png", "Study Session");
  await capture(page, "/analytics", "analytics.png", "Analytics");
  await capture(page, "/goals", "goals.png", "Goals");
  await capture(page, "/settings", "settings.png", "Settings");

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
