import { LayoutDashboard, ShoppingBag, Key, Zap, Database, Star } from "lucide-react";
import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/ui/theme-toggle";

interface SidebarProps {
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
  const items = [
    { name: "Overview", icon: LayoutDashboard, href: "/" },
    { name: "Catalog", icon: ShoppingBag, href: "/catalog" },
    { name: "Merchandising", icon: Star, href: "/merchandising" },
    { name: "Ingest", icon: Database, href: "/ingest" },
    { name: "Go Live", icon: Key, href: "/go-live" },
  ];

  return (
    <div className={cn("pb-12 min-h-screen border-r border-border bg-white flex flex-col", className)}>
      <div className="space-y-4 py-4 flex-1">
        <div className="px-3 py-2">
          <div className="flex items-center gap-2 px-4 mb-8">
            <Zap className="h-6 w-6 text-zinc-900" fill="currentColor" />
            <h2 className="text-lg font-bold tracking-tight text-zinc-900">
              Mercury
            </h2>
          </div>
          <div className="space-y-1">
            {items.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) => cn(
                  "w-full flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-zinc-100 hover:text-zinc-900",
                  isActive ? "bg-zinc-100 text-zinc-900" : "text-zinc-500"
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.name}
              </NavLink>
            ))}
          </div>
        </div>
      </div>
      <div className="px-7 py-4 border-t border-border flex items-center justify-between">
        <p className="text-xs text-zinc-400 font-medium">Mercury v4.0.0</p>
        <ThemeToggle />
      </div>
    </div>
  );
}
