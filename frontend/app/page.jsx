import Link from "next/link";
import { ArrowRight, BarChart3, Brain, Clock3, Sparkles } from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "Adaptive Planner",
    description: "AI-assisted scheduling based on available time, performance and Pareto priority.",
  },
  {
    icon: BarChart3,
    title: "Deep Analytics",
    description: "Track weak topics, trend and consistency with actionable insights.",
  },
  {
    icon: Clock3,
    title: "Spaced Repetition",
    description: "Anki-style review cycles that adapt intervals from your answer quality.",
  },
  {
    icon: Sparkles,
    title: "Focus Sessions",
    description: "Pomodoro timer with session finalization directly connected to analytics.",
  },
];

const pricing = [
  {
    name: "Free",
    price: "$0",
    detail: "Basic planner + manual tracking",
    cta: "Start Free",
  },
  {
    name: "Pro",
    price: "$10",
    detail: "AI planner, analytics and spaced repetition",
    cta: "Go Pro",
    highlighted: true,
  },
  {
    name: "Premium",
    price: "$20",
    detail: "Full StudyOS + AI tutor + advanced analytics",
    cta: "Get Premium",
  },
];

export default function LandingPage() {
  return (
    <main className="page-fade min-h-screen px-4 py-8 lg:px-10">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.25em] text-accent">StudyOS</p>
          <h1 className="mt-1 text-lg font-semibold">The Operating System for Learning</h1>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/auth/login" className="rounded-xl border border-white/15 bg-white/5 px-4 py-2 text-sm">
            Login
          </Link>
          <Link href="/auth/register" className="rounded-xl border border-primary/45 bg-primary/20 px-4 py-2 text-sm text-primary">
            Get Started
          </Link>
        </div>
      </header>

      <section className="mx-auto mt-10 grid w-full max-w-6xl gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <article className="rounded-3xl border border-primary/30 bg-gradient-to-br from-card to-card-soft p-7 lg:p-9">
          <p className="text-xs uppercase tracking-[0.25em] text-secondary">Learning Engine</p>
          <h2 className="mt-3 text-4xl font-semibold leading-tight lg:text-5xl">
            Plan, track and optimize your studies with AI.
          </h2>
          <p className="mt-4 max-w-xl text-slate-300">
            Build daily plans, prioritize what matters with Pareto, run spaced repetition and measure real evolution.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/auth/register" className="inline-flex items-center gap-2 rounded-xl border border-primary/50 bg-primary px-4 py-2 text-sm font-medium text-white">
              Get Started
              <ArrowRight size={15} />
            </Link>
            <Link href="/dashboard" className="rounded-xl border border-white/20 bg-white/5 px-4 py-2 text-sm">
              View Demo
            </Link>
          </div>
        </article>

        <article className="glass rounded-3xl p-5">
          <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Dashboard Preview</p>
          <div className="mt-4 grid gap-3">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-sm text-slate-300">Study Progress Today</p>
              <p className="mt-2 text-3xl font-semibold text-success">70%</p>
            </div>
            <div className="grid grid-cols-5 gap-2">
              {[2, 1, 3, 2, 4].map((hours, idx) => (
                <div key={idx} className="rounded-xl border border-white/10 bg-white/5 p-2 text-center">
                  <p className="text-xs text-slate-400">{["Mon", "Tue", "Wed", "Thu", "Fri"][idx]}</p>
                  <p className="mt-1 text-lg font-semibold text-secondary">{hours}h</p>
                </div>
              ))}
            </div>
            <div className="rounded-2xl border border-success/35 bg-success/10 p-4">
              <p className="text-sm text-slate-300">▶ Start Study Session</p>
            </div>
          </div>
        </article>
      </section>

      <section className="mx-auto mt-10 grid w-full max-w-6xl gap-4 md:grid-cols-2 xl:grid-cols-4">
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <article key={feature.title} className="glass rounded-2xl p-4">
              <div className="inline-flex rounded-xl border border-primary/40 bg-primary/20 p-2 text-primary">
                <Icon size={16} />
              </div>
              <h3 className="mt-3 text-lg font-semibold">{feature.title}</h3>
              <p className="mt-1 text-sm text-slate-400">{feature.description}</p>
            </article>
          );
        })}
      </section>

      <section className="mx-auto mt-10 w-full max-w-6xl">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Pricing</p>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {pricing.map((plan) => (
            <article
              key={plan.name}
              className={`rounded-2xl border p-5 ${
                plan.highlighted
                  ? "border-primary/60 bg-gradient-to-b from-primary/20 to-card"
                  : "border-white/10 bg-card/75"
              }`}
            >
              <p className="text-sm text-slate-300">{plan.name}</p>
              <p className="mt-2 text-4xl font-semibold">{plan.price}</p>
              <p className="mt-2 text-sm text-slate-400">{plan.detail}</p>
              <button className="mt-5 w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm">
                {plan.cta}
              </button>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
