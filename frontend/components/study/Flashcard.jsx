"use client";

import { Rotate3D } from "lucide-react";
import { useState } from "react";

export default function Flashcard({ front, back, meta, actions }) {
  const [flipped, setFlipped] = useState(false);

  return (
    <article className="glass rounded-2xl p-4 lg:p-5">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">{flipped ? "Back" : "Front"}</p>
        <button
          type="button"
          onClick={() => setFlipped((value) => !value)}
          className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-3 py-1.5 text-xs text-slate-200"
        >
          <Rotate3D size={14} />
          Flip
        </button>
      </div>

      <div className="min-h-28 rounded-xl border border-white/10 bg-background/55 p-4">
        <p className="text-lg font-semibold">{flipped ? back : front}</p>
        {meta ? <p className="mt-2 text-xs text-slate-400">{meta}</p> : null}
      </div>

      {actions ? <div className="mt-4">{actions}</div> : null}
    </article>
  );
}
