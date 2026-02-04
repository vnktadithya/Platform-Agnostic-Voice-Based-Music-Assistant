import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface NeonStreamProps {
    start: [number, number, number]; // Received as Center [0,0,0]
    end: [number, number, number];   // Received as Platform Position
    color: string;
    growTime?: number;
    stayTime?: number;
}

export const NeonStream = ({ start, end, color, growTime = 2.0, stayTime = 2.0 }: NeonStreamProps) => {
    // Cycle Configuration
    // User requested "start from platform and move towards SAM. after reaching, it should stay for 2 seconds and then disappear."
    // We default to a faster grow time (1s) and the requested 2s stay time.
    const GROW_TIME = growTime;
    const STAY_TIME = stayTime;
    const OFF_TIME = 0.5;  // Short off time before unmounting/resetting externally
    const FADE_OUT_TIME = 0.5;

    const particleCount = 700;

    // Refs
    const meshRef = useRef<THREE.InstancedMesh>(null!);
    const dummy = useMemo(() => new THREE.Object3D(), []);

    // State
    const cycleState = useRef({
        timer: 0,
        growth: 0,      // 0..1 (Length of stream)
        opacity: 0,     // 0..1 (Global visibility)
    });

    // Particle Data
    const particles = useMemo(() => {
        const data = [];
        for (let i = 0; i < particleCount; i++) {
            data.push({
                phase: (i / particleCount),
                offset: new THREE.Vector3(
                    (Math.random() - 0.5) * 0.2,
                    (Math.random() - 0.5) * 0.2,
                    (Math.random() - 0.5) * 0.2
                ),
                speed: 0.5 + Math.random() * 0.2,
                size: 0.5 + Math.random() * 0.5
            });
        }
        return data;
    }, [particleCount]);

    // Geometric Data (Static basis)
    const { platformPos } = useMemo(() => {
        // Start = SAM [0,0,0], End = Platform
        const platformVec = new THREE.Vector3(...end);
        return { platformPos: platformVec };
    }, [end]);

    useFrame((state, delta) => {
        if (!meshRef.current) return;

        const time = state.clock.elapsedTime;
        const s = cycleState.current;
        s.timer += delta;

        // --- CYCLE STATE MACHINE ---
        if (s.timer <= GROW_TIME) {
            s.opacity = 1.0;
            s.growth = s.timer / GROW_TIME;
        } else if (s.timer <= GROW_TIME + STAY_TIME) {
            s.growth = 1.0;
            s.opacity = 1.0;
        } else if (s.timer <= GROW_TIME + STAY_TIME + FADE_OUT_TIME) {
            s.growth = 1.0;
            const fadeProgress = (s.timer - (GROW_TIME + STAY_TIME)) / FADE_OUT_TIME;
            s.opacity = 1.0 - fadeProgress;
        } else if (s.timer <= GROW_TIME + STAY_TIME + FADE_OUT_TIME + OFF_TIME) {
            s.growth = 0;
            s.opacity = 0;
        } else {
            s.timer = 0;
            s.growth = 0;
            s.opacity = 1;
        }

        // --- UPDATE PARTICLES ---
        const centerVec = new THREE.Vector3(...start);

        particles.forEach((p, i) => {
            // Flow: FROM Platform TO Center
            let t = (p.phase + time * 0.2 * p.speed) % 1;

            // Lerp from Platform(end) to Center(start)
            const pos = new THREE.Vector3().lerpVectors(platformPos, centerVec, t);

            // Visibility Check: 
            let visible = true;
            if (t > s.growth) visible = false;

            // Wobbly offset
            const pinch = Math.sin(t * Math.PI);
            pos.addScaledVector(p.offset, pinch);

            dummy.position.copy(pos);
            dummy.rotation.set(0, 0, 0);

            let scale = visible ? (p.size * 0.01 * pinch) : 0;
            scale *= s.opacity;

            dummy.scale.setScalar(scale);
            dummy.updateMatrix();
            meshRef.current.setMatrixAt(i, dummy.matrix);
        });

        meshRef.current.instanceMatrix.needsUpdate = true;
    });

    return (
        <group>
            {/* Particles */}
            <instancedMesh ref={meshRef} args={[undefined, undefined, particleCount]}>
                <sphereGeometry args={[1, 16, 16]} />
                <meshBasicMaterial
                    color={new THREE.Color(color).multiplyScalar(3.5)}
                    transparent
                    opacity={0.8}
                    blending={THREE.AdditiveBlending}
                    toneMapped={false}
                />
            </instancedMesh>
        </group>
    );
};
