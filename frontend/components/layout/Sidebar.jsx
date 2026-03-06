"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { appNavigation } from "./navigation";
import { useStudyOS } from "../providers/StudyOSProvider";

export default function Sidebar() {
  const pathname = usePathname();
  const { organizations, activeOrgId, setActiveOrgId, email } = useStudyOS();

  return (
    <aside className="hidden lg:flex lg:w-72 lg:flex-col lg:gap-5 lg:border-r lg:border-white/10 lg:bg-card/60 lg:p-5">
      <div className="rounded-2xl border border-primary/30 bg-gradient-to-br from-primary/20 to-secondary/10 p-5 shadow-glow">
        <p className="text-xs uppercase tracking-[0.25em] text-accent">StudyOS</p>
        <h2 className="mt-2 text-2xl font-semibold">Operating System for Learning</h2>
        <p className="mt-3 text-sm text-slate-300">Welcome back{email ? `, ${email}` : ""}.</p>
      </div>

      <div className="glass rounded-2xl p-4">
        <p className="mb-2 text-xs uppercase tracking-[0.2em] text-slate-400">Workspace</p>
        <select
          className="w-full rounded-xl border border-white/15 bg-background/70 p-2 text-sm"
          value={activeOrgId || ""}
          onChange={(event) => setActiveOrgId(Number(event.target.value) || null)}
        >
          {!organizations.length ? <option value="">No organizations</option> : null}
          {organizations.map((org) => (
            <option key={org.id} value={org.id}>
              {org.name} ({org.role})
            </option>
          ))}
        </select>
      </div>

      <nav className="glass flex-1 rounded-2xl p-3">
        <ul className="space-y-1">
          {appNavigation.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition ${
                    active
                      ? "bg-primary/25 text-white shadow-inner"
                      : "text-slate-300 hover:bg-white/5 hover:text-white"
                  }`}
                >
                  <Icon size={16} />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
