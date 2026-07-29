"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

type NavLinkProps = {
  href: string;
  label: string;
  icon?: ReactNode;
  badge?: string;
  onNavigate?: () => void;
};

export function NavLink({
  href,
  label,
  icon,
  badge,
  onNavigate,
}: NavLinkProps) {
  const pathname = usePathname();
  const isActive =
    href === "/" ? pathname === href : pathname.startsWith(href);

  return (
    <Link
      href={href}
      onClick={onNavigate}
      aria-current={isActive ? "page" : undefined}
      className={`flex min-h-11 items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#D3A62C] ${
        isActive
          ? "bg-[#D3A62C] text-[#17211F]"
          : "text-white/75 hover:bg-white/10 hover:text-white"
      }`}
    >
      {icon && <span className="shrink-0" aria-hidden="true">{icon}</span>}
      <span className="min-w-0 flex-1 truncate">{label}</span>
      {badge && (
        <span
          className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${
            isActive
              ? "bg-[#17211F]/10 text-[#17211F]"
              : "bg-white/10 text-white/65"
          }`}
        >
          {badge}
        </span>
      )}
    </Link>
  );
}
