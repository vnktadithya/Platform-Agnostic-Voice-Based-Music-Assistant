import { useRef, useState, useEffect, useMemo, memo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Environment, MeshTransmissionMaterial, Float } from '@react-three/drei';
import * as THREE from 'three';
import { useStore } from '../../store/useStore';
import { Eye, BarWave, SpeakingPulse } from './SamParts';


/* ---------------- ORB ---------------- */
export const SamCore = memo(() => {
    const group = useRef<THREE.Group>(null!);
    const materialRef = useRef<any>(null!);
    const [blink, setBlink] = useState(false);

    // Connect to Store
    const { samState } = useStore();

    // ---------------- STATE MAPPING ----------------
    // Map backend states to visual properties
    const visualState = useMemo(() => {
        switch (samState) {
            case 'LISTENING':
                return {
                    color: '#00ccff', // Cyan/Blue
                    lightColor: '#00ccff',
                    eyeScale: [1.2, 1.2, 1], // Wide open attention
                    distortion: 0.4,
                    speed: 2,
                };
            case 'THINKING':
                return {
                    color: '#bd00ff', // Purple
                    lightColor: '#bd00ff',
                    eyeScale: [1.0, 0.5, 1], // Squinting/Processing
                    distortion: 1.2, // HIGH internal turbulence
                    speed: 5, // Fast float
                };
            case 'SPEAKING':
                return {
                    color: '#004d40', // Gold/Orange (Intelligence)
                    lightColor: '#00f2ff', // Gold
                    eyeScale: [1.1, 1.1, 1], // Normal Happy
                    distortion: 0.3,
                    speed: 2,
                };
            default: // IDLE
                return {
                    color: '#ffffff', // White
                    lightColor: '#ffaa00', // Warm idle light
                    eyeScale: [1, 1, 1],
                    distortion: 0.3,
                    speed: 2,
                };
        }
    }, [samState]);


    // ---------------- BLINK LOOP ----------------
    useEffect(() => {
        let timeout: any;
        const blinkLoop = () => {
            const minTime = samState === 'THINKING' ? 300 : 2000;
            const varTime = samState === 'THINKING' ? 800 : 3000;

            const nextBlink = minTime + Math.random() * varTime;
            timeout = setTimeout(() => {
                setBlink(true);
                setTimeout(() => setBlink(false), 150);
                blinkLoop();
            }, nextBlink);
        };
        blinkLoop();
        return () => clearTimeout(timeout);
    }, [samState]);

    // ---------------- ANIMATION FRAME ----------------
    useFrame((state, _delta) => {
        if (!group.current) return;

        const time = state.clock.elapsedTime;

        // 1. Mouse Tracking (Smooth Look) - RESTORED
        const { x, y } = state.pointer;
        group.current.rotation.y = THREE.MathUtils.lerp(group.current.rotation.y, x * 0.5, 0.1);
        group.current.rotation.x = THREE.MathUtils.lerp(group.current.rotation.x, -y * 0.5, 0.1);

        // 2. Idle Breathing (Scale: 1 -> 1.02 -> 1, Duration: 6-8s)
        // Cycle ~7s => ~0.9 rad/s
        const breathingCycle = (Math.sin(time * 0.9) * 0.5 + 0.5); // 0 to 1
        const breathingScale = 1.0 + breathingCycle * 0.02; // 1.0 to 1.02

        // 3. Audio Reactive Pulsing + Breathing
        const currentAudioLevel = useStore.getState().audioLevel || 0;
        const pulse = currentAudioLevel * 0.2;
        const targetScale = breathingScale + pulse;

        group.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.2);

        // 4. Sub-pixel Vertical Drift
        // "Sub-pixel" implies very small movement.
        const drift = Math.sin(time * 0.5) * 0.015;
        group.current.position.y = drift;

        // 5. Material Updates & Soft Emissive Pulse
        if (materialRef.current) {
            // Dynamic chromatic aberration
            const targetAberration = 1.5 + currentAudioLevel * 2.0;
            materialRef.current.chromaticAberration = THREE.MathUtils.lerp(materialRef.current.chromaticAberration, targetAberration, 0.1);

            // Dynamic distortion
            materialRef.current.distortion = THREE.MathUtils.lerp(materialRef.current.distortion, visualState.distortion, 0.1);

            // Dynamic Color
            materialRef.current.color = new THREE.Color(visualState.color);
            // materialRef.current.attenuationColor = new THREE.Color(visualState.color);

            // Soft Emissive Pulse
            // If SPEAKING, boost it significantly based on audio
            let targetEmissiveIntensity = 0.2 + (breathingCycle * 0.3); // Default IDLE

            if (samState === 'SPEAKING') {
                // User requested removing "white glowing background"
                // Keeping it subtle, barely higher than idle, or just rely on pulse rings.
                targetEmissiveIntensity = 0.15 + currentAudioLevel * 0.25; // Much lower boost
            }

            materialRef.current.emissiveIntensity = THREE.MathUtils.lerp(materialRef.current.emissiveIntensity, targetEmissiveIntensity, 0.1);

            // Optional: "Slight rotation or gradient drift"
            // We can rotate the group faster when speaking
            if (samState === 'SPEAKING') {
                group.current.rotation.y += 0.01;
            }
        }
    });

    return (
        <group>
            {/* Environment is key for reflections on the bubble */}
            <Environment preset="city" />

            {/* COLORED LIGHTS - Matching User Snippet Intensities (200/100) */}
            {/* Warm light from top-left */}
            <spotLight
                position={[10, 10, 10]}
                angle={0.15}
                penumbra={1}
                intensity={80} // HIGH INTENSITY
                color={visualState.lightColor} // Reacts to state
                castShadow
            />

            {/* Cool light from bottom-right */}
            <pointLight
                position={[-10, -10, -10]}
                intensity={40} // HIGH INTENSITY
                color={samState === 'SPEAKING' ? '#9fd418ff' : '#aa00ff'} // Gold when speaking, else purple backing
            />

            {/* General Fill */}
            <ambientLight intensity={0.5} />

            <Float
                speed={visualState.speed}
                rotationIntensity={0.5} // RESTORED GENTLE FLOAT
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
                            resolution={1024} // High res
                            transmission={1}
                            roughness={0.1}
                            clearcoat={1}
                            clearcoatRoughness={0.1}
                            thickness={1.2}
                            ior={1.5}
                            chromaticAberration={1.5} // High default rainbow effect
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
                    {/* Positioned slightly in front of the sphere surface */}
                    <group position={[0, 0, 0.9]}>
                        {/* Left Eye */}
                        <Eye
                            position={[-0.3, 0.05, 0]}
                            blink={blink}
                            scale={visualState.eyeScale}
                            color={samState === 'LISTENING' ? '#00ccff' : 'white'}
                        />
                        {/* Right Eye */}
                        <Eye
                            position={[0.3, 0.05, 0]}
                            blink={blink}
                            scale={visualState.eyeScale}
                            color={samState === 'LISTENING' ? '#00ccff' : 'white'}
                        />
                    </group>

                    {/* SPEAKING PULSE - INSIDE GROUP FOR CENTERING */}
                    {samState === 'SPEAKING' && (
                        <group position={[0, 0, 0]}>
                            <SpeakingPulse />
                        </group>
                    )}
                </group>
            </Float>

            {/* LISTENING WAVE - Supports SAM */}
            {samState === 'LISTENING' && (
                <group position={[0, -1.4, 0]} scale={[1, 1, 1]}>
                    <BarWave />
                </group>
            )}


        </group>
    );
});
