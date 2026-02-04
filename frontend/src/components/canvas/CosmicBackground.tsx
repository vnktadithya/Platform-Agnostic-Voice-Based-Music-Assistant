import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Stars } from '@react-three/drei';
import * as THREE from 'three';

// --- SHADERS ---
// Enhanced Vertex Shader for Deep Space Fog
const fogVertexShader = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

// Enhanced Fragment Shader for Aurora/Nebula Glow
const fogFragmentShader = `
  uniform float uTime;
  uniform vec3 uPlatformColor; // New Uniform
  varying vec2 vUv;
  
  // Simplex noise (3D)
  vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
  vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
  vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
  vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }
  float snoise(vec3 v) { 
    const vec2 C = vec2(1.0/6.0, 1.0/3.0);
    const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
    vec3 i = floor(v + dot(v, C.yyy));
    vec3 x0 = v - i + dot(i, C.xxx);
    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g.xyz, l.zxy);
    vec3 i2 = max(g.xyz, l.zxy);
    vec3 x1 = x0 - i1 + C.xxx;
    vec3 x2 = x0 - i2 + C.yyy;
    vec3 x3 = x0 - D.yyy;
    i = mod289(i);
    vec4 p = permute(permute(permute( 
               i.z + vec4(0.0, i1.z, i2.z, 1.0))
             + i.y + vec4(0.0, i1.y, i2.y, 1.0)) 
             + i.x + vec4(0.0, i1.x, i2.x, 1.0));
    float n_ = 0.142857142857;
    vec3 ns = n_ * D.wyz - D.xzx;
    vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_);
    vec4 x = x_ * ns.x + ns.yyyy;
    vec4 y = y_ * ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);
    vec4 b0 = vec4(x.xy, y.xy);
    vec4 b1 = vec4(x.zw, y.zw);
    vec4 s0 = floor(b0)*2.0 + 1.0;
    vec4 s1 = floor(b1)*2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));
    vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
    vec3 p0 = vec3(a0.xy,h.x);
    vec3 p1 = vec3(a0.zw,h.y);
    vec3 p2 = vec3(a0.zw,h.z);
    vec3 p3 = vec3(a1.zw,h.w);
    vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
    p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
    vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
    m = m * m;
    return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
  }

  // Simple Grain Noise
  float random(vec2 uv) {
    return fract(sin(dot(uv.xy, vec2(12.9898, 78.233))) * 43758.5453123);
  }

  void main() {
    // Increased speed for "breathing" effect (0.02 -> 0.05)
    float n = snoise(vec3(vUv * 2.5, uTime * 0.05));
    float n2 = snoise(vec3(vUv * 4.5 + 100.0, uTime * 0.08));
    
    // Deep Midnight Palette (Base)
    vec3 bg = vec3(0.01, 0.01, 0.03); 
    vec3 nebula1 = vec3(0.08, 0.02, 0.20); 
    vec3 nebula2 = vec3(0.02, 0.08, 0.20); 
    
    // Soft Aurora
    float glow = smoothstep(0.35, 0.85, n) * 0.5;
    float glow2 = smoothstep(0.40, 0.90, n2) * 0.4;
    
    vec3 baseColor = bg + nebula1 * glow + nebula2 * glow2;

    // --- PULSE EFFECT ---
    // Smooth pulse between 0.0 and 1.0 using sin(uTime)
    float pulse = sin(uTime * 0.8) * 0.5 + 0.5; 
    
    // Mix the base nebula color with the platform color
    // We keep the mix subtle (max 30%) so it tints the fog instead of replacing it
    vec3 finalColor = mix(baseColor, uPlatformColor * (glow + glow2 + 0.1), pulse * 0.4);

    // Vignette
    float vig = 1.0 - length(vUv - 0.5) * 1.5;
    finalColor *= clamp(vig + 0.5, 0.0, 1.0);
    
    // Subtle Film Grain / Noise
    float grain = random(vUv * uTime) * 0.03; 
    finalColor += grain;

    gl_FragColor = vec4(finalColor, 1.0);
  }
`;

interface CosmicBackgroundProps {
  platformColor?: string | null;
}

export const CosmicBackground = ({ platformColor }: CosmicBackgroundProps) => {
  const mesh = useRef<THREE.Mesh>(null!);
  const parallaxGroup = useRef<THREE.Group>(null!);

  // Initial uniform values
  const uniforms = useMemo(() => ({
    uTime: { value: 0 },
    uPlatformColor: { value: new THREE.Color(0.0, 0.0, 0.0) } // Default black means no tint
  }), []);

  // Update uniform when platformColor changes
  useMemo(() => {
    if (platformColor) {
      uniforms.uPlatformColor.value.set(platformColor);
    } else {
      // Revert to black to disable tint
      uniforms.uPlatformColor.value.set(0x000000);
    }
  }, [platformColor, uniforms]);

  useFrame((state) => {
    const { clock, pointer, camera } = state;
    const time = clock.getElapsedTime();

    // 1. Update Shader Time
    if (mesh.current) {
      (mesh.current.material as THREE.ShaderMaterial).uniforms.uTime.value = time;

      // Lock background plane to camera view (Infinite Void effect)
      mesh.current.position.copy(camera.position);
      mesh.current.quaternion.copy(camera.quaternion);
      mesh.current.translateZ(-50); // Push back

      const cam = camera as THREE.PerspectiveCamera;
      if (cam.isPerspectiveCamera) {
        const scale = 2 * Math.tan((cam.fov * Math.PI) / 180 / 2) * 50;
        mesh.current.scale.set(scale * cam.aspect * 1.2, scale * 1.2, 1);
      }
    }

    // 2. Parallax Logic (Rotate entire group based on mouse)
    if (parallaxGroup.current) {
      // pointer.x goes from -1 to 1. We want a subtle rotation, say +/- 5 degrees (0.08 rad)
      parallaxGroup.current.rotation.y = THREE.MathUtils.lerp(
        parallaxGroup.current.rotation.y,
        pointer.x * 0.05,
        0.05
      );
      parallaxGroup.current.rotation.x = THREE.MathUtils.lerp(
        parallaxGroup.current.rotation.x,
        -pointer.y * 0.05,
        0.05
      );

      // Add a very slow constant rotation to the stars for "dynamic environment"
      parallaxGroup.current.rotation.z = time * 0.005;
    }
  });

  return (
    <group ref={parallaxGroup}>
      {/* Deep Nebula */}
      <mesh ref={mesh}>
        <planeGeometry args={[1, 1]} />
        <shaderMaterial
          vertexShader={fogVertexShader}
          fragmentShader={fogFragmentShader}
          uniforms={uniforms}
          depthWrite={false}
        />
      </mesh>

      {/* Moving Stars */}
      <Stars
        radius={100}
        depth={50}
        count={5000}
        factor={4}
        saturation={0}
        fade
        speed={1}
      />
    </group>
  );
};
