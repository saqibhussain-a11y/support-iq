"use client";

import { ShieldAlert, Sparkles } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ComponentType } from "react";

import { cn } from "@/lib/utils";

const NAV_LINKS: { href: string; label: string; icon: ComponentType<{ className?: string }> }[] = [
  { href: "/", label: "Ask", icon: Sparkles },
  { href: "/queue", label: "Review queue", icon: ShieldAlert },
];

function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2">
      <span className="flex size-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
        <Sparkles className="size-4" />
      </span>
      <span className="text-sm font-semibold tracking-tight">SupportIQ</span>
    </Link>
  );
}

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <>
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-border bg-muted px-3 py-5 md:flex">
        <div className="px-2">
          <Logo />
        </div>
        <nav className="mt-8 flex flex-col gap-1">
          {NAV_LINKS.map((link) => {
            const active = pathname === link.href;
            const Icon = link.icon;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition-colors",
                  active
                    ? "bg-primary/10 font-medium text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                <Icon className="size-4" />
                {link.label}
              </Link>
            );
          })}
        </nav>
        <p className="mt-auto px-2.5 text-xs text-muted-foreground">
          AI Customer Support Intelligence Platform
        </p>
      </aside>

      <header className="sticky top-0 z-10 flex h-14 items-center gap-4 border-b border-border/60 bg-background/80 px-4 backdrop-blur-sm md:hidden">
        <Logo />
        <nav className="ml-auto flex items-center gap-1 text-sm">
          {NAV_LINKS.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "rounded-md px-2.5 py-1.5 transition-colors",
                  active ? "bg-primary/10 font-medium text-primary" : "text-muted-foreground hover:text-foreground",
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </header>
    </>
  );
}
