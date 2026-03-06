"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import DashboardCard from "../../../components/dashboard/DashboardCard";
import ChartCard from "../../../components/dashboard/ChartCard";
import SectionCard from "../../../components/ui/SectionCard";
import ToastStack from "../../../components/ui/ToastStack";
import { useStudyOS } from "../../../components/providers/StudyOSProvider";
import { toPercent, toFixed } from "../../../lib/formatters";
import { useNotify } from "../../../lib/use-notify";

export default function DashboardPage() {
  const { activeOrgId, apiRequest } = useStudyOS();
  const [days, setDays] = useState(30);
  const [dashboard, setDashboard] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [reviewQuality, setReviewQuality] = useState({});
  const [sessionForm, setSessionForm] = useState({
    completed_tasks: 1,
    study_minutes: 45,
    focus_score: 75,
    time_block: "19:00-21:00",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { items: toasts, push } = useNotify();

  async function loadData() {
    if (!activeOrgId) return;
    setLoading(true);
    try {
      setError("");
      const [dashboardData, dueReviews] = await Promise.all([
        apiRequest({ path: `/analytics/dashboard?days=${days}` }),
        apiRequest({ path: "/reviews/due" }),
      ]);
      setDashboard(dashboardData);
      setReviews(dueReviews);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!activeOrgId) return;
    loadData();
  }, [activeOrgId, days]);

  const weeklyTrend = useMemo(() => {
    const rows = dashboard?.trend || [];
    return rows.slice(-7);
  }, [dashboard]);

  async function finalizeManualSession(event) {
    event.preventDefault();
    if (!activeOrgId) return;
    try {
      setError("");
      await apiRequest({
        method: "POST",
        path: "/sessions/finalize",
        body: { source: "manual", ...sessionForm },
      });
      push("ok", "Session finalized and analytics updated.");
      await loadData();
    } catch (requestError) {
      setError(requestError.message);
      push("error", requestError.message);
    }
  }

  async function finalizeReview(review) {
    if (!activeOrgId) return;
    const quality = Number(reviewQuality[review.task_id] ?? 4);
    try {
      setError("");
      await apiRequest({
        method: "POST",
        path: "/reviews/answer",
        body: { task_id: review.task_id, quality },
      });
      await apiRequest({
        method: "POST",
        path: "/sessions/finalize",
        body: {
          source: "review",
          quality,
          study_minutes: review.estimated_time || 0,
          time_block: sessionForm.time_block,
        },
      });
      push("ok", `Review completed: ${review.title}`);
      await loadData();
    } catch (requestError) {
      setError(requestError.message);
      push("error", requestError.message);
    }
  }

  if (!activeOrgId) {
    return (
      <SectionCard title="No Organization Selected" description="Create or select a workspace to load your dashboard.">
        <p className="text-sm text-slate-300">Login and make sure at least one organization is available in your account.</p>
      </SectionCard>
    );
  }

  return (
    <div className="grid gap-4 lg:gap-5">
      {error ? <p className="rounded-xl border border-danger/45 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p> : null}

      <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <DashboardCard
          label="Evolution Score"
          value={toFixed(dashboard?.progress?.evolution_score, 1)}
          hint="Composite score from consistency, productivity and completion."
        />
        <DashboardCard
          label="Consistency"
          value={toPercent(dashboard?.consistency?.consistency_rate, 1)}
          hint={`${dashboard?.consistency?.active_days || 0} active days in the window.`}
          color="success"
        />
        <DashboardCard
          label="Current Streak"
          value={`${dashboard?.consistency?.current_streak ?? 0} days`}
          hint={`Best streak: ${dashboard?.consistency?.best_streak ?? 0} days`}
          color="secondary"
        />
        <DashboardCard
          label="Completion"
          value={toPercent(dashboard?.progress?.completion_rate, 1)}
          hint={`${dashboard?.progress?.completed_tasks ?? 0}/${dashboard?.progress?.total_tasks ?? 0} tasks done`}
          color="warning"
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <ChartCard
          title="Productivity Trend"
          description={`Rolling window of ${days} days.`}
          actions={
            <div className="flex items-center gap-2">
              <label className="text-xs text-slate-400">Days</label>
              <input
                type="number"
                min={7}
                max={365}
                value={days}
                onChange={(event) => setDays(Number(event.target.value) || 30)}
                className="w-20 rounded-lg border border-white/10 bg-background px-2 py-1 text-xs"
              />
            </div>
          }
        >
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={dashboard?.trend || []}>
              <defs>
                <linearGradient id="trendColor" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#7B61FF" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#7B61FF" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <Tooltip />
              <Area type="monotone" dataKey="productivity_index" stroke="#7B61FF" fillOpacity={1} fill="url(#trendColor)" />
              <Line type="monotone" dataKey="focus_score" stroke="#4F9CF9" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Weekly Study Minutes" description="Last 7 entries from your timeline.">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={weeklyTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <Tooltip />
              <Line type="monotone" dataKey="study_minutes" stroke="#34D399" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <SectionCard
          title="Due Reviews"
          description="Answer reviews to feed spaced repetition and auto-log performance."
          actions={
            <Link href="/review" className="rounded-lg border border-white/15 bg-white/5 px-3 py-1.5 text-xs">
              Open Review Mode
            </Link>
          }
        >
          {!reviews.length ? (
            <p className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-slate-400">No reviews due right now.</p>
          ) : (
            <ul className="space-y-2">
              {reviews.map((review) => (
                <li
                  key={review.task_id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/5 p-3"
                >
                  <div>
                    <p className="font-medium">{review.title}</p>
                    <p className="text-xs text-slate-400">
                      {review.subject} · {review.category} · {review.estimated_time} min
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <select
                      value={reviewQuality[review.task_id] ?? 4}
                      onChange={(event) =>
                        setReviewQuality((prev) => ({ ...prev, [review.task_id]: Number(event.target.value) }))
                      }
                      className="rounded-lg border border-white/15 bg-background px-2 py-1 text-xs"
                    >
                      <option value={1}>Again</option>
                      <option value={2}>Hard</option>
                      <option value={4}>Good</option>
                      <option value={5}>Easy</option>
                    </select>
                    <button
                      type="button"
                      onClick={() => finalizeReview(review)}
                      className="rounded-lg border border-primary/45 bg-primary/20 px-3 py-1.5 text-xs text-primary"
                    >
                      Finalize
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </SectionCard>

        <SectionCard title="Finalize Session" description="Manual logging when you finish a focus block.">
          <form className="grid gap-3" onSubmit={finalizeManualSession}>
            <label className="grid gap-1 text-xs text-slate-400">
              Completed tasks
              <input
                type="number"
                min={0}
                value={sessionForm.completed_tasks}
                onChange={(event) => setSessionForm((prev) => ({ ...prev, completed_tasks: Number(event.target.value) }))}
                className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
              />
            </label>
            <label className="grid gap-1 text-xs text-slate-400">
              Study minutes
              <input
                type="number"
                min={0}
                value={sessionForm.study_minutes}
                onChange={(event) => setSessionForm((prev) => ({ ...prev, study_minutes: Number(event.target.value) }))}
                className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
              />
            </label>
            <label className="grid gap-1 text-xs text-slate-400">
              Focus score
              <input
                type="number"
                min={0}
                max={100}
                value={sessionForm.focus_score}
                onChange={(event) => setSessionForm((prev) => ({ ...prev, focus_score: Number(event.target.value) }))}
                className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
              />
            </label>
            <label className="grid gap-1 text-xs text-slate-400">
              Time block
              <input
                value={sessionForm.time_block}
                onChange={(event) => setSessionForm((prev) => ({ ...prev, time_block: event.target.value }))}
                className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
              />
            </label>
            <button
              type="submit"
              disabled={loading}
              className="rounded-xl border border-success/45 bg-success/20 px-4 py-2 text-sm text-success disabled:opacity-60"
            >
              {loading ? "Saving..." : "Finalize Session"}
            </button>
          </form>
        </SectionCard>
      </section>

      <ToastStack items={toasts} />
    </div>
  );
}
