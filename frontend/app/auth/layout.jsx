import Link from "next/link";

export default function AuthLayout({ children }) {
  return (
    <main className="page-fade min-h-screen px-4 py-8 lg:px-10">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between">
        <Link href="/" className="text-xs uppercase tracking-[0.25em] text-accent">
          StudyOS
        </Link>
        <p className="text-xs text-slate-400">The Operating System for Learning</p>
      </header>

      <section className="mx-auto mt-10 grid w-full max-w-6xl gap-6 lg:grid-cols-[1fr_1fr]">
        <article className="rounded-3xl border border-primary/30 bg-gradient-to-br from-card-soft/95 to-card/95 p-6 lg:p-8">
          <p className="text-xs uppercase tracking-[0.2em] text-secondary">Adaptive Learning Engine</p>
          <h2 className="mt-3 text-4xl font-semibold leading-tight">
            Build smarter study cycles, not static to-do lists.
          </h2>
          <ul className="mt-4 grid gap-2 text-sm text-slate-300">
            <li>Automatic daily plan generation by availability.</li>
            <li>Spaced repetition integrated with performance logs.</li>
            <li>Organization workspaces and role-based collaboration.</li>
            <li>Dashboard with trend, heatmap and evolution score.</li>
          </ul>
        </article>
        <div>{children}</div>
      </section>
    </main>
  );
}
