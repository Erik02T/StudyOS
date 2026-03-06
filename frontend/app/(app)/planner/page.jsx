"use client";

import { useMemo, useState } from "react";
import { WandSparkles } from "lucide-react";
import SectionCard from "../../../components/ui/SectionCard";
import { useStudyOS } from "../../../components/providers/StudyOSProvider";

export default function PlannerPage() {
  const { activeOrgId, apiRequest } = useStudyOS();
  const [form, setForm] = useState({
    available_minutes: 120,
    time_block: "19:00-21:00",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [plan, setPlan] = useState(null);

  const totalScheduled = useMemo(() => {
    if (!plan) return 0;
    const reviewMinutes = (plan.scheduled_reviews || []).reduce((sum, item) => sum + (item.estimated_time || 0), 0);
    const newMinutes = (plan.scheduled_new_tasks || []).reduce((sum, item) => sum + (item.estimated_time || 0), 0);
    return reviewMinutes + newMinutes;
  }, [plan]);

  async function generatePlan(event) {
    event.preventDefault();
    if (!activeOrgId) return;
    try {
      setLoading(true);
      setError("");
      const payload = await apiRequest({
        method: "POST",
        path: "/planner/generate-plan",
        body: {
          available_minutes: Number(form.available_minutes),
          time_block: form.time_block,
        },
      });
      setPlan(payload);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  if (!activeOrgId) {
    return (
      <SectionCard title="Planner unavailable" description="Select an organization first.">
        <p className="text-sm text-slate-300">The planner depends on workspace context and your study data.</p>
      </SectionCard>
    );
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
      <SectionCard
        title="Generate Daily Plan"
        description="Cognitive load cap + category balancing + time-block focus."
      >
        <form onSubmit={generatePlan} className="grid gap-3">
          <label className="grid gap-1 text-xs text-slate-400">
            Available minutes
            <input
              type="number"
              min={30}
              max={960}
              value={form.available_minutes}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, available_minutes: Number(event.target.value) || 120 }))
              }
              className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
            />
          </label>
          <label className="grid gap-1 text-xs text-slate-400">
            Preferred time block
            <input
              value={form.time_block}
              onChange={(event) => setForm((prev) => ({ ...prev, time_block: event.target.value }))}
              className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
            />
          </label>
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-primary/45 bg-primary/20 px-4 py-2 text-sm text-primary"
          >
            <WandSparkles size={15} />
            {loading ? "Generating..." : "Generate plan"}
          </button>
        </form>
        {error ? <p className="mt-3 rounded-xl border border-danger/45 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p> : null}
      </SectionCard>

      <SectionCard title="Plan Output" description="Daily schedule assembled by Study Engine.">
        {!plan ? (
          <p className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-slate-400">
            Generate a plan to see scheduled reviews, new tasks and planner context.
          </p>
        ) : (
          <div className="grid gap-4">
            <div className="grid gap-2 md:grid-cols-3">
              <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                <p className="text-xs text-slate-400">Available</p>
                <p className="text-xl font-semibold">{plan.available_minutes} min</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                <p className="text-xs text-slate-400">Scheduled</p>
                <p className="text-xl font-semibold">{totalScheduled} min</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                <p className="text-xs text-slate-400">Unused</p>
                <p className="text-xl font-semibold">{plan.unused_minutes} min</p>
              </div>
            </div>

            <div>
              <p className="mb-2 text-xs uppercase tracking-[0.2em] text-slate-400">Scheduled Reviews</p>
              {!plan.scheduled_reviews?.length ? (
                <p className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-slate-400">No due reviews selected.</p>
              ) : (
                <ul className="space-y-2">
                  {plan.scheduled_reviews.map((item) => (
                    <li key={item.task_id} className="rounded-xl border border-white/10 bg-white/5 p-3">
                      <p className="font-medium">{item.title}</p>
                      <p className="text-xs text-slate-400">
                        {item.subject} · {item.estimated_time} min · interval {item.review_interval_days}d
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div>
              <p className="mb-2 text-xs uppercase tracking-[0.2em] text-slate-400">New Tasks</p>
              {!plan.scheduled_new_tasks?.length ? (
                <p className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-slate-400">No new tasks fit current constraints.</p>
              ) : (
                <ul className="space-y-2">
                  {plan.scheduled_new_tasks.map((item) => (
                    <li key={item.task_id} className="rounded-xl border border-white/10 bg-white/5 p-3">
                      <p className="font-medium">{item.title}</p>
                      <p className="text-xs text-slate-400">
                        {item.subject} · {item.category} · priority {item.priority_score.toFixed(2)}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="rounded-xl border border-secondary/30 bg-secondary/10 p-3 text-xs text-slate-200">
              <p className="font-medium">AI Suggestion</p>
              <p className="mt-1">
                Best focus factor for this plan: {plan.planning_context?.hour_focus_factor} with cognitive budget of{" "}
                {plan.planning_context?.cognitive_budget}.
              </p>
            </div>
          </div>
        )}
      </SectionCard>
    </div>
  );
}
