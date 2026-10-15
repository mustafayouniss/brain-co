import type { ReactNode } from "react";
import { homeCopy } from "@/content/app";
import { BrandMark } from "@/components/brand/icons";

const nodes: Array<[number, number, number]> = [
  [44, 97, 2.8],
  [60, 59, 3.5],
  [94, 35, 2.4],
  [130, 38, 3.2],
  [160, 66, 2.7],
  [174, 103, 3.8],
  [159, 137, 2.4],
  [128, 163, 3.2],
  [91, 160, 2.4],
  [56, 137, 3.6],
  [83, 85, 3],
  [119, 72, 2.5],
  [145, 103, 3.5],
  [119, 127, 2.7],
  [82, 121, 2.7],
  [104, 102, 5],
];

const connections: Array<[number, number]> = [
  [0, 1], [0, 9], [0, 10], [1, 2], [1, 10], [2, 3], [2, 11],
  [3, 4], [3, 11], [4, 5], [4, 12], [5, 6], [5, 12], [6, 7],
  [6, 13], [7, 8], [7, 13], [8, 9], [8, 14], [9, 14], [10, 11],
  [10, 14], [10, 15], [11, 12], [11, 15], [12, 13], [12, 15],
  [13, 14], [13, 15], [14, 15],
];

/** Hero visual: orbiting rings + pulsing node network around the brand core. */
export function BrainNetwork({ center, label }: { center?: ReactNode; label?: ReactNode } = {}) {
  return (
    <div className="brain-visual" role="img" aria-label={homeCopy.brainAria}>
      {center && <div className="brain-field">{center}</div>}
      <div className="brain-orbit brain-orbit-outer" />
      <div className="brain-orbit brain-orbit-inner" />
      <svg className="brain-network" viewBox="0 0 208 200">
        <g className="network-lines">
          {connections.map(([from, to]) => (
            <line
              key={`${from}-${to}`}
              x1={nodes[from][0]}
              x2={nodes[to][0]}
              y1={nodes[from][1]}
              y2={nodes[to][1]}
            />
          ))}
        </g>
        <g className="network-nodes">
          {nodes.map(([cx, cy, radius], index) => (
            <circle cx={cx} cy={cy} key={`${cx}-${cy}`} r={radius}>
              <animate
                attributeName="opacity"
                begin={`${index * 0.12}s`}
                dur="2.8s"
                repeatCount="indefinite"
                values="0.45;1;0.45"
              />
            </circle>
          ))}
        </g>
      </svg>
      {!center && (
        <div className="brain-core">
          <BrandMark />
        </div>
      )}
      {label ?? <span className="brain-label">{homeCopy.brainLabel}</span>}
    </div>
  );
}
