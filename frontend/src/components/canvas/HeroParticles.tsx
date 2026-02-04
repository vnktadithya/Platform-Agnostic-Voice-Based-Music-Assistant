import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

// --- WAVEFORM BACKGROUND COMPONENT ---
const WaveformBackground = ({ targetColor, targetPos }: { targetColor?: string | null, targetPos?: [number, number, number] | null }) => {

    // Internal state for smooth color interpolation
    const currentColor = useRef(new THREE.Color('#8b5cf6'));
    const currentBias = useRef(0);

    // Custom shader for soft, drifting waveforms
    const shaderArgs = useMemo(() => ({
        uniforms: {
            uTime: { value: 0 },
            uColor: { value: new THREE.Color('#8b5cf6') }, // Violet base
            uBiasX: { value: 0.0 }, // Horizontal bias
        },
        vertexShader: `
            varying vec2 vUv;
            void main() {
                vUv = uv;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
        fragmentShader: `
            uniform float uTime;
            uniform vec3 uColor;
            uniform float uBiasX;
            varying vec2 vUv;

            void main() {
                // Horizontal drift + Bias
                // Bias subtly shifts the "center" of waves or the phase
                float t = uTime * 0.05; 
                
                // Shift coordinate system based on bias
                // vUv.x is 0..1. Bias is approx -0.5 to 0.5
                // We shift the wave phase based on bias
                // "Subtle background wave bias toward hovered platform"
                // Using bias to slightly offset the wave phase based on x position
                float biasOffset = uBiasX * 0.2 * (1.0 - abs(vUv.x - 0.5) * 2.0); // Focus bias near center?
                
                // Simple phase shift:
                vec2 uv = vUv;
                uv.x -= uBiasX * 0.05; // Subtle shift towards bias direction

                // Create multiple sine waves
                float wave1 = sin(uv.x * 3.0 + t) * 0.2;
                float wave2 = sin(uv.x * 5.0 - t * 0.5) * 0.1;
                float wave3 = sin(uv.x * 2.0 + t * 0.2) * 0.15;
                
                // Combine and center them vertically
                // Add a small vertical tilt based on bias? No, horizontal bias requested.
                float combinedWave = 0.5 + wave1 + wave2 + wave3;
                
                // Calculate distance from UV Y to the combined wave height
                float dist = abs(uv.y - combinedWave);
                
                // Soft blur edge: 1.0 at center, falling off quickly
                // "Blurred edges"
                float alpha = smoothstep(0.2, 0.0, dist);
                
                // Opacity drift (faint)
                // "5-10% opacity" -> multiplier around 0.05 - 0.1
                // Increased to 0.18 per user request for better visibility
                alpha *= 0.18; 

                // "Sound Presence": Low-frequency pulse
                // 5-8s cycle -> uTime * ~0.8 to 1.0. Let's use 0.8 (~7.8s cycle)
                float pulse = 0.5 + 0.5 * sin(uTime * 0.8); // 0 to 1
                // Modulate amplitude slightly: Base 0.8 + 0.4 var
                float breath = 0.6 + 0.4 * pulse;
                alpha *= breath;

                gl_FragColor = vec4(uColor, alpha);
            }
        `,
        transparent: true,
        depthWrite: false,
    }), []);

    const materialRef = useRef<THREE.ShaderMaterial>(null!);
    const meshRef = useRef<THREE.Mesh>(null!);

    useFrame((state) => {
        const { camera, clock } = state;
        const time = clock.elapsedTime;

        if (meshRef.current) {
            // --- LOCK TO CAMERA (Infinite Background) ---
            meshRef.current.position.copy(camera.position);
            meshRef.current.quaternion.copy(camera.quaternion);
            meshRef.current.translateZ(-10); // Push back

            const cam = camera as THREE.PerspectiveCamera;
            if (cam.isPerspectiveCamera) {
                // Calculate scale to fill the frustum at depth -10
                // Height = 2 * tan(fov/2) * distance
                const scaleY = 2 * Math.tan((cam.fov * Math.PI) / 180 / 2) * 10;
                const scaleX = scaleY * cam.aspect;
                // Add a bit of overscan (1.2) to be safe
                meshRef.current.scale.set(scaleX * 1.2, scaleY * 1.2, 1);
            }
        }

        if (materialRef.current) {
            materialRef.current.uniforms.uTime.value = time;

            // Color Harmony Interpolation
            const target = new THREE.Color(targetColor || '#8b5cf6');
            currentColor.current.lerp(target, 0.5); // Increased speed to be visible in ~2-3s
            materialRef.current.uniforms.uColor.value.copy(currentColor.current);

            // Bias Interpolation
            // Map targetPos.x (world approx -8 to 8) to bias (-1 to 1)
            let targetBias = 0;
            if (targetPos) {
                // targetPos is [x, y, z]. World width typically visible is -10 to 10 approx at depth 0
                // Background is at -5 depth, so it covers even wider.
                // We want bias -1 (left) to 1 (right).
                targetBias = Math.max(-1, Math.min(1, targetPos[0] / 8));
            }
            // Lerp bias smoothly
            currentBias.current += (targetBias - currentBias.current) * 0.05;
            materialRef.current.uniforms.uBiasX.value = currentBias.current;
        }
    });

    return (
        // Large plane covers background
        <mesh ref={meshRef}>
            <planeGeometry args={[1, 1]} />
            <shaderMaterial ref={materialRef} {...shaderArgs} />
        </mesh>
    );
};

// --- STAR FIELD COMPONENT ---
const Particles = ({ connecting }: { connecting: boolean }) => {
    const particlesRef = useRef<THREE.Points>(null!);
    const particleCount = 1500;

    // Used for the "ripple" state
    const rippleRef = useRef(0);

    const initialPositions = useMemo(() => {
        const pos = new Float32Array(particleCount * 3);
        const spread = 40;
        for (let i = 0; i < particleCount * 3; i += 3) {
            pos[i] = (Math.random() - 0.5) * spread;
            pos[i + 1] = (Math.random() - 0.5) * spread;
            pos[i + 2] = (Math.random() - 0.5) * spread;
        }
        return pos;
    }, []);

    // Create a circular texture on the fly to avoid asset dependencies
    const circleTexture = useMemo(() => {
        const canvas = document.createElement('canvas');
        canvas.width = 32;
        canvas.height = 32;
        const ctx = canvas.getContext('2d');
        if (ctx) {
            ctx.beginPath();
            ctx.arc(16, 16, 14, 0, Math.PI * 2);
            ctx.fillStyle = 'white';
            ctx.fill();
        }
        return new THREE.CanvasTexture(canvas);
    }, []);

    useFrame((state, delta) => {
        if (!particlesRef.current) return;

        const time = state.clock.elapsedTime;
        const positions = particlesRef.current.geometry.attributes.position.array as Float32Array;

        // DNA Interaction Logic:
        // If connecting, ripple increases. If not, it decays.
        if (connecting) {
            rippleRef.current += delta * 2.0; // Ripple spreads out
        } else {
            rippleRef.current = 0; // Reset
        }
        const rippleDist = rippleRef.current * 5.0; // Speed of spread

        for (let i = 0; i < particleCount; i++) {
            const i3 = i * 3;
            const x = initialPositions[i3];
            const y = initialPositions[i3 + 1];
            const z = initialPositions[i3 + 2];

            // Standard Audio-reactive "breathing" logic (Background)
            let waveY = Math.sin(time * 0.5 + x * 0.5) * 0.5;
            let breatheZ = Math.cos(time * 0.3 + y * 0.3) * 0.5;

            // DNA INTERACTION: "Teach the background"
            if (connecting) {
                // Calculate distance from center (SAM)
                const dist = Math.sqrt(x * x + y * y + z * z);

                // --- 1. Faint Wave Ripple ---
                // A wave that travels outwards: sin(distance - rippleTime)
                // Only affect if the wave front is near this particle
                const waveFront = Math.abs(dist - rippleDist);
                const rippleEffect = Math.max(0, 1 - waveFront * 0.5); // 1 at wave front, 0 elsewhere

                if (rippleEffect > 0) {
                    // Push particles slightly outward/upward as the ripple passes
                    waveY += rippleEffect * 0.5 * Math.sin(time * 10);
                    breatheZ += rippleEffect * 0.5;
                }

                // --- 2. Alignment ---
                // "Particles slightly align" -> Reduce chaos, conform to a slight grid or flow
                // We'll subtly pull Y towards 0 (a disc) or align to flow
                // Let's damp the noise slightly based on ripple
                // (Here implemented as a slight "taming" of the sine wave drift)
                waveY *= 0.5;
            }

            positions[i3] = x;
            positions[i3 + 1] = y + waveY;
            positions[i3 + 2] = z + breatheZ;
        }

        particlesRef.current.geometry.attributes.position.needsUpdate = true;

        // Alignment Effect:
        // If connecting, spin/align the whole field slightly faster or lock it
        const targetRotationSpeed = connecting ? 0.1 : 0.02;
        particlesRef.current.rotation.y += (targetRotationSpeed - particlesRef.current.rotation.y) * 0.05; // Smooth accel
    });

    return (
        <points ref={particlesRef}>
            <bufferGeometry>
                <bufferAttribute
                    attach="attributes-position"
                    count={particleCount}
                    array={new Float32Array(initialPositions)}
                    itemSize={3}
                    args={[new Float32Array(initialPositions), 3]}
                />
            </bufferGeometry>
            <pointsMaterial
                size={0.15}
                color={connecting ? "#c4b5fd" : "#a78bfa"} // Slightly brighter/whiter when connecting
                map={circleTexture}
                transparent
                alphaTest={0.5}
                opacity={0.8}
                sizeAttenuation
                blending={THREE.AdditiveBlending}
                depthWrite={false}
            />
        </points>
    );
};

export const HeroParticles = ({ connecting, hoveredColor, hoveredPos }: { connecting?: boolean, hoveredColor?: string | null, hoveredPos?: [number, number, number] | null }) => {
    return (
        <group>
            <ambientLight intensity={0.4} />

            <pointLight position={[10, 10, 10]} intensity={1} color="#8b5cf6" />
            <pointLight position={[-10, -10, -10]} intensity={0.5} color="#3b82f6" />
            <spotLight position={[0, 10, 0]} angle={0.3} penumbra={1} intensity={1} color="#22d3ee" />

            <WaveformBackground targetColor={hoveredColor} targetPos={hoveredPos} />

            {/* Pass connecting state to particles */}
            <Particles connecting={!!connecting} />

            <OrbitControls enableZoom={false} enablePan={false} />
        </group>
    );
};
