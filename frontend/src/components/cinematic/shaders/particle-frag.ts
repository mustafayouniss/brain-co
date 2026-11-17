/**
 * Brain-Co Cinematic Redesign — Particle Fragment Shader
 * Renders anti-aliased, circular neural points with luminous cores,
 * soft atmospheric glow, and rich spectral color fidelity.
 * Reference: docs/architecture/cinematic_frontend_redesign_plan.md (V3.3)
 */

export const PARTICLE_FRAGMENT_SHADER = /* glsl */ `
precision highp float;

uniform float uOpacity;

varying vec3 vColor;
varying float vAlpha;
varying float vPulse;

void main() {
  // Distance from center of point sprite [0.0, 0.5]
  vec2 coord = gl_PointCoord - vec2(0.5);
  float dist = length(coord);

  // Hard disc cull
  if (dist > 0.5) {
    discard;
  }

  // Dual-profile glow:
  // 1. Brilliant core needle
  float core = smoothstep(0.20, 0.0, dist);
  // 2. Soft atmospheric edge
  float edge = smoothstep(0.5, 0.05, dist);

  // Combine core and aura
  float shape = mix(edge * 0.75, 1.0, core * 0.45);

  // Boost pulse center brightness
  vec3 finalColor = vColor;
  if (vPulse > 0.05) {
    finalColor += vec3(0.15, 0.25, 0.35) * vPulse * core;
  }

  float finalAlpha = uOpacity * vAlpha * shape;

  gl_FragColor = vec4(finalColor, finalAlpha);
}
`;
