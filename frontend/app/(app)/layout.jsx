"use client";

import { useMemo } from "react";
import { usePathname } from "next/navigation";
import AuthGate from "../../components/auth/AuthGate";
import AppShell from "../../components/layout/AppShell";
import { pageMeta } from "../../components/layout/page-meta";

export default function ProtectedLayout({ children }) {
  const pathname = usePathname();
  const meta = useMemo(() => pageMeta[pathname] || pageMeta["/dashboard"], [pathname]);

  return (
    <AuthGate>
      <AppShell title={meta.title} subtitle={meta.subtitle}>
        {children}
      </AppShell>
    </AuthGate>
  );
}
