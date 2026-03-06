"use client";

import { useEffect, useMemo, useState } from "react";
import { Pause, Play, RotateCcw } from "lucide-react";

function formatTime(totalSeconds) {
  const safe = Math.max(0, totalSeconds);
  const mm = Math.floor(safe / 60)
    .toString()
    .padStart(2, "0");
  const ss = Math.floor(safe % 60)
    .toString()
    .padStart(2, "0");
  return `${mm}:${ss}`;
}

export default function StudyTimer({ initialMinutes = 25, onComplete }) {
  const [running, setRunning] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(initialMinutes * 60);

  useEffect(() => {
    setSecondsLeft(initialMinutes * 60);
  }, [initialMinutes]);

  useEffect(() => {
    if (!running) return undefined;
    const id = window.setInterval(() => {
      setSecondsLeft((current) => {
        if (current <= 1) {
          window.clearInterval(id);
          setRunning(false);
          if (onComplete) onComplete();
          return 0;
        }
        return current - 1;
      });
    }, 1000);
    return () => window.clearInterval(id);
  }, [running, onComplete]);

  const progress = useMemo(() => {
    const full = Math.max(1, initialMinutes * 60);
    return ((full - secondsLeft) / full) * 100;
  }, [secondsLeft, initialMinutes]);

  return (
    <div className="glass rounded-2xl p-5">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Focus Timer</p>
      <p className="mt-2 text-5xl font-semibold">{formatTime(secondsLeft)}</p>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full bg-gradient-to-r from-primary to-secondary" style={{ width: `${progress}%` }} />
      </div>
      <div className="mt-4 flex gap-2">
        <button
          type="button"
          onClick={() => setRunning((value) => !value)}
          className="inline-flex items-center gap-2 rounded-xl border border-primary/45 bg-primary/20 px-3 py-2 text-sm text-primary"
        >
          {running ? <Pause size={15} /> : <Play size={15} />}
          {running ? "Pause" : "Start"}
        </button>
        <button
          type="button"
          onClick={() => {
            setRunning(false);
            setSecondsLeft(initialMinutes * 60);
          }}
          className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm text-slate-200"
        >
          <RotateCcw size={15} />
          Reset
        </button>
      </div>
    </div>
  );
}
