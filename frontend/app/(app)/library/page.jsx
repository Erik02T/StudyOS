"use client";

import { useEffect, useMemo, useState } from "react";
import SectionCard from "../../../components/ui/SectionCard";
import ToastStack from "../../../components/ui/ToastStack";
import { useStudyOS } from "../../../components/providers/StudyOSProvider";
import { useNotify } from "../../../lib/use-notify";

export default function LibraryPage() {
  const { activeOrgId, apiRequest } = useStudyOS();
  const [subjects, setSubjects] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [subjectForm, setSubjectForm] = useState({
    name: "",
    importance_level: 3,
    difficulty: 3,
    category: "general",
  });
  const [taskForm, setTaskForm] = useState({
    title: "",
    subject_id: "",
    estimated_time: 30,
    mastery_level: 0,
    status: "pending",
  });
  const { items: toasts, push } = useNotify();

  const subjectsById = useMemo(() => {
    const map = new Map();
    subjects.forEach((subject) => map.set(subject.id, subject));
    return map;
  }, [subjects]);

  async function loadLibrary() {
    if (!activeOrgId) return;
    setLoading(true);
    try {
      setError("");
      const [subjectRows, taskRows] = await Promise.all([
        apiRequest({ path: "/subjects/" }),
        apiRequest({ path: "/tasks/" }),
      ]);
      setSubjects(subjectRows);
      setTasks(taskRows);
      if (!taskForm.subject_id && subjectRows.length) {
        setTaskForm((prev) => ({ ...prev, subject_id: subjectRows[0].id }));
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!activeOrgId) return;
    loadLibrary();
  }, [activeOrgId]);

  async function createSubject(event) {
    event.preventDefault();
    if (!activeOrgId) return;
    try {
      setError("");
      await apiRequest({
        method: "POST",
        path: "/subjects/",
        body: {
          ...subjectForm,
          importance_level: Number(subjectForm.importance_level),
          difficulty: Number(subjectForm.difficulty),
        },
      });
      setSubjectForm({ name: "", importance_level: 3, difficulty: 3, category: "general" });
      push("ok", "Subject created.");
      await loadLibrary();
    } catch (requestError) {
      setError(requestError.message);
      push("error", requestError.message);
    }
  }

  async function createTask(event) {
    event.preventDefault();
    if (!activeOrgId) return;
    try {
      setError("");
      await apiRequest({
        method: "POST",
        path: "/tasks/",
        body: {
          ...taskForm,
          subject_id: Number(taskForm.subject_id),
          estimated_time: Number(taskForm.estimated_time),
          mastery_level: Number(taskForm.mastery_level),
        },
      });
      setTaskForm((prev) => ({ ...prev, title: "", estimated_time: 30, mastery_level: 0, status: "pending" }));
      push("ok", "Task created.");
      await loadLibrary();
    } catch (requestError) {
      setError(requestError.message);
      push("error", requestError.message);
    }
  }

  async function toggleTaskStatus(task) {
    if (!activeOrgId) return;
    const nextStatus = task.status === "done" ? "pending" : "done";
    try {
      setError("");
      await apiRequest({
        method: "PUT",
        path: `/tasks/${task.id}`,
        body: { status: nextStatus },
      });
      push("ok", `Task "${task.title}" marked as ${nextStatus}.`);
      await loadLibrary();
    } catch (requestError) {
      setError(requestError.message);
      push("error", requestError.message);
    }
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
      <div className="grid gap-4">
        <SectionCard title="Add Subject" description="Create folders for your learning domains.">
          <form onSubmit={createSubject} className="grid gap-3">
            <label className="grid gap-1 text-xs text-slate-400">
              Name
              <input
                value={subjectForm.name}
                onChange={(event) => setSubjectForm((prev) => ({ ...prev, name: event.target.value }))}
                placeholder="Programming"
                className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
                required
              />
            </label>
            <div className="grid gap-3 sm:grid-cols-3">
              <label className="grid gap-1 text-xs text-slate-400">
                Importance
                <input
                  type="number"
                  min={1}
                  max={5}
                  value={subjectForm.importance_level}
                  onChange={(event) =>
                    setSubjectForm((prev) => ({ ...prev, importance_level: Number(event.target.value) }))
                  }
                  className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
                />
              </label>
              <label className="grid gap-1 text-xs text-slate-400">
                Difficulty
                <input
                  type="number"
                  min={1}
                  max={5}
                  value={subjectForm.difficulty}
                  onChange={(event) => setSubjectForm((prev) => ({ ...prev, difficulty: Number(event.target.value) }))}
                  className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
                />
              </label>
              <label className="grid gap-1 text-xs text-slate-400">
                Category
                <input
                  value={subjectForm.category}
                  onChange={(event) => setSubjectForm((prev) => ({ ...prev, category: event.target.value }))}
                  className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
                />
              </label>
            </div>
            <button type="submit" className="rounded-xl border border-primary/45 bg-primary/20 px-4 py-2 text-sm text-primary">
              Create subject
            </button>
          </form>
        </SectionCard>

        <SectionCard title="Add Task" description="Register learning units inside a subject.">
          <form onSubmit={createTask} className="grid gap-3">
            <label className="grid gap-1 text-xs text-slate-400">
              Title
              <input
                value={taskForm.title}
                onChange={(event) => setTaskForm((prev) => ({ ...prev, title: event.target.value }))}
                placeholder="FastAPI auth hardening"
                className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
                required
              />
            </label>
            <label className="grid gap-1 text-xs text-slate-400">
              Subject
              <select
                value={taskForm.subject_id}
                onChange={(event) => setTaskForm((prev) => ({ ...prev, subject_id: event.target.value }))}
                className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
                required
              >
                <option value="">Select subject</option>
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.name}
                  </option>
                ))}
              </select>
            </label>
            <div className="grid gap-3 sm:grid-cols-3">
              <label className="grid gap-1 text-xs text-slate-400">
                Minutes
                <input
                  type="number"
                  min={5}
                  max={240}
                  value={taskForm.estimated_time}
                  onChange={(event) => setTaskForm((prev) => ({ ...prev, estimated_time: Number(event.target.value) }))}
                  className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
                />
              </label>
              <label className="grid gap-1 text-xs text-slate-400">
                Mastery
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={taskForm.mastery_level}
                  onChange={(event) => setTaskForm((prev) => ({ ...prev, mastery_level: Number(event.target.value) }))}
                  className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
                />
              </label>
              <label className="grid gap-1 text-xs text-slate-400">
                Status
                <select
                  value={taskForm.status}
                  onChange={(event) => setTaskForm((prev) => ({ ...prev, status: event.target.value }))}
                  className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
                >
                  <option value="pending">pending</option>
                  <option value="in_progress">in_progress</option>
                  <option value="done">done</option>
                </select>
              </label>
            </div>
            <button type="submit" className="rounded-xl border border-primary/45 bg-primary/20 px-4 py-2 text-sm text-primary">
              Create task
            </button>
          </form>
        </SectionCard>
      </div>

      <SectionCard
        title="Knowledge Library"
        description="Subjects, tasks and mastery map."
        actions={
          <button
            type="button"
            onClick={loadLibrary}
            disabled={loading}
            className="rounded-lg border border-white/15 bg-white/5 px-3 py-1.5 text-xs"
          >
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        }
      >
        {error ? <p className="mb-3 rounded-xl border border-danger/45 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p> : null}
        <div className="grid gap-3">
          <div>
            <p className="mb-2 text-xs uppercase tracking-[0.2em] text-slate-400">Subjects</p>
            {!subjects.length ? (
              <p className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-slate-400">No subjects yet.</p>
            ) : (
              <ul className="space-y-2">
                {subjects.map((subject) => (
                  <li key={subject.id} className="rounded-xl border border-white/10 bg-white/5 p-3">
                    <p className="font-medium">{subject.name}</p>
                    <p className="text-xs text-slate-400">
                      Importance {subject.importance_level} · Difficulty {subject.difficulty} · {subject.category}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div>
            <p className="mb-2 text-xs uppercase tracking-[0.2em] text-slate-400">Tasks</p>
            {!tasks.length ? (
              <p className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-slate-400">No tasks yet.</p>
            ) : (
              <ul className="space-y-2">
                {tasks.map((task) => (
                  <li key={task.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/5 p-3">
                    <div>
                      <p className="font-medium">{task.title}</p>
                      <p className="text-xs text-slate-400">
                        {subjectsById.get(task.subject_id)?.name || "Unknown subject"} · {task.estimated_time} min · mastery{" "}
                        {task.mastery_level}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => toggleTaskStatus(task)}
                      className={`rounded-lg border px-3 py-1.5 text-xs ${
                        task.status === "done"
                          ? "border-warning/50 bg-warning/15 text-warning"
                          : "border-success/45 bg-success/20 text-success"
                      }`}
                    >
                      {task.status === "done" ? "Mark pending" : "Mark done"}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </SectionCard>

      <ToastStack items={toasts} />
    </div>
  );
}
