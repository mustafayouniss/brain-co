"use client";

import React from "react";
import Link from "next/link";
import { ArrowIcon } from "@/components/brand/icons";
import { buttonClasses } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface DepartmentSectionProps {
  id: string;
  tag: string;
  title: string;
  description: string;
  tags: string[];
  active?: boolean;
}

export function DepartmentSectionCard({
  id,
  tag,
  title,
  description,
  tags,
}: DepartmentSectionProps) {
  return (
    <section
      id={id}
      className="relative z-10 min-h-screen flex items-center justify-end px-6 sm:px-12 lg:px-24 pointer-events-none"
    >
      <div
        className={cn(
          "pointer-events-auto max-w-[480px] w-full p-8 sm:p-10 rounded-2xl",
          "bg-gradient-to-br from-[#1b1233]/75 via-[#0a0a10]/85 to-[#10252d]/55",
          "border border-[#A98CE6]/25 shadow-[0_20px_60px_rgba(0,0,0,0.65),inset_0_1px_0_rgba(255,255,255,0.08)]",
          "backdrop-blur-xl transition-all duration-700"
        )}
      >
        <div className="text-[11px] font-mono tracking-[0.25em] text-[#9ADCEB] uppercase mb-4 font-semibold">
          {tag}
        </div>
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-semibold tracking-[-0.025em] leading-[1.08] mb-5 text-transparent bg-clip-text bg-gradient-to-r from-[#F3EEFA] via-[#C4B5F0] to-[#E8D98A]">
          {title}
        </h2>
        <p className="text-[#a9a3bf] text-base sm:text-lg leading-[1.7] font-light mb-6">
          {description}
        </p>
        <div className="flex flex-wrap gap-2">
          {tags.map((t) => (
            <span
              key={t}
              className="text-xs px-3.5 py-1.5 rounded-full border border-[#C4B5F0]/25 bg-[#C4B5F0]/10 backdrop-blur-md text-[#D8D2EC] font-mono"
            >
              {t}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}

export function FinalUnifiedSection() {
  return (
    <section
      id="unified"
      className="relative z-10 min-h-screen flex items-center justify-center text-center px-6 sm:px-12 pb-20 pointer-events-none"
    >
      <div className="pointer-events-auto max-w-3xl flex flex-col items-center">
        <div className="text-[12px] font-mono tracking-[0.28em] text-[#9ADCEB] uppercase mb-4 font-semibold">
          Autonomous Hive Mind
        </div>
        <h2 className="text-4xl sm:text-6xl md:text-7xl font-semibold tracking-[-0.03em] leading-[1.02] mb-6 text-transparent bg-clip-text bg-gradient-to-r from-[#F3EEFA] via-[#C4B5F0] to-[#E8D98A]">
          All intelligence. <br />
          One living brain.
        </h2>
        <p className="max-w-xl text-[#a9a3bf] text-lg sm:text-xl leading-[1.7] font-light mb-10">
          Knowledge never walks out the door. Legal, HR, Sales, Finance, and Operations synchronize inside one continuous neural foundation.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/onboarding"
            className={cn(
              buttonClasses("primary", "lg"),
              "px-10 py-4 text-base font-semibold rounded-full bg-gradient-to-r from-[#A98CE6] via-[#C4B5F0] to-[#EAD9A0] text-[#0b0816] shadow-[0_0_35px_rgba(169,140,230,0.45)] border-0 transition-transform duration-300 hover:scale-105"
            )}
          >
            <span>Activate Organization Brain</span>
            <ArrowIcon className="ml-2" />
          </Link>
          <Link
            href="/contact"
            className={cn(
              buttonClasses("secondary", "lg"),
              "px-8 py-4 text-base rounded-full bg-white/[0.04] hover:bg-white/[0.08] text-[#F3EEFA] border border-white/15 backdrop-blur-md"
            )}
          >
            <span>Schedule Briefing</span>
          </Link>
        </div>
      </div>
    </section>
  );
}
