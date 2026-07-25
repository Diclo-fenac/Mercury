import { Bell, Search, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function Topbar() {
  return (
    <header className="h-16 border-b border-border bg-white flex items-center justify-between px-6 sticky top-0 z-10">
      <div className="flex items-center flex-1">
        <div className="relative w-96">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-zinc-500" />
          <Input
            type="search"
            placeholder="Search commands or settings... (Cmd+K)"
            className="w-full bg-zinc-50 border-none pl-9 focus-visible:ring-1 focus-visible:ring-zinc-200 rounded-lg"
          />
        </div>
      </div>
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" className="text-zinc-500 hover:text-zinc-900">
          <Bell className="h-5 w-5" />
        </Button>
        <div className="h-8 w-8 rounded-full bg-zinc-200 border border-border flex items-center justify-center overflow-hidden">
          <User className="h-4 w-4 text-zinc-500" />
        </div>
      </div>
    </header>
  );
}
