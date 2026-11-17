/**
 * Brain-Co Cinematic Redesign — Multi-State Particle Vertex Shader
 * Supports smooth 3-stage morphing:
 * Fragmented Shards -> Converging Vortex -> Coherent Dual-Hemisphere Brain.
 * Features 3D Key/Fill/Fresnel lighting and traveling action potentials.
 */

export const PARTICLE_VERTEX_SHADER = /* glsl */ `
uniform float uProgress;
uniform float uTime;
uniform float uNoiseStrength;
uniform float uDpr;
uniform float uBaseSize;
uniform float uSizeAttenuation;

attribute vec3 aTargetConverge;
attribute vec3 aTargetBrain;
attribute vec3 aNormal;
attribute float aRegion;
attribute float aPhase;
attribute float aSize;
attribute float aAlpha;

varying vec3 vColor;
varying float vAlpha;
varying float vPulse;

// Simplex 3D noise
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x) { return mod289(((x * 34.0) + 1.0) * x); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

float snoise(vec3 v) {
  const vec2 C = vec2(1.0 / 6.0, 1.0 / 3.0);
  const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);

  vec3 i  = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);

  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min(g.xyz, l.zxy);
  vec3 i2 = max(g.xyz, l.zxy);

  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;
  vec3 x3 = x0 - 0.5;

  i = mod289(i);
  vec4 p = permute(permute(permute(
             i.z + vec4(0.0, i1.z, i2.z, 1.0))
           + i.y + vec4(0.0, i1.y, i2.y, 1.0))
           + i.x + vec4(0.0, i1.x, i2.x, 1.0));

  vec3 ns = 0.142857142857 * D.wyz - D.xzx;
  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);

  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_);

  vec4 x = x_ *ns.x + ns.yyyy;
  vec4 y = y_ *ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);

  vec4 b0 = vec4(x.xy, y.xy);
  vec4 b1 = vec4(x.zw, y.zw);

  vec4 s0 = floor(b0) * 2.0 + 1.0;
  vec4 s1 = floor(b1) * 2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));

  vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
  vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;

  vec3 p0 = vec3(a0.xy, h.x);
  vec3 p1 = vec3(a0.zw, h.y);
  vec3 p2 = vec3(a1.xy, h.z);
  vec3 p3 = vec3(a1.zw, h.w);

  vec4 norm = taylorInvSqrt(vec4(dot(p0, p0), dot(p1, p1), dot(p2, p2), dot(p3, p3)));
  p0 *= norm.x;
  p1 *= norm.y;
  p2 *= norm.z;
  p3 *= norm.w;

  vec4 m = max(0.6 - vec4(dot(x0, x0), dot(x1, x1), dot(x2, x2), dot(x3, x3)), 0.0);
  m = m * m;
  return 42.0 * dot(m * m, vec4(dot(p0, x0), dot(p1, x1), dot(p2, x2), dot(p3, x3)));
}

vec3 curlNoise(vec3 p) {
  const float e = 0.05;
  float n1 = snoise(vec3(p.x, p.y + e, p.z));
  float n2 = snoise(vec3(p.x, p.y - e, p.z));
  float n3 = snoise(vec3(p.x, p.y, p.z + e));
  float n4 = snoise(vec3(p.x, p.y, p.z - e));
  float n5 = snoise(vec3(p.x + e, p.y, p.z));
  float n6 = snoise(vec3(p.x - e, p.y, p.z));

  float x = (n1 - n2) - (n3 - n4);
  float y = (n3 - n4) - (n5 - n6);
  float z = (n5 - n6) - (n1 - n2);

  return normalize(vec3(x, y, z));
}

void main() {
  // Continuous 3-state morphing pipeline:
  // Phase 1 (0.0 -> 0.35): Fragmented Shards -> Converging Vortex
  // Phase 2 (0.35 -> 1.0): Converging Vortex -> Coherent Dual-Hemisphere Brain
  vec3 mixedPos;
  float brainWeight = 0.0;

  if (uProgress < 0.35) {
    float t1 = smoothstep(0.0, 0.35, uProgress);
    mixedPos = mix(position, aTargetConverge, t1);
    brainWeight = 0.0;
  } else {
    float t2 = smoothstep(0.35, 1.0, uProgress);
    mixedPos = mix(aTargetConverge, aTargetBrain, t2);
    brainWeight = t2;
  }

  // Organic idle curl displacement
  if (uNoiseStrength > 0.001) {
    vec3 noiseSeed = mixedPos * 0.35 + vec3(uTime * 0.05) + vec3(aPhase * 3.0);
    vec3 curl = curlNoise(noiseSeed);
    float noiseScale = mix(0.70, 0.12, brainWeight) * uNoiseStrength;
    mixedPos += curl * noiseScale;
  }

  vec4 mvPosition = modelViewMatrix * vec4(mixedPos, 1.0);
  gl_Position = projectionMatrix * mvPosition;

  // View vector & normal vector in view-space
  vec3 viewDir = normalize(-mvPosition.xyz);
  vec3 radialNormal = normalize(mixedPos);
  vec3 morphNormal = normalize(mix(radialNormal, aNormal, brainWeight));
  vec3 normalView = normalize(normalMatrix * morphNormal);

  // Directional Lighting & Fresnel Rim
  vec3 keyLightDir = normalize(vec3(0.65, 0.95, 1.15));
  float keyDiff = max(0.0, dot(normalView, keyLightDir));

  vec3 fillLightDir = normalize(vec3(-0.75, -0.40, -0.65));
  float fillDiff = max(0.0, dot(normalView, fillLightDir));

  float fresnel = pow(1.0 - max(0.0, dot(normalView, viewDir)), 2.6);

  // Brain-Co Color Palette
  vec3 cCyan     = vec3(0.0, 0.85, 1.0);    // Neural activity (#00d8ff)
  vec3 cBlue     = vec3(0.05, 0.45, 0.98);  // Electric blue (#0d73fa)
  vec3 cTeal     = vec3(0.08, 0.52, 0.43);  // Structural teal (#15846e)
  vec3 cViolet   = vec3(0.50, 0.32, 1.0);   // Electric violet (#8052ff)
  vec3 cPurple   = vec3(0.18, 0.07, 0.42);  // Midnight sulci shadows (#2e126b)
  vec3 cAmber    = vec3(1.0, 0.72, 0.16);   // Warm amber highlight (#ffb829)
  vec3 cMagenta  = vec3(1.0, 0.0, 0.50);    // Synaptic action potential (#ff007f)

  // Structural base color assignment
  vec3 baseColor = cBlue;
  if (aRegion < 0.5) {
    baseColor = mix(cBlue, cCyan, keyDiff * 0.8 + 0.2);
  } else if (aRegion < 1.5) {
    baseColor = mix(cPurple, cViolet, fillDiff * 0.7 + 0.3);
  } else if (aRegion < 2.5) {
    baseColor = mix(cTeal, cCyan, keyDiff * 0.6 + 0.4);
  } else if (aRegion < 3.5) {
    baseColor = mix(cCyan, cMagenta, 0.45);
  } else {
    baseColor = mix(cViolet, cTeal, keyDiff * 0.5 + 0.3);
  }

  // Neural action potential propagation wave
  float wave = sin(uTime * 2.4 - length(aTargetBrain) * 3.2 + aPhase * 6.28);
  float pulse = smoothstep(0.72, 0.98, wave) * brainWeight;
  if (aRegion > 2.5 && aRegion < 3.5) {
    pulse *= 1.35;
  }
  vPulse = pulse;

  // Light composite
  vec3 litColor = baseColor * (0.32 + keyDiff * 0.75 + fillDiff * 0.25);
  litColor += cCyan * (fresnel * 0.70);
  litColor = mix(litColor, cMagenta, pulse * 0.55);
  litColor += cAmber * (pulse * 0.35);

  // Dust color blend during state 1/2
  vec3 dustColor = mix(vec3(0.15, 0.45, 0.85), vec3(0.70, 0.85, 1.0), aPhase);
  vColor = mix(dustColor, litColor, brainWeight);

  // Depth fade
  float depthFade = clamp(1.0 - (length(mvPosition.xyz) - 5.0) / 6.0, 0.35, 1.0);
  vAlpha = aAlpha * depthFade * mix(0.65, 0.92, brainWeight);
  if (pulse > 0.08) {
    vAlpha = min(1.0, vAlpha + pulse * 0.45);
  }

  // Particle size attenuation
  float size = uBaseSize * aSize * uDpr;
  if (uSizeAttenuation > 0.5) {
    size *= (7.5 / -mvPosition.z);
  }
  size *= (1.0 + pulse * 0.30);
  gl_PointSize = clamp(size, 1.5, 9.5);
}
`;
