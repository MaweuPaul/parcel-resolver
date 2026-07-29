"use client";

import { useState } from "react";
import {
  ArrowLeftRight,
  BadgeCheck,
  Boxes,
  LayoutDashboard,
  Layers3,
  Menu,
  Ruler,
  ScanSearch,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import dashboard from "@/config/dashboard.json";
import { NavLink } from "./nav-link";

const icons: Record<string, LucideIcon> = {
  "layout-dashboard": LayoutDashboard,
  "scan-search": ScanSearch,
  "badge-check": BadgeCheck,
  ruler: Ruler,
  boxes: Boxes,
  "arrow-left-right": ArrowLeftRight,
};

export function Sidebar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <div className="flex min-h-16 items-center justify-between bg-[#0A332E] px-4 text-white lg:hidden">
        <Brand />
        <button
          type="button"
          onClick={() => setIsOpen((open) => !open)}
          aria-label={isOpen ? "Close navigation" : "Open navigation"}
          aria-expanded={isOpen}
          className="grid size-11 place-items-center rounded-xl border border-white/15 transition-colors hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#D3A62C]"
        >
          {isOpen ? <X aria-hidden="true" className="size-5" /> : <Menu aria-hidden="true" className="size-5" />}
        </button>
      </div>

      {isOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={() => setIsOpen(false)}
          className="fixed inset-0 z-30 bg-slate-950/55 lg:hidden"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-[17.5rem] flex-col bg-[#0A332E] text-white shadow-2xl transition-transform duration-200 lg:sticky lg:top-0 lg:z-10 lg:h-dvh lg:translate-x-0 lg:shadow-none ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex min-h-20 items-center border-b border-white/10 px-5">
          <Brand />
        </div>

        <nav
          aria-label="Main navigation"
          className="flex-1 overflow-y-auto px-4 py-5"
        >
          {dashboard.navigation.map((item) => {
            const Icon = icons[item.icon];

            return (
              <NavLink
                key={item.id}
                href={item.href}
                label={item.label}
                icon={Icon ? <Icon className="size-4" /> : undefined}
                onNavigate={() => setIsOpen(false)}
              />
            );
          })}

          {dashboard.toolGroups.map((group) => (
            <section key={group.id} className="mt-7">
              <h2 className="px-3 text-xs font-semibold uppercase tracking-[0.16em] text-white/45">
                {group.label}
              </h2>
              <div className="mt-2 space-y-1">
                {group.tools.map((tool) => {
                  const Icon = icons[tool.icon];

                  return (
                    <NavLink
                      key={tool.id}
                      href={tool.href}
                      label={tool.shortName}
                      icon={Icon ? <Icon className="size-4" /> : undefined}
                      badge={tool.status === "planned" ? "Soon" : undefined}
                      onNavigate={() => setIsOpen(false)}
                    />
                  );
                })}
              </div>
            </section>
          ))}
        </nav>

        <div className="border-t border-white/10 px-5 py-4">
          <p className="text-xs leading-5 text-white/45">
            Expandable tools for spatial analysis.
          </p>
        </div>
      </aside>
    </>
  );
}

function Brand() {
  return (
    <div className="flex items-center gap-3">
      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-[#D3A62C] text-[#17211F]">
        <Layers3 aria-hidden="true" className="size-5" />
      </span>
      <span>
        <span className="block font-semibold tracking-tight">
          {dashboard.product.name}
        </span>
        <span className="block text-xs text-white/50">
          {dashboard.product.description}
        </span>
      </span>
    </div>
  );
}
