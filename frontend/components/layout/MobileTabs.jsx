"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { mobileNavigation } from "./navigation";

export default function MobileTabs() {
  const pathname = usePathname();

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 border-t border-white/10 bg-card/95 px-2 py-2 lg:hidden">
      <div className="mx-auto grid max-w-xl grid-cols-5 gap-1">
        {mobileNavigation.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center gap-1 rounded-xl px-2 py-2 text-[10px] transition ${
                active ? "bg-primary/25 text-white" : "text-slate-300 hover:bg-white/5"
              }`}
            >
              <Icon size={15} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
