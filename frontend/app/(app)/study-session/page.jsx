"use client";

import { useMemo, useState } from "react";
import SectionCard from "../../../components/ui/SectionCard";
import StudyTimer from "../../../components/study/StudyTimer";
import ToastStack from "../../../components/ui/ToastStack";
import { useStudyOS } from "../../../components/providers/StudyOSProvider";
import { useNotify } from "../../../lib/use-notify";

export default function StudySessionPage() {
  const { activeOrgId, apiRequest } = useStudyOS();
  const [topic, setTopic] = useState("Japanese Kanji");
  const [timerMinutes, setTimerMinutes] = useState(25);
  const [form, setForm] = useState({
    completed_tasks: 1,
    study_minutes: 25,
    focus_score: 80,
    quality: 4,
    time_block: "19:00-21:00",
  });
  const [saving, setSaving] = useState(false);
  const [lastResult, setLastResult] = useState(null);
  const [error, setError] = useState("");
  const { items: toasts, push } = useNotify();

  const canSubmit = useMemo(() => Boolean(activeOrgId && !saving), [activeOrgId, saving]);

  async function finalizeSession(source = "manual") {
    if (!activeOrgId) return;
    try {
      setSaving(true);
      setError("");
      const payload = await apiRequest({
        method: "POST",
        path: "/sessions/finalize",
        body: { source, ...form },
      });
      setLastResult(payload);
      push("ok", "Study session finalized.");
    } catch (requestError) {
      setError(requestError.message);
      push("error", requestError.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
      <SectionCard title="Focus Mode" description={`Topic: ${topic}`}>
        <div className="grid gap-3">
          <label className="grid gap-1 text-xs text-slate-400">
            Topic
            <input
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
            />
          </label>
          <label className="grid gap-1 text-xs text-slate-400">
            Timer minutes
            <input
              type="number"
              min={5}
              max={120}
              value={timerMinutes}
              onChange={(event) => {
                const value = Number(event.target.value) || 25;
                setTimerMinutes(value);
                setForm((prev) => ({ ...prev, study_minutes: value }));
              }}
              className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
            />
          </label>
          <StudyTimer
            initialMinutes={timerMinutes}
            onComplete={() => {
              push("ok", "Timer finished.");
            }}
          />
        </div>
      </SectionCard>

      <SectionCard title="Session Actions" description="Finalize and log performance automatically.">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            finalizeSession("manual");
          }}
          className="grid gap-3"
        >
          <label className="grid gap-1 text-xs text-slate-400">
            Completed tasks
            <input
              type="number"
              min={0}
              value={form.completed_tasks}
              onChange={(event) => setForm((prev) => ({ ...prev, completed_tasks: Number(event.target.value) }))}
              className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
            />
          </label>
          <label className="grid gap-1 text-xs text-slate-400">
            Focus score
            <input
              type="number"
              min={0}
              max={100}
              value={form.focus_score}
              onChange={(event) => setForm((prev) => ({ ...prev, focus_score: Number(event.target.value) }))}
              className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
            />
          </label>
          <label className="grid gap-1 text-xs text-slate-400">
            Quality (0-5)
            <input
              type="number"
              min={0}
              max={5}
              value={form.quality}
              onChange={(event) => setForm((prev) => ({ ...prev, quality: Number(event.target.value) }))}
              className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
            />
          </label>
          <label className="grid gap-1 text-xs text-slate-400">
            Time block
            <input
              value={form.time_block}
              onChange={(event) => setForm((prev) => ({ ...prev, time_block: event.target.value }))}
              className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
            />
          </label>

          <div className="flex flex-wrap gap-2">
            <button
              type="submit"
              disabled={!canSubmit}
              className="rounded-xl border border-success/45 bg-success/20 px-4 py-2 text-sm text-success disabled:opacity-60"
            >
              {saving ? "Saving..." : "Finalize Session"}
            </button>
            <button
              type="button"
              disabled={!canSubmit}
              onClick={() => finalizeSession("focus_timer")}
              className="rounded-xl border border-primary/45 bg-primary/20 px-4 py-2 text-sm text-primary disabled:opacity-60"
            >
              Save as Focus Timer
            </button>
          </div>
        </form>

        {error ? <p className="mt-3 rounded-xl border border-danger/45 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p> : null}
        {lastResult ? (
          <div className="mt-3 rounded-xl border border-white/10 bg-white/5 p-3 text-sm">
            <p className="font-medium text-slate-100">{lastResult.message}</p>
            <p className="mt-1 text-xs text-slate-400">
              {lastResult.study_minutes} min · focus {lastResult.focus_score} · productivity {lastResult.productivity_index}
            </p>
          </div>
        ) : null}
      </SectionCard>

      <ToastStack items={toasts} />
    </div>
  );
}
