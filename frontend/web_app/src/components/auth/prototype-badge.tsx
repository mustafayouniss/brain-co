import { cn } from "@/lib/utils";

/**
 * Visible MOCK label. Task requirement: "Anything not backed by a real
 * endpoint must be visibly labeled MOCK in the UI and in code." Every screen
 * of the post-selection journey (auth, onboarding, workspace) renders this
 * badge because none of them is backed by a real backend yet
 * (see docs/FLOW_AUDIT.md).
 */
export function PrototypeBadge({
  className,
  label = "Prototype · MOCK",
}: {
  className?: string;
  label?: string;
}) {
  return (
    <span
      className={cn("tag", className)}
      title="This flow runs against a simulated backend. No real data is stored."
    >
      {label}
    </span>
  );
}
