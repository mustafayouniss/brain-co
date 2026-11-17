/**
 * Brain-Co Cinematic Redesign — Dala-Grade Vertex Shader
 * Multi-state continuous morphing (0.0 -> 3.0), GPU tumbling rotation,
 * interactive cursor repulsion, faceted lighting, and optical depth computation.
 */

export const DALA_VERTEX_SHADER = /* glsl */ `
precision highp float;

uniform float u_progress;   // [0.0, 3.0] continuous narrative scroll scrub
uniform float u_time;       // continuous animation clock
uniform vec2 u_mouse;       // interactive cursor [-1.0, 1.0]

// Instanced Attributes (Packed for WebGL attribute limits <= 16)
attribute vec3 aBarycentric;     // Barycentric coordinates for edge detection
attribute vec3 aInstanceTarget0; // State 0: Hero Vortex
attribute vec3 aInstanceTarget1; // State 1: Fragmentation Scatter
attribute vec3 aInstanceTarget2; // State 2: Convergence Vortex
attribute vec3 aInstanceTarget3; // State 3: Coalesced Brain
attribute vec4 aInstanceRot;    // xyz: rotAxis, w: rotSpeed
attribute vec4 aInstanceParams; // x: scale, y: colorGroup, z: phase, w: depthLayer

// Varyings to Fragment Shader
varying vec3 vBarycentric;
varying vec3 vColor;
varying float vAlpha;
varying float vSpecular;
varying float vFresnel;
varying float vDepthDefocus;

// Rodrigues rotation formula: rotates vector v around unit axis k by angle theta
vec3 rotateAxisAngle(vec3 v, vec3 k, float theta) {
  float cosTheta = cos(theta);
  float sinTheta = sin(theta);
  return v * cosTheta + cross(k, v) * sinTheta + k * dot(k, v) * (1.0 - cosTheta);
}

void main() {
  vBarycentric = aBarycentric;

  // 1. Continuous 4-Stage Morphing (0.0 -> 3.0)
  vec3 instanceCenter;
  float p = clamp(u_progress, 0.0, 3.0);

  if (p < 1.0) {
    // Stage 0 -> 1: Hero Vortex -> Fragmentation Scatter
    float t = smoothstep(0.0, 1.0, p);
    instanceCenter = mix(aInstanceTarget0, aInstanceTarget1, t);
  } else if (p < 2.0) {
    // Stage 1 -> 2: Scatter -> Convergence Vortex
    float t = smoothstep(1.0, 2.0, p);
    instanceCenter = mix(aInstanceTarget1, aInstanceTarget2, t);
  } else {
    // Stage 2 -> 3: Convergence Vortex -> Coalesced Brain
    float t = smoothstep(2.0, 3.0, p);
    instanceCenter = mix(aInstanceTarget2, aInstanceTarget3, t);
  }

  // 2. Interactive Cursor Repulsion (Active exclusively on user cursor movement)
  if (length(u_mouse) > 0.005) {
    vec3 screenPos = instanceCenter;
    vec2 delta = screenPos.xy - vec2(u_mouse.x * 2.5, u_mouse.y * 1.8);
    float distToMouse = length(delta);
    if (distToMouse < 1.1) {
      float repelForce = (1.0 - distToMouse / 1.1) * 0.25;
      instanceCenter.xy += normalize(delta) * repelForce;
    }
  }

  // 3. Per-Instance Unpacking & Anatomical Normal Alignment
  vec3 norm = normalize(aInstanceRot.xyz);
  float rotSpeed = aInstanceRot.w;
  float instanceScale = aInstanceParams.x;
  float colorGroup = aInstanceParams.y;
  float instancePhase = aInstanceParams.z;
  float depthLayer = aInstanceParams.w;

  // Align pyramid apex (local +Y) with true outward anatomical surface normal
  vec3 up = vec3(0.0, 1.0, 0.0);
  vec3 alignAxis = cross(up, norm);
  float alignLen = length(alignAxis);
  float alignAngle = acos(clamp(dot(up, norm), -1.0, 1.0));
  vec3 k = alignLen > 0.001 ? normalize(alignAxis) : vec3(1.0, 0.0, 0.0);

  vec3 alignedPos = rotateAxisAngle(position, k, alignAngle);
  vec3 alignedNorm = rotateAxisAngle(normal, k, alignAngle);

  // Subtle organic breathing oscillation around normal for facet specular sparkle
  float tumbleAngle = sin(u_time * 0.85 + instancePhase) * 0.25;
  vec3 rotatedLocalPos = rotateAxisAngle(alignedPos, norm, tumbleAngle) * instanceScale;
  vec3 rotatedFacetNormal = rotateAxisAngle(alignedNorm, norm, tumbleAngle);

  // 4. World and View Position
  vec3 worldPos = instanceCenter + rotatedLocalPos;
  vec4 mvPosition = modelViewMatrix * vec4(worldPos, 1.0);
  gl_Position = projectionMatrix * mvPosition;

  // 5. Faceted Lighting Vectors
  vec3 viewDir = normalize(-mvPosition.xyz);
  vec3 normalView = normalize(normalMatrix * rotatedFacetNormal);

  // Directional Key Light (Warm golden-white from top-right)
  vec3 keyLightDir = normalize(vec3(0.65, 0.95, 1.15));
  float keyDiff = max(0.0, dot(normalView, keyLightDir));

  // Directional Fill Light (Cool violet from bottom-left)
  vec3 fillLightDir = normalize(vec3(-0.75, -0.40, -0.65));
  float fillDiff = max(0.0, dot(normalView, fillLightDir));

  // Blinn-Phong Specular Glint (Sharp facet sheen)
  vec3 halfVector = normalize(keyLightDir + viewDir);
  float spec = pow(max(0.0, dot(normalView, halfVector)), 24.0);
  vSpecular = spec;

  // View-Space Fresnel Rim Highlight
  float fresnel = pow(1.0 - max(0.0, dot(normalView, viewDir)), 2.5);
  vFresnel = fresnel;

  // 6. Reference Color Science: Golden Rim, Platinum Dorsal Face, Chromatic Crevices
  vec3 cGold   = vec3(1.0, 0.72, 0.16);   // Luminous Amber/Gold (#ffb829)
  vec3 cWhite  = vec3(0.98, 0.98, 1.0);   // Platinum Specular White (#fafaff)
  vec3 cCyan   = vec3(0.0, 0.92, 1.0);    // Electric Cyan (#00eaff)
  vec3 cViolet = vec3(0.68, 0.28, 0.96);  // Vivid Royal Violet / Magenta (#a855f7)
  vec3 cDark   = vec3(0.12, 0.12, 0.16);  // Deep Obsidian / Charcoal Sulcal Valley

  // Base shard color from group
  vec3 baseColor = cGold;
  if (colorGroup < 0.5) {
    // Group 0: Golden Amber Rim (accentuated by grazing Fresnel)
    baseColor = mix(cGold, vec3(1.0, 0.85, 0.35), fresnel * 0.45);
  } else if (colorGroup < 1.5) {
    // Group 1: Platinum Specular White Dorsal Surface
    baseColor = mix(cWhite, vec3(0.85, 0.90, 1.0), fillDiff * 0.3);
  } else if (colorGroup < 2.5) {
    // Group 2: Electric Cyan / Action Potentials
    baseColor = mix(cCyan, cViolet, sin(instancePhase) * 0.5 + 0.5);
  } else {
    // Group 3: Deep Obsidian / Charcoal Sulcal Shadow Valleys
    baseColor = cDark;
  }

  // Final lit color composite:
  vec3 litColor = baseColor * (0.40 + keyDiff * 0.60 + fillDiff * 0.25);
  litColor += cWhite * (spec * 0.95);
  // Enhance golden rim with Fresnel edge reflection
  if (colorGroup < 0.5) {
    litColor += cGold * (fresnel * 0.85);
  } else {
    litColor += cCyan * (fresnel * 0.45);
  }

  vColor = litColor;

  // 7. Optical Depth-of-Field Defocus
  // Focal plane is at Z = 0.0 in world space
  float focusDist = 0.0;
  float depthDist = abs(instanceCenter.z - focusDist);
  vDepthDefocus = clamp(depthDist / 3.5, 0.0, 1.0);

  // Depth attenuation
  float depthFade = clamp(1.0 - (length(mvPosition.xyz) - 4.5) / 5.5, 0.35, 1.0);
  vAlpha = depthFade * mix(0.85, 0.98, smoothstep(1.5, 2.5, p));
}
`;
