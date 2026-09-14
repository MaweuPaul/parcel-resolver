"use client";

import Link from "next/link";
import {
  ArrowLeftRight,
  BadgeCheck,
  Boxes,
  Ruler,
  ScanSearch,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import dashboard from "@/config/dashboard.json";
import { useAnalysesCompleted } from "@/lib/analytics";

const icons: Record<string, LucideIcon> = {
  "scan-search": ScanSearch,
  "badge-check": BadgeCheck,
  ruler: Ruler,
  boxes: Boxes,
  "arrow-left-right": ArrowLeftRight,
};

export default function Home() {
  const analysesCompleted = useAnalysesCompleted();

  const allTools = dashboard.toolGroups.flatMap((group) => group.tools);
  const availableCount = allTools.filter((tool) => tool.status === "available").length;
  const plannedCount = allTools.length - availableCount;

  const summaryCards = [
    { id: "available-tools", label: "Available tools", value: availableCount },
    { id: "planned-tools", label: "Planned tools", value: plannedCount },
    {
      id: "analyses",
      label: "Analyses completed",
      value: analysesCompleted,
    },
  ];

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-[#17211F]">
          {dashboard.overview.title}
        </h1>
        <p className="mt-1 text-sm text-[#17211F]/60">
          {dashboard.overview.description}
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {summaryCards.map((card) => (
          <div
            key={card.id}
            className="rounded-2xl border border-black/10 bg-white p-5 shadow-sm"
          >
            <p className="text-3xl font-semibold tracking-tight text-[#17211F]">
              {card.value}
            </p>
            <p className="mt-1 text-sm text-[#17211F]/60">{card.label}</p>
          </div>
        ))}
      </div>

      <p className="-mt-4 text-xs text-[#17211F]/40">
        &ldquo;Analyses completed&rdquo; counts successful tool runs in this
        browser only — it isn&apos;t tracked on the server, and clearing site
        data resets it to zero.
      </p>

      {dashboard.toolGroups.map((group) => (
        <section key={group.id} className="flex flex-col gap-3">
          <h2 className="text-xs font-semibold uppercase tracking-[0.16em] text-[#17211F]/50">
            {group.label}
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {group.tools.map((tool) => {
              const Icon = icons[tool.icon];
              const isAvailable = tool.status === "available";

              return (
                <Link
                  key={tool.id}
                  href={tool.href}
                  aria-disabled={!isAvailable}
                  onClick={(event) => {
                    if (!isAvailable) event.preventDefault();
                  }}
                  className={`flex flex-col gap-3 rounded-2xl border border-black/10 bg-white p-5 shadow-sm transition-colors ${
                    isAvailable
                      ? "hover:border-[#D3A62C]"
                      : "cursor-default opacity-60"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="grid size-10 place-items-center rounded-xl bg-[#0A332E] text-[#D3A62C]">
                      {Icon && <Icon aria-hidden="true" className="size-4" />}
                    </span>
                    {!isAvailable && (
                      <span className="rounded-full bg-black/5 px-2 py-0.5 text-[11px] font-semibold text-[#17211F]/60">
                        Soon
                      </span>
                    )}
                  </div>
                  <div>
                    <h3 className="font-semibold text-[#17211F]">{tool.name}</h3>
                    <p className="mt-1 text-sm text-[#17211F]/60">
                      {tool.description}
                    </p>
                  </div>
                </Link>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
