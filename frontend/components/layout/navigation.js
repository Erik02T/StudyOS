import {
  BarChart3,
  CalendarCheck2,
  Gauge,
  Goal,
  Library,
  RefreshCcw,
  Settings,
  Timer,
} from "lucide-react";

export const appNavigation = [
  { href: "/dashboard", label: "Dashboard", icon: Gauge },
  { href: "/planner", label: "Planner", icon: CalendarCheck2 },
  { href: "/library", label: "Library", icon: Library },
  { href: "/study-session", label: "Study Session", icon: Timer },
  { href: "/review", label: "Review", icon: RefreshCcw },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/goals", label: "Goals", icon: Goal },
  { href: "/settings", label: "Settings", icon: Settings },
];

export const mobileNavigation = [
  { href: "/dashboard", label: "Home", icon: Gauge },
  { href: "/study-session", label: "Study", icon: Timer },
  { href: "/review", label: "Review", icon: RefreshCcw },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/settings", label: "Profile", icon: Settings },
];
