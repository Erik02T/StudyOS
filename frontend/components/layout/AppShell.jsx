"use client";

import { Bell, LogOut } from "lucide-react";
import MobileTabs from "./MobileTabs";
import Sidebar from "./Sidebar";
import { useStudyOS } from "../providers/StudyOSProvider";

export default function AppShell({ title, subtitle, children }) {
  const { apiBase, setApiBase, logout } = useStudyOS();

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[18rem_1fr]">
      <Sidebar />
      <main className="page-fade flex min-h-screen flex-col pb-20 lg:pb-6">
        <header className="sticky top-0 z-30 border-b border-white/10 bg-background/85 px-4 py-3 backdrop-blur lg:px-8">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h1 className="text-xl font-semibold lg:text-2xl">{title}</h1>
              <p className="text-sm text-slate-400">{subtitle}</p>
            </div>
            <div className="flex items-center gap-2">
              <button className="rounded-xl border border-white/10 bg-card px-3 py-2 text-xs text-slate-200">
                <Bell size={14} />
              </button>
              <button
                onClick={logout}
                className="inline-flex items-center gap-2 rounded-xl border border-danger/40 bg-danger/15 px-3 py-2 text-xs text-danger"
              >
                <LogOut size={14} />
                Logout
              </button>
            </div>
          </div>
          <div className="mt-3 grid max-w-xl gap-2">
            <label className="text-xs uppercase tracking-[0.2em] text-slate-400">API Base</label>
            <input
              value={apiBase}
              onChange={(e) => setApiBase(e.target.value)}
              className="rounded-xl border border-white/10 bg-card px-3 py-2 text-sm text-slate-100"
            />
          </div>
        </header>
        <div className="flex-1 px-4 py-5 lg:px-8">{children}</div>
      </main>
      <MobileTabs />
    </div>
  );
}
