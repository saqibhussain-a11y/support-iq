import { AlertTriangle, CheckCircle2, ShieldAlert } from "lucide-react";
import type { ComponentType } from "react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { EscalationLevel, TicketCategory, TicketPriority } from "@/lib/api";

const CATEGORY_STYLES: Record<TicketCategory, string> = {
  billing: "bg-blue-50 text-blue-700 ring-blue-600/20 dark:bg-blue-500/10 dark:text-blue-400 dark:ring-blue-400/20",
  shipping:
    "bg-purple-50 text-purple-700 ring-purple-600/20 dark:bg-purple-500/10 dark:text-purple-400 dark:ring-purple-400/20",
  product:
    "bg-indigo-50 text-indigo-700 ring-indigo-600/20 dark:bg-indigo-500/10 dark:text-indigo-400 dark:ring-indigo-400/20",
  account: "bg-cyan-50 text-cyan-700 ring-cyan-600/20 dark:bg-cyan-500/10 dark:text-cyan-400 dark:ring-cyan-400/20",
  other: "bg-gray-100 text-gray-700 ring-gray-500/20 dark:bg-gray-500/10 dark:text-gray-400 dark:ring-gray-400/20",
};

export function CategoryBadge({ category }: { category: TicketCategory }) {
  return (
    <Badge className={cn("rounded-md capitalize ring-1 ring-inset", CATEGORY_STYLES[category])}>
      {category}
    </Badge>
  );
}

const PRIORITY_STYLES: Record<TicketPriority, string> = {
  low: "bg-slate-100 text-slate-700 ring-slate-500/20 dark:bg-slate-500/10 dark:text-slate-400 dark:ring-slate-400/20",
  medium:
    "bg-amber-50 text-amber-700 ring-amber-600/20 dark:bg-amber-500/10 dark:text-amber-400 dark:ring-amber-400/20",
  high: "bg-red-50 text-red-700 ring-red-600/20 dark:bg-red-500/10 dark:text-red-400 dark:ring-red-400/20",
};

export function PriorityBadge({ priority }: { priority: TicketPriority }) {
  return (
    <Badge className={cn("rounded-md capitalize ring-1 ring-inset", PRIORITY_STYLES[priority])}>
      {priority} priority
    </Badge>
  );
}

export const ESCALATION_META: Record<
  EscalationLevel,
  {
    label: string;
    icon: ComponentType<{ className?: string }>;
    bannerClassName: string;
    calloutClassName: string;
  }
> = {
  none: {
    label: "Resolved automatically",
    icon: CheckCircle2,
    bannerClassName: "bg-emerald-50 text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-400",
    calloutClassName:
      "bg-emerald-50 text-emerald-800 ring-emerald-600/20 dark:bg-emerald-500/10 dark:text-emerald-400 dark:ring-emerald-400/20",
  },
  review: {
    label: "Escalated for review",
    icon: AlertTriangle,
    bannerClassName: "bg-amber-50 text-amber-800 dark:bg-amber-500/10 dark:text-amber-400",
    calloutClassName:
      "bg-amber-50 text-amber-800 ring-amber-600/20 dark:bg-amber-500/10 dark:text-amber-400 dark:ring-amber-400/20",
  },
  immediate: {
    label: "Escalated immediately",
    icon: ShieldAlert,
    bannerClassName: "bg-red-50 text-red-800 dark:bg-red-500/10 dark:text-red-400",
    calloutClassName:
      "bg-red-50 text-red-800 ring-red-600/20 dark:bg-red-500/10 dark:text-red-400 dark:ring-red-400/20",
  },
};
