import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useStore } from '../../store/useStore';

/* ---------------- EYES ---------------- */
export const Eye = ({ position, blink, scale = [1, 1, 1], color = "white" }: { position: [number, number, number], blink: boolean, scale: number[], color: string }) => {
    const mesh = useRef<THREE.Mesh>(null!);

    useFrame((_state, _delta) => {
        if (!mesh.current) return;

        // Blinking Animation (Lerp to 0.05 on Y axis when blinking)
        const targetY = blink ? 0.05 : scale[1];
        const targetX = scale[0];

        // Smooth transition
        mesh.current.scale.y = THREE.MathUtils.lerp(mesh.current.scale.y, targetY, 0.4);
        mesh.current.scale.x = THREE.MathUtils.lerp(mesh.current.scale.x, targetX, 0.2);
    });

    return (
        <mesh ref={mesh} position={position} rotation={[0, 0, 0]} castShadow>
            {/* Capsule Geometry: Radius 0.08, Length 0.25 - Matches User Snippet exactly for pill shape */}
            <capsuleGeometry args={[0.08, 0.25, 4, 16]} />
            <meshStandardMaterial
                color={color}
                emissive={color}
                emissiveIntensity={1.5}
                toneMapped={false}
            />
        </mesh>
    );
};



/* ---------------- LISTENING WAVE ---------------- */
export const ListeningWave = () => {
    // TRANSIENT UPDATE: Read from store directly in loop to avoid re-renders
    const lineRef = useRef<THREE.Line>(null!);

    // Geometry setup - Create points once
    const pointsCount = 100;
    const width = 6; // Width of the wave

    // Arrays for attributes
    const positions = useMemo(() => {
        const arr = new Float32Array(pointsCount * 3);
        for (let i = 0; i < pointsCount; i++) {
            const x = (i / (pointsCount - 1)) * width - (width / 2);
            arr[i * 3] = x;
            arr[i * 3 + 1] = 0;
            arr[i * 3 + 2] = 0;
        }
        return arr;
    }, []);

    const colors = useMemo(() => {
        const arr = new Float32Array(pointsCount * 3);
        const color1 = new THREE.Color('#00ccff'); // Cyan
        const color2 = new THREE.Color('#bd00ff'); // Purple
        const tempColor = new THREE.Color();

        for (let i = 0; i < pointsCount; i++) {
            const t = i / (pointsCount - 1);
            tempColor.copy(color1).lerp(color2, t);
            arr[i * 3] = tempColor.r;
            arr[i * 3 + 1] = tempColor.g;
            arr[i * 3 + 2] = tempColor.b;
        }
        return arr;
    }, []);

    useFrame((_state) => {
        if (!lineRef.current) return;

        const time = _state.clock.elapsedTime;
        const positionsAttribute = lineRef.current.geometry.attributes.position;
        // Use transient state
        const currentAudioLevel = useStore.getState().audioLevel || 0;

        // Animate Y positions
        for (let i = 0; i < pointsCount; i++) {
            const x = positions[i * 3]; // original x

            // Taper at edges so wave fades out
            // Normalized x from -1 to 1 (approx) based on width
            const normX = x / (width / 2);
            const taper = Math.max(0, 1 - Math.abs(normX));
            const smoothTaper = taper * taper * (3 - 2 * taper); // Smoothstep

            // Wave Math: Multiple Sines for organic calm feel
            // Base breathing wave (always present)
            const baseWave = Math.sin(x * 1.5 + time * 2.0) * 0.05;

            // Voice active wave (responds to audio)
            // Higher frequency, higher amplitude
            const activeWave = Math.sin(x * 4.0 - time * 8.0) * 0.3 * currentAudioLevel
                + Math.sin(x * 8.0 + time * 12.0) * 0.15 * currentAudioLevel;

            // Combine
            // When silent, settles to baseWave
            // When loud, activeWave dominates
            const y = (baseWave + activeWave) * smoothTaper;

            positionsAttribute.setY(i, y);
        }

        positionsAttribute.needsUpdate = true;
    });

    return (
        // @ts-ignore
        <line ref={lineRef}>
            <bufferGeometry>
                <bufferAttribute
                    attach="attributes-position"
                    count={pointsCount}
                    array={positions}
                    itemSize={3}
                    args={[positions, 3]}
                />
                <bufferAttribute
                    attach="attributes-color"
                    count={pointsCount}
                    array={colors}
                    itemSize={3}
                    args={[colors, 3]}
                />
            </bufferGeometry>
            <lineBasicMaterial
                vertexColors
                transparent
                opacity={0.6}
                linewidth={2} // Note: native WebGL lineWidth is often limited to 1 on Windows
            />
        </line>
    );
};

