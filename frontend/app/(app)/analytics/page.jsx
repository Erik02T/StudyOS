"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import ChartCard from "../../../components/dashboard/ChartCard";
import DashboardCard from "../../../components/dashboard/DashboardCard";
import SectionCard from "../../../components/ui/SectionCard";
import { useStudyOS } from "../../../components/providers/StudyOSProvider";
import { toPercent, toFixed } from "../../../lib/formatters";

export default function AnalyticsPage() {
  const { activeOrgId, apiRequest } = useStudyOS();
  const [days, setDays] = useState(30);
  const [dashboard, setDashboard] = useState(null);
  const [events, setEvents] = useState([]);
  const [eventsPage, setEventsPage] = useState(1);
  const [eventsMeta, setEventsMeta] = useState({ page: 1, pages: 1, total: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadAnalytics() {
    if (!activeOrgId) return;
    setLoading(true);
    try {
      setError("");
      const [dashboardData, eventsData] = await Promise.all([
        apiRequest({ path: `/analytics/dashboard?days=${days}` }),
        apiRequest({ path: `/analytics/events?page=${eventsPage}&page_size=10` }),
      ]);
      setDashboard(dashboardData);
      setEvents(eventsData.items || []);
      setEventsMeta({ page: eventsData.page, pages: eventsData.pages, total: eventsData.total });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!activeOrgId) return;
    loadAnalytics();
  }, [activeOrgId, days, eventsPage]);

  return (
    <div className="grid gap-4">
      {error ? <p className="rounded-xl border border-danger/45 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p> : null}

      <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <DashboardCard
          label="Avg Productivity"
          value={toPercent(dashboard?.summary?.avg_productivity_index, 1)}
          hint={`${dashboard?.summary?.entries ?? 0} entries`}
          color="primary"
        />
        <DashboardCard
          label="Avg Focus"
          value={toPercent(dashboard?.summary?.avg_focus_score, 1)}
          hint={`Best bucket: ${dashboard?.heatmap?.best_time_bucket || "--"}`}
          color="secondary"
        />
        <DashboardCard
          label="Avg Study Minutes"
          value={toFixed(dashboard?.summary?.avg_study_minutes, 0)}
          hint="Per active log entry"
          color="success"
        />
        <DashboardCard
          label="Evolution"
          value={toFixed(dashboard?.progress?.evolution_score, 1)}
          hint="Global learning score"
          color="warning"
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <ChartCard
          title="Productivity + Focus Trend"
          description="Historical line across selected date window."
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
            <LineChart data={dashboard?.trend || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <Tooltip />
              <Line type="monotone" dataKey="productivity_index" stroke="#7B61FF" strokeWidth={3} dot={false} />
              <Line type="monotone" dataKey="focus_score" stroke="#4F9CF9" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Heatmap by Time Bucket" description="Where you perform better across the day.">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={dashboard?.heatmap?.heatmap || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis dataKey="bucket" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="avg_productivity_index" radius={[8, 8, 0, 0]}>
                {(dashboard?.heatmap?.heatmap || []).map((item, idx) => (
                  <Cell
                    key={`${item.bucket}-${idx}`}
                    fill={item.bucket === dashboard?.heatmap?.best_time_bucket ? "#34D399" : "#4F9CF9"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </section>

      <SectionCard title="Audit Events" description="Operational stream for sessions, reviews and org administration.">
        {loading ? (
          <p className="text-sm text-slate-400">Loading analytics events...</p>
        ) : !events.length ? (
          <p className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-slate-400">No events recorded yet.</p>
        ) : (
          <div className="grid gap-2">
            {events.map((event) => (
              <div key={event.id} className="rounded-xl border border-white/10 bg-white/5 p-3">
                <p className="text-sm font-medium">{event.event_type}</p>
                <p className="text-xs text-slate-400">
                  Entity: {event.entity_type || "--"}#{event.entity_id || "--"} · user {event.user_id || "system"}
                </p>
                <p className="text-xs text-slate-500">{new Date(event.created_at).toLocaleString()}</p>
              </div>
            ))}
          </div>
        )}
        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-400">
          <span>Total {eventsMeta.total}</span>
          <button
            type="button"
            disabled={eventsMeta.page <= 1}
            onClick={() => setEventsPage((prev) => Math.max(1, prev - 1))}
            className="rounded-lg border border-white/15 bg-white/5 px-3 py-1"
          >
            Prev
          </button>
          <span>
            Page {eventsMeta.page} / {eventsMeta.pages}
          </span>
          <button
            type="button"
            disabled={eventsMeta.page >= eventsMeta.pages}
            onClick={() => setEventsPage((prev) => Math.min(eventsMeta.pages, prev + 1))}
            className="rounded-lg border border-white/15 bg-white/5 px-3 py-1"
          >
            Next
          </button>
        </div>
      </SectionCard>
    </div>
  );
}
