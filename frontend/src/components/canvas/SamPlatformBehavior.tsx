import { useRef, useState, useEffect, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Environment, MeshTransmissionMaterial, Float } from '@react-three/drei';
import * as THREE from 'three';

/* ---------------- EYES ---------------- */
const Eye = ({ position, blink, scale = [1, 1, 1], color = "white" }: { position: [number, number, number], blink: boolean, scale: number[], color: string }) => {
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

/* ---------------- ORB ---------------- */
interface SamPlatformBehaviorProps {
    lookAtTarget: [number, number, number] | null;
}

export const SamPlatformBehavior = ({ lookAtTarget }: SamPlatformBehaviorProps) => {
    const group = useRef<THREE.Group>(null!);
    const materialRef = useRef<any>(null!);
    const [blink, setBlink] = useState(false);

    // Platform Selection is always "IDLE" basically, or we can use generic state

    // ---------------- STATE MAPPING ----------------
    const visualState = useMemo(() => {
        // Default IDLE state visuals
        return {
            color: '#ffffff', // White
            lightColor: '#ffaa00', // Warm idle light
            eyeScale: [1, 1, 1],
            distortion: 0.3,
            speed: 2,
        };
    }, []);

    // ---------------- BLINK LOOP ----------------
    useEffect(() => {
        let timeout: any;
        const blinkLoop = () => {
            const minTime = 2000;
            const varTime = 3000;
            const nextBlink = minTime + Math.random() * varTime;
            timeout = setTimeout(() => {
                setBlink(true);
                setTimeout(() => setBlink(false), 150);
                blinkLoop();
            }, nextBlink);
        };
        blinkLoop();
        return () => clearTimeout(timeout);
    }, []);

    // ---------------- ANIMATION FRAME ----------------
    useFrame((state, _delta) => {
        if (!group.current) return;

        const time = state.clock.elapsedTime;

        // 1. Look At Logic
        if (lookAtTarget) {
            // Start with RAW platform position
            const targetVec = new THREE.Vector3(...lookAtTarget);

            // A. Bobbing (Matches PlatformOrbit: Local Mesh Position)
            // Phase uses raw X. Amplitude is 0.1 (raw units).
            targetVec.y += Math.sin(time + targetVec.x) * 0.1;

            // B. Rotation (Matches PlatformOrbit: Group Rotation)
            targetVec.applyAxisAngle(new THREE.Vector3(0, 1, 0), time * 0.2);

            // C. Scale (Matches PlatformSelect Group Scale 0.85)
            targetVec.multiplyScalar(0.85);

            // D. Robust Rotation (Quaternion Slerp)
            // Use Matrix4.lookAt to generate the correct rotation matrix for looking at targetVec from (0,0,0)
            targetVec.negate(); // FIX: Align +Z face to target by looking at -Target
            const lookMat = new THREE.Matrix4();
            lookMat.lookAt(new THREE.Vector3(0, 0, 0), targetVec, new THREE.Vector3(0, 1, 0));

            const targetQuat = new THREE.Quaternion();
            targetQuat.setFromRotationMatrix(lookMat);

            // Slerp for smooth, robust tracking (avoids gimbal lock & wrap-around glitches)
            group.current.quaternion.slerp(targetQuat, 0.2);

        } else {
            // Idle wander look
            // Return to IDLE straight position (Identity Quaternion)
            // This ensures smooth transition back to center and removes any residual roll/tilt
            const identityQuat = new THREE.Quaternion(); // Identity = Facing z-forward, upright

            // Slerp back to center
            group.current.quaternion.slerp(identityQuat, 0.05);

            // Optionally add very subtle noise if needed, but USER requested strictly "normal position"
        }

        // 2. Idle Breathing
        const breathingCycle = (Math.sin(time * 0.9) * 0.5 + 0.5);
        const breathingScale = 1.0 + breathingCycle * 0.02;
        const targetScale = breathingScale;

        group.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.2);

        // 3. Sub-pixel Vertical Drift
        const drift = Math.sin(time * 0.5) * 0.015;
        group.current.position.y = drift;

        // 4. Material Updates
        if (materialRef.current) {
            materialRef.current.chromaticAberration = THREE.MathUtils.lerp(materialRef.current.chromaticAberration, 1.5, 0.1);
            materialRef.current.distortion = THREE.MathUtils.lerp(materialRef.current.distortion, visualState.distortion, 0.1);
            materialRef.current.color = new THREE.Color(visualState.color);

            const targetEmissiveIntensity = 0.2 + (breathingCycle * 0.3);
            materialRef.current.emissiveIntensity = THREE.MathUtils.lerp(materialRef.current.emissiveIntensity, targetEmissiveIntensity, 0.1);
        }
    });

    return (
        <group>
            <Environment preset="city" />

            <spotLight
                position={[10, 10, 10]}
                angle={0.15}
                penumbra={1}
                intensity={80}
                color={visualState.lightColor}
                castShadow
            />

            <pointLight
                position={[-10, -10, -10]}
                intensity={40}
                color={'#aa00ff'}
            />

            <ambientLight intensity={0.5} />

            <Float
                speed={visualState.speed}
                rotationIntensity={0.5}
                floatIntensity={1}
                floatingRange={[-0.2, 0.2]}
            >
                <group ref={group}>
                    {/* THE BUBBLE SPHERE */}
                    <mesh>
                        <sphereGeometry args={[1, 64, 64]} />
                        <MeshTransmissionMaterial
                            ref={materialRef}
                            backside
                            samples={16}
                            resolution={1024}
                            transmission={1}
                            roughness={0.1}
                            clearcoat={1}
                            clearcoatRoughness={0.1}
                            thickness={1.2}
                            ior={1.5}
                            chromaticAberration={1.5}
                            anisotropy={0.3}
                            distortion={visualState.distortion}
                            distortionScale={0.5}
                            temporalDistortion={0.2}
                            attenuationDistance={0.5}
                            attenuationColor="#ffffff"
                            color="#ffffff"
                            background={new THREE.Color('#000000')}
                        />
                    </mesh>

                    {/* EYES GROUP */}
                    <group position={[0, 0, 0.9]}>
                        <Eye
                            position={[-0.3, 0.05, 0]}
                            blink={blink}
                            scale={visualState.eyeScale}
                            color={'white'}
                        />
                        <Eye
                            position={[0.3, 0.05, 0]}
                            blink={blink}
                            scale={visualState.eyeScale}
                            color={'white'}
                        />
                    </group>
                </group>
            </Float>
        </group>
    );
};
