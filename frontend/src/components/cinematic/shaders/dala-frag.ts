/**
 * Brain-Co Cinematic Redesign — Dala-Grade Fragment Shader
 * Renders faceted crystal shards with luminous crystalline wireframe edges,
 * translucent obsidian glass facets, sharp specular glints, optical depth defocus,
 * and procedural film grain dither.
 */

export const DALA_FRAGMENT_SHADER = /* glsl */ `
precision highp float;

uniform float u_opacity;

varying vec3 vBarycentric;
varying vec3 vColor;
varying float vAlpha;
varying float vSpecular;
varying float vFresnel;
varying float vDepthDefocus;

void main() {
  // 1. Facet Wireframe Edge vs Glass Interior via Screen-Space Barycentric Derivatives
  vec3 d = fwidth(vBarycentric);
  vec3 a3 = smoothstep(vec3(0.0), d * 1.6, vBarycentric);
  float edgeFactor = 1.0 - min(min(a3.x, a3.y), a3.z);

  // 2. Interior Glass Facet (subtle obsidian tint, high specular sheen)
  // Transparent inside allows background void and neighboring shards to be seen
  float faceAlpha = mix(0.04, 0.45, vSpecular) * vAlpha;
  vec3 faceColor = vColor * (0.35 + vSpecular * 0.95);

  // 3. Crystalline Wireframe Edges (bright, high-contrast luminous lines)
  vec3 edgeColor = vColor * 1.75 + vec3(0.15, 0.15, 0.20);
  if (vSpecular > 0.15) {
    edgeColor += vec3(0.9, 0.9, 1.0) * (vSpecular - 0.15) * 2.2;
  }
  float edgeAlpha = vAlpha * 0.98;

  vec3 color = mix(faceColor, edgeColor, edgeFactor);
  float finalAlpha = mix(faceAlpha, edgeAlpha, edgeFactor) * u_opacity;

  // 4. Razor-Sharp Depth Contrast (Preserves luminous wireframe definition without milky defocus)
  // vDepthDefocus subtly enhances distant atmospheric depth without reducing facet edge contrast
  if (vDepthDefocus > 0.75) {
    color *= 0.92;
  }

  // 5. High-Frequency Analog Film Grain Dither (eliminates 8-bit banding, adds cinema texture)
  float noise = fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453);
  vec3 dither = (vec3(noise) - 0.5) * 0.024;
  color += dither;

  gl_FragColor = vec4(color, finalAlpha);
}
`;
