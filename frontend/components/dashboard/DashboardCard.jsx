export default function DashboardCard({ label, value, hint, color = "primary" }) {
  const accentClass =
    color === "success"
      ? "from-success/25 to-success/5 border-success/35"
      : color === "warning"
        ? "from-warning/25 to-warning/5 border-warning/35"
        : color === "danger"
          ? "from-danger/25 to-danger/5 border-danger/35"
          : "from-primary/25 to-secondary/5 border-primary/35";

  return (
    <article className={`rounded-2xl border bg-gradient-to-br p-4 lg:p-5 ${accentClass}`}>
      <p className="text-xs uppercase tracking-[0.2em] text-slate-300">{label}</p>
      <p className="mt-2 text-2xl font-semibold lg:text-3xl">{value}</p>
      {hint ? <p className="mt-2 text-xs text-slate-300">{hint}</p> : null}
    </article>
  );
}
