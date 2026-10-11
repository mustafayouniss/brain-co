"use client";

import * as React from "react";
import { shapeUrls, type Shape } from "@/content/app";

let framePromise: Promise<Record<Shape, Document>> | undefined;

/** Load + parse the five morph frames once (shared across instances). */
function loadFrames(): Promise<Record<Shape, Document>> {
  if (!framePromise) {
    framePromise = Promise.all(
      (Object.entries(shapeUrls) as [Shape, string][]).map(async ([name, url]) => {
        const source = await fetch(url).then((response) => response.text());
        return [name, new DOMParser().parseFromString(source, "image/svg+xml")] as const;
      }),
    ).then(
      (entries) => Object.fromEntries(entries) as Record<Shape, Document>,
    );
  }
  return framePromise;
}

/**
 * Particle morph engine — ported 1:1 from the source app (src/App.tsx).
 * Lerps every `dot_*` circle's cx/cy/r/fill-opacity (and final fill) between
 * two SVG frames with an ease-in-out curve; `drifting` idles in place.
 */
export function ParticleMorph({
  from,
  target,
  duration,
  drifting = false,
  className = "",
}: {
  from: Shape;
  target: Shape;
  duration: number;
  drifting?: boolean;
  className?: string;
}) {
  const host = React.useRef<HTMLDivElement>(null);
  const animation = React.useRef(0);
  const initialized = React.useRef(false);

  React.useEffect(() => {
    let disposed = false;
    const token = ++animation.current;

    loadFrames().then((frames) => {
      if (disposed || !host.current) return;
      if (!initialized.current) {
        host.current.innerHTML = frames[from].documentElement.outerHTML;
        initialized.current = true;
      }

      const dots = Array.from(
        host.current.querySelectorAll<SVGCircleElement>('[id^="dot_"]'),
      );
      const destination = frames[target];
      const starts = dots.map((dot) => ({
        cx: Number(dot.getAttribute("cx")),
        cy: Number(dot.getAttribute("cy")),
        r: Number(dot.getAttribute("r")),
        opacity: Number(dot.getAttribute("fill-opacity") ?? 1),
        fill: dot.getAttribute("fill") ?? "#FFFFFF",
      }));
      const ends = dots.map((dot) => {
        const partner = destination.getElementById(dot.id);
        return {
          cx: Number(partner?.getAttribute("cx")),
          cy: Number(partner?.getAttribute("cy")),
          r: Number(partner?.getAttribute("r")),
          opacity: Number(partner?.getAttribute("fill-opacity") ?? 1),
          fill: partner?.getAttribute("fill") ?? "#FFFFFF",
        };
      });
      const started = performance.now();

      function draw(now: number) {
        if (disposed || animation.current !== token) return;
        const driftOnly = drifting && from === target;
        const progress = driftOnly
          ? 0
          : duration === 0
            ? 1
            : Math.min(1, (now - started) / duration);
        const eased =
          progress < 0.5
            ? 2 * progress * progress
            : 1 - Math.pow(-2 * progress + 2, 2) / 2;

        dots.forEach((dot, index) => {
          const start = starts[index];
          const end = ends[index];
          const driftX = driftOnly ? Math.sin(index * 1.71 + now / 620) * 2.2 : 0;
          const driftY = driftOnly ? Math.cos(index * 1.13 + now / 740) * 2.2 : 0;
          dot.setAttribute(
            "cx",
            String(start.cx + (end.cx - start.cx) * eased + driftX),
          );
          dot.setAttribute(
            "cy",
            String(start.cy + (end.cy - start.cy) * eased + driftY),
          );
          dot.setAttribute("r", String(start.r + (end.r - start.r) * eased));
          dot.setAttribute(
            "fill-opacity",
            String(start.opacity + (end.opacity - start.opacity) * eased),
          );
          if (progress === 1) dot.setAttribute("fill", end.fill);
        });

        if (progress < 1 || driftOnly) requestAnimationFrame(draw);
      }

      requestAnimationFrame(draw);
    });

    return () => {
      disposed = true;
    };
  }, [duration, drifting, from, target]);

  return (
    <div
      className={`particle-morph ${className}`}
      ref={host}
      role="img"
      aria-label={`${target} dot shape`}
    />
  );
}

/** Static rendering of a morph frame (no animation). */
export function StaticShape({
  shape,
  className = "",
}: {
  shape: Shape;
  className?: string;
}) {
  return (
    <img
      className={`static-shape ${className}`}
      src={shapeUrls[shape]}
      alt={`${shape} dot shape`}
      decoding="async"
    />
  );
}
