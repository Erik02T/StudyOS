"use client";

import { useEffect, useState } from "react";
import Flashcard from "../../../components/study/Flashcard";
import SectionCard from "../../../components/ui/SectionCard";
import ToastStack from "../../../components/ui/ToastStack";
import { useStudyOS } from "../../../components/providers/StudyOSProvider";
import { REVIEW_QUALITY_OPTIONS } from "../../../lib/constants";
import { useNotify } from "../../../lib/use-notify";

export default function ReviewPage() {
  const { activeOrgId, apiRequest } = useStudyOS();
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [busyTaskId, setBusyTaskId] = useState(null);
  const { items: toasts, push } = useNotify();

  async function loadDueReviews() {
    if (!activeOrgId) return;
    setLoading(true);
    try {
      setError("");
      const data = await apiRequest({ path: "/reviews/due" });
      setReviews(data);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!activeOrgId) return;
    loadDueReviews();
  }, [activeOrgId]);

  async function answer(review, quality) {
    if (!activeOrgId) return;
    setBusyTaskId(review.task_id);
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
          study_minutes: review.estimated_time,
          time_block: "19:00-21:00",
        },
      });
      setReviews((prev) => prev.filter((item) => item.task_id !== review.task_id));
      push("ok", `Review completed: ${review.title}`);
    } catch (requestError) {
      setError(requestError.message);
      push("error", requestError.message);
    } finally {
      setBusyTaskId(null);
    }
  }

  return (
    <div className="grid gap-4">
      <SectionCard
        title="Spaced Repetition Queue"
        description="Answer quality drives next interval and mastery adaptation."
        actions={
          <button
            type="button"
            onClick={loadDueReviews}
            disabled={loading}
            className="rounded-lg border border-white/15 bg-white/5 px-3 py-1.5 text-xs"
          >
            {loading ? "Refreshing..." : "Refresh Queue"}
          </button>
        }
      >
        {error ? <p className="mb-3 rounded-xl border border-danger/45 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p> : null}
        {!reviews.length ? (
          <p className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-slate-400">
            No reviews due. Your repetition queue is clear.
          </p>
        ) : (
          <div className="grid gap-3 lg:grid-cols-2">
            {reviews.map((review) => (
              <Flashcard
                key={review.task_id}
                front={review.title}
                back={`${review.subject} · ${review.category}`}
                meta={`Estimated: ${review.estimated_time} min · Interval: ${review.interval} days`}
                actions={
                  <div className="flex flex-wrap gap-2">
                    {REVIEW_QUALITY_OPTIONS.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        disabled={busyTaskId === review.task_id}
                        onClick={() => answer(review, option.value)}
                        className="rounded-lg border border-primary/35 bg-primary/15 px-3 py-1.5 text-xs text-primary disabled:opacity-60"
                      >
                        {busyTaskId === review.task_id ? "Saving..." : option.label}
                      </button>
                    ))}
                  </div>
                }
              />
            ))}
          </div>
        )}
      </SectionCard>
      <ToastStack items={toasts} />
    </div>
  );
}
