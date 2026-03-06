"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useStudyOS } from "../providers/StudyOSProvider";

export default function AuthGate({ children }) {
  const { token, hydrated } = useStudyOS();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!hydrated) return;
    if (!token) {
      const next = encodeURIComponent(pathname || "/dashboard");
      router.replace(`/auth/login?next=${next}`);
    }
  }, [token, hydrated, pathname, router]);

  if (!hydrated) {
    return <div className="flex min-h-screen items-center justify-center text-slate-300">Loading workspace...</div>;
  }

  if (!token) {
    return <div className="flex min-h-screen items-center justify-center text-slate-400">Redirecting to login...</div>;
  }

  return children;
}