/* ---------------- LISTENING BAR WAVE ---------------- */
export const BarWave = () => {
    // TRANSIENT UPDATE
    const meshRef = useRef<THREE.InstancedMesh>(null!);
    const count = 40; // Number of bars
    const dummy = useMemo(() => new THREE.Object3D(), []);

    // Generate colors (Cyan to Purple Gradient)
    const colors = useMemo(() => {
        const arr = new Float32Array(count * 3);
        const color1 = new THREE.Color('#00ccff'); // Cyan
        const color2 = new THREE.Color('#bd00ff'); // Purple
        const tempColor = new THREE.Color();

        for (let i = 0; i < count; i++) {
            const t = i / (count - 1);
            tempColor.copy(color1).lerp(color2, t);
            tempColor.toArray(arr, i * 3);
        }
        return arr;
    }, []);

    useFrame((state) => {
        if (!meshRef.current) return;

        const time = state.clock.elapsedTime;
        const currentAudioLevel = useStore.getState().audioLevel || 0;

        for (let i = 0; i < count; i++) {
            // Position spread from -3 to 3
            const spacing = 0.15;
            const x = (i - count / 2) * spacing;

            // Normalized position for shaping (bell curve effect)
            const normX = (i / (count - 1)) * 2 - 1; // -1 to 1
            const bellCurve = Math.exp(-normX * normX * 2); // Taper at edges

            // Wave Logic
            // 1. Idle breathing
            const idle = Math.sin(x * 2.0 + time * 3.0) * 0.15 * bellCurve;

            // 2. Audio reaction (pseudo-spectrum)
            // Use different frequencies for different bars to fake a spectrum
            const active = (Math.sin(time * 15 + i * 134.32) * 0.5 + 0.5) * currentAudioLevel * 1.5 * bellCurve;

            // Height
            const h = 0.2 + Math.max(0, idle + active);

            dummy.position.set(x, 0, 0);
            dummy.scale.set(1, h, 1);
            dummy.updateMatrix();

            meshRef.current.setMatrixAt(i, dummy.matrix);
        }
        meshRef.current.instanceMatrix.needsUpdate = true;
    });

    return (
        <instancedMesh ref={meshRef} args={[undefined, undefined, count]} position={[0, 0, 0]}>
            <capsuleGeometry args={[0.04, 1, 4, 8]} />
            <meshBasicMaterial
                toneMapped={false}
            >
                {/* We use instanceColor attribute for gradient */}
            </meshBasicMaterial>
            <instancedBufferAttribute
                attach="instanceColor"
                args={[colors, 3]}
            />
        </instancedMesh>
    );
};



/* ---------------- SPEAKING PULSE (INTELLIGENCE) ---------------- */
// Soft concentric rings (shells) emitting from SAM
export const SpeakingPulse = () => {
    // TRANSIENT UPDATE
    const meshRef = useRef<THREE.InstancedMesh>(null!);
    const count = 5; // Number of active pulses allowed
    const dummy = useMemo(() => new THREE.Object3D(), []);

    // State to track each pulse's lifecycle [scale, opacity, active]
    // We use a ref to hold state across frames without re-rendering
    const pulses = useRef(new Array(count).fill(null).map(() => ({
        active: false,
        scale: 1,
        opacity: 0,
        startTime: 0
    })));

    useFrame((state) => {
        if (!meshRef.current) return;

        const time = state.clock.elapsedTime;
        const currentAudioLevel = useStore.getState().audioLevel || 0;

        // 1. Spawning Logic
        // Threshold to spawn a new pulse (sensitivity)
        if (currentAudioLevel > 0.1) {
            // Find an inactive pulse or one that is very old
            const availablePulse = pulses.current.find(p => !p.active || (time - p.startTime > 2.0));

            // Limit spawn rate (don't spawn every frame)
            const lastSpawn = Math.max(...pulses.current.map(p => p.startTime));
            if (availablePulse && (time - lastSpawn > 0.2)) {
                availablePulse.active = true;
                availablePulse.startTime = time;
                availablePulse.scale = 1.0; // Start at SAM surface
                availablePulse.opacity = 0.3 * Math.min(1, currentAudioLevel); // Explicit intensity (Subtle)
            }
        }

        // 2. Update Pulses
        pulses.current.forEach((pulse, i) => {
            if (!pulse.active) {
                // Hide offscreen/scale 0
                dummy.scale.set(0, 0, 0);
            } else {
                const age = time - pulse.startTime;

                // Expansion: fast then slow? or linear?
                // "Expand outward slowly"
                pulse.scale = 1.05 + age * 0.4; // Start from edge (1.05)

                // Fade out: "Fade gently"
                // Opacity decays with age
                const lifeParams = Math.max(0, 1 - age / 2.0); // 2 second life
                const currentOpacity = pulse.opacity * lifeParams;

                if (lifeParams <= 0) pulse.active = false;

                dummy.position.set(0, 0, 0);
                dummy.scale.set(pulse.scale, pulse.scale, pulse.scale);
                dummy.updateMatrix();

                meshRef.current.setMatrixAt(i, dummy.matrix);

                // Hack: We need to set opacity per instance. 
                // Since this is basic material, we can't easily do per-instance alpha without custom shader.
                // INNOVATION: We will use the COLOR attribute to pass opacity if we use a custom shader.
                // OR SIMPLER for "Make sure you don't change anything else":
                // Just use varying sizes. 
                // BUT user wants opacity fade.
                // We will use 'setColorAt' to darken it towards black to simulate fade if blending is additive?
                // Let's use MeshBasicMaterial with transparent=true and opacity=1 globally, 
                // and scale the instance color brightness to fade it.
                // (White * 0.5 = Grey ~ transparent in additive blending or just dark on black background)

                const intensity = currentOpacity;
                const c = new THREE.Color('#00f2ff').multiplyScalar(intensity * 0.7); // Soft Blue-ish
                meshRef.current.setColorAt(i, c);
            }
        });

        meshRef.current.instanceMatrix.needsUpdate = true;
        if (meshRef.current.instanceColor) meshRef.current.instanceColor.needsUpdate = true;
    });

    return (
        <instancedMesh ref={meshRef} args={[undefined, undefined, count]}>
            <sphereGeometry args={[1, 32, 32]} />
            {/* transmission material is too heavy for instances usually, use basic transparent */}
            <meshBasicMaterial
                transparent
                blending={THREE.AdditiveBlending}
                depthWrite={false}
                toneMapped={false}
                side={THREE.BackSide} // Only render front face to avoid white background behind SAM
            />
        </instancedMesh>
    );
}
