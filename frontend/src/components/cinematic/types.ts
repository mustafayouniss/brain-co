/**
 * Brain-Co Cinematic Redesign — Shared Types & Engine Configuration
 * Defines generative states, device tiers, geometric budgets, and callback interfaces.
 */

export enum DeviceTier {
  Tier1_DesktopHigh = "Tier1_DesktopHigh",
  Tier2_DesktopStandard = "Tier2_DesktopStandard",
  Tier3_Tablet = "Tier3_Tablet",
  Tier4_Mobile = "Tier4_Mobile",
  Tier5_Fallback = "Tier5_Fallback",
}

export enum GenerativeState {
  Fragmented = 0,     // Dispersed organizational knowledge shards
  Converging = 1,     // Gravitational alignment into streamlines
  Organizing = 2,     // Emerging regional neural clusters
  CoherentBrain = 3,  // Unmistakable dual-hemisphere brain architecture
  ActiveFlow = 4,     // High-velocity synaptic knowledge transmission
}

export interface ParticleBudget {
  tier: DeviceTier;
  shardCount: number;           // Instanced 3D faceted tetrahedral shards
  filamentCount: number;        // Neural filament geometric connection count
  dustCount: number;            // Ambient volumetric cosmic particles
  crystalCount: number;         // Backward compatibility alias
  foregroundCrystalCount: number;
  nodeCount: number;            // Backward compatibility alias
  lineCount: number;            // Backward compatibility alias
  dprCap: number;
  enableCurlNoise: boolean;
  enableSizeAttenuation: boolean;
}

export const PARTICLE_BUDGETS: Record<DeviceTier, ParticleBudget> = {
  [DeviceTier.Tier1_DesktopHigh]: {
    tier: DeviceTier.Tier1_DesktopHigh,
    shardCount: 16000,
    filamentCount: 1400,
    dustCount: 4000,
    crystalCount: 16000,
    foregroundCrystalCount: 20,
    nodeCount: 4000,
    lineCount: 1400,
    dprCap: 1.5,
    enableCurlNoise: true,
    enableSizeAttenuation: true,
  },
  [DeviceTier.Tier2_DesktopStandard]: {
    tier: DeviceTier.Tier2_DesktopStandard,
    shardCount: 12000,
    filamentCount: 1000,
    dustCount: 2500,
    crystalCount: 12000,
    foregroundCrystalCount: 16,
    nodeCount: 2500,
    lineCount: 1000,
    dprCap: 1.25,
    enableCurlNoise: true,
    enableSizeAttenuation: true,
  },
  [DeviceTier.Tier3_Tablet]: {
    tier: DeviceTier.Tier3_Tablet,
    shardCount: 6000,
    filamentCount: 600,
    dustCount: 1500,
    crystalCount: 6000,
    foregroundCrystalCount: 10,
    nodeCount: 1500,
    lineCount: 600,
    dprCap: 1.25,
    enableCurlNoise: false,
    enableSizeAttenuation: true,
  },
  [DeviceTier.Tier4_Mobile]: {
    tier: DeviceTier.Tier4_Mobile,
    shardCount: 3000,
    filamentCount: 300,
    dustCount: 800,
    crystalCount: 3000,
    foregroundCrystalCount: 0,
    nodeCount: 800,
    lineCount: 300,
    dprCap: 1.0,
    enableCurlNoise: false,
    enableSizeAttenuation: false,
  },
  [DeviceTier.Tier5_Fallback]: {
    tier: DeviceTier.Tier5_Fallback,
    shardCount: 0,
    filamentCount: 0,
    dustCount: 0,
    crystalCount: 0,
    foregroundCrystalCount: 0,
    nodeCount: 0,
    lineCount: 0,
    dprCap: 1.0,
    enableCurlNoise: false,
    enableSizeAttenuation: false,
  },
};

export interface EngineCallbacks {
  onContextLost?: () => void;
  onContextRestored?: () => void;
  onFpsDegrade?: (avgFps: number) => void;
}

export interface BrainEngineOptions extends EngineCallbacks {
  tier?: DeviceTier;
  targetCanvas?: HTMLCanvasElement;
  asymmetric?: boolean;
}
