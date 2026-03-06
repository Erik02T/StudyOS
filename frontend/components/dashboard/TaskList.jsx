export default function TaskList({ items, actionLabel = "Complete", onAction, disabled }) {
  if (!items?.length) {
    return <p className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-slate-400">No tasks yet.</p>;
  }

  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li
          key={item.task_id ?? item.id}
          className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/5 p-3"
        >
          <div>
            <p className="font-medium text-slate-100">{item.title}</p>
            <p className="text-xs text-slate-400">
              {item.subject || item.category || "General"} · {item.estimated_time || 0} min
            </p>
          </div>
          {onAction ? (
            <button
              type="button"
              disabled={disabled}
              onClick={() => onAction(item)}
              className="rounded-xl border border-primary/50 bg-primary/20 px-3 py-1.5 text-xs text-primary disabled:cursor-not-allowed disabled:opacity-60"
            >
              {actionLabel}
            </button>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
