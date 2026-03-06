"use client";

import { useEffect, useMemo, useState } from "react";
import SectionCard from "../../../components/ui/SectionCard";
import { useStudyOS } from "../../../components/providers/StudyOSProvider";

const STORAGE_KEY = "studyos_goals";

export default function GoalsPage() {
  const { activeOrgId, apiRequest } = useStudyOS();
  const [dashboard, setDashboard] = useState(null);
  const [goals, setGoals] = useState([]);
  const [goalForm, setGoalForm] = useState({ title: "", target: 100, progress: 0 });

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const parsed = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "[]");
      if (Array.isArray(parsed)) setGoals(parsed);
    } catch (_error) {
      setGoals([]);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(goals));
  }, [goals]);

  useEffect(() => {
    if (!activeOrgId) return;
    apiRequest({ path: "/analytics/dashboard?days=30" })
      .then(setDashboard)
      .catch(() => {
        setDashboard(null);
      });
  }, [activeOrgId]);

  const suggestedGoal = useMemo(() => {
    const done = dashboard?.progress?.completed_tasks ?? 0;
    const total = dashboard?.progress?.total_tasks ?? 0;
    return {
      title: "Complete all active tasks",
      progress: done,
      target: Math.max(total, 1),
    };
  }, [dashboard]);

  function addGoal(event) {
    event.preventDefault();
    if (!goalForm.title.trim()) return;
    setGoals((prev) => [
      ...prev,
      { id: `${Date.now()}-${Math.random().toString(16).slice(2)}`, ...goalForm, target: Number(goalForm.target) },
    ]);
    setGoalForm({ title: "", target: 100, progress: 0 });
  }

  function updateProgress(goalId, value) {
    setGoals((prev) =>
      prev.map((goal) => (goal.id === goalId ? { ...goal, progress: Math.max(0, Math.min(goal.target, value)) } : goal))
    );
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
      <SectionCard title="Create Goal" description="Track long-term milestones with measurable targets.">
        <form className="grid gap-3" onSubmit={addGoal}>
          <label className="grid gap-1 text-xs text-slate-400">
            Goal title
            <input
              value={goalForm.title}
              onChange={(event) => setGoalForm((prev) => ({ ...prev, title: event.target.value }))}
              placeholder="Learn 1000 words"
              className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
            />
          </label>
          <label className="grid gap-1 text-xs text-slate-400">
            Target
            <input
              type="number"
              min={1}
              value={goalForm.target}
              onChange={(event) => setGoalForm((prev) => ({ ...prev, target: Number(event.target.value) || 1 }))}
              className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
            />
          </label>
          <button type="submit" className="rounded-xl border border-primary/45 bg-primary/20 px-4 py-2 text-sm text-primary">
            Add goal
          </button>
        </form>

        <div className="mt-4 rounded-xl border border-secondary/30 bg-secondary/10 p-3 text-sm">
          <p className="font-medium">Suggested from analytics</p>
          <p className="text-slate-200">{suggestedGoal.title}</p>
          <p className="text-xs text-slate-400">
            {suggestedGoal.progress}/{suggestedGoal.target}
          </p>
        </div>
      </SectionCard>

      <SectionCard title="Goal Progress" description="Daily consistency feeds long-term growth.">
        {!goals.length ? (
          <p className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-slate-400">No goals yet.</p>
        ) : (
          <div className="grid gap-3">
            {goals.map((goal) => {
              const ratio = Math.round((goal.progress / goal.target) * 100);
              return (
                <article key={goal.id} className="rounded-xl border border-white/10 bg-white/5 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-medium">{goal.title}</p>
                    <p className="text-xs text-slate-400">{ratio}%</p>
                  </div>
                  <p className="mt-1 text-xs text-slate-400">
                    {goal.progress} / {goal.target}
                  </p>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10">
                    <div className="h-full rounded-full bg-gradient-to-r from-primary to-secondary" style={{ width: `${ratio}%` }} />
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={goal.target}
                    value={goal.progress}
                    onChange={(event) => updateProgress(goal.id, Number(event.target.value))}
                    className="mt-2 w-full"
                  />
                </article>
              );
            })}
          </div>
        )}
      </SectionCard>
    </div>
  );
}
