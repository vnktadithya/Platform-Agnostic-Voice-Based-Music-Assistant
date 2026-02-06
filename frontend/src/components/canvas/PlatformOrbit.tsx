import { useRef, useState, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Decal, useTexture, Html } from '@react-three/drei';
import * as THREE from 'three';
import { getAuthUrl, getPlatformStatus, API_URL } from '../../services/api';

import { NeonStream } from './NeonStream';

// Map logos to the ones we have in public/logos/
export const PLATFORMS = [
    { id: 'spotify', name: 'Spotify', color: '#1DB954', position: [2.5, 1.8, 0], logo: '/logos/spotify.png' },
    { id: 'applemusic', name: 'Apple Music', color: '#FA243C', position: [-2.5, 1.8, 0], logo: '/logos/applemusic.png' },
    { id: 'youtubemusic', name: 'YouTube Music', color: '#FF0000', position: [1.8, -1.5, 1], logo: '/logos/youtubemusic.png' },
    { id: 'amazonmusic', name: 'Amazon Music', color: '#25D1DA', position: [-1.8, -1.5, 1], logo: '/logos/amazonmusic.png' },
    { id: 'soundcloud', name: 'SoundCloud', color: '#ff5500', position: [2.5, 0, -2], logo: '/logos/soundcloud.png' },
    { id: 'deezer', name: 'Deezer', color: '#FF0092', position: [-2.5, 0, -2], logo: '/logos/deezer.png' },
];

// Preload all textures
PLATFORMS.forEach(platform => {
    useTexture.preload(platform.logo);
});

const DNAHelix = ({ start, end, color, onConnected }: { start: [number, number, number], end: [number, number, number], color: string, onConnected?: () => void }) => {
    const count = 60; // Denser helix
    const radius = 0.12;
    const turns = 3;

    // Refs for particles, rungs, and flowing sparkles
    const particlesRef = useRef<THREE.InstancedMesh>(null!);
    const rungsRef = useRef<THREE.InstancedMesh>(null!);
    const sparklesRef = useRef<THREE.InstancedMesh>(null!);
    const dummy = useMemo(() => new THREE.Object3D(), []);

    // Growth State
    const growthRef = useRef(0);
    const connectedRef = useRef(false);

    // Calculate alignment (Local Space)
    const { length, quaternion } = useMemo(() => {
        const startVec = new THREE.Vector3(...start);
        const endVec = new THREE.Vector3(...end);
        const direction = new THREE.Vector3().subVectors(endVec, startVec);
        const len = direction.length();

        const dir = direction.normalize();
        const quat = new THREE.Quaternion();
        quat.setFromUnitVectors(new THREE.Vector3(0, 0, 1), dir);

        return { length: len, quaternion: quat };
    }, [start, end]);

    useFrame((_state, delta) => {
        if (!particlesRef.current || !rungsRef.current || !sparklesRef.current) return;
        const time = _state.clock.elapsedTime;

        // --- GROWTH ANIMATION LOGIC ---
        // Grow from 0 to 1 over approx 1.5 seconds
        if (growthRef.current < 1) {
            growthRef.current += delta * 0.6; // Speed control
            if (growthRef.current > 1) growthRef.current = 1;
        } else if (!connectedRef.current && onConnected && growthRef.current >= 1) {
            connectedRef.current = true;
            onConnected();
        }

        const growth = growthRef.current;

        // Iterate particles
        for (let i = 0; i < count; i++) {
            // tBase is the static index 0..1
            let tBase = i / count;

            // Flowing effect: shift t by time (Slower speed)
            // We calculate t FIRST, because visibility depends on physical position
            let t = (tBase - time * 0.08) % 1;
            if (t < 0) t += 1;

            // Check visibility based on growth
            // Growth flows FROM Platform (1) TO SAM (0)
            // So visible range is [1 - growth, 1] applied to the dynamic t
            if (t < (1 - growth)) {
                // Invisible section (set scale to 0)
                dummy.position.set(0, 0, 0); // Hide off
                dummy.scale.set(0, 0, 0);
                dummy.updateMatrix();
                particlesRef.current.setMatrixAt(i, dummy.matrix);
                particlesRef.current.setMatrixAt(i + count, dummy.matrix);
                rungsRef.current.setMatrixAt(i, dummy.matrix);
                sparklesRef.current.setMatrixAt(i * 2, dummy.matrix);
                sparklesRef.current.setMatrixAt(i * 2 + 1, dummy.matrix);
                continue;
            }



            // Fading at ends (scale)
            const scaleFactor = Math.sin(t * Math.PI); // 0 at ends, 1 in middle

            const angle = t * Math.PI * 2 * turns; // Rotation based on position
            const z = t * length;

            // --- MAIN HELIX PARTICLES ---
            // Strand 1
            const x1 = Math.cos(angle) * radius;
            const y1 = Math.sin(angle) * radius;
            dummy.position.set(x1, y1, z);
            dummy.rotation.set(0, 0, 0);
            dummy.scale.setScalar(0.015 * scaleFactor);
            dummy.updateMatrix();
            particlesRef.current.setMatrixAt(i, dummy.matrix);

            // Strand 2
            const x2 = Math.cos(angle + Math.PI) * radius;
            const y2 = Math.sin(angle + Math.PI) * radius;
            dummy.position.set(x2, y2, z);
            dummy.scale.setScalar(0.015 * scaleFactor);
            dummy.updateMatrix();
            particlesRef.current.setMatrixAt(i + count, dummy.matrix);

            // --- RUNGS (LINES) ---
            dummy.position.set(0, 0, z);
            dummy.rotation.set(0, 0, angle + Math.PI / 2);
            dummy.scale.set(0.02 * scaleFactor, radius * 2 * scaleFactor, 0.02 * scaleFactor);
            dummy.updateMatrix();
            rungsRef.current.setMatrixAt(i, dummy.matrix);

            // --- FLOWING SPARKLES (Aura) ---
            // Particles that drift away from the center
            for (let j = 0; j < 2; j++) {
                const sIdx = i * 2 + j;
                // Independent phase for drifting
                let driftT = (t + j * 0.5 + time * 0.2) % 1;

                const driftRadius = radius * (1.2 + driftT * 3); // Drift outwards significantly
                const driftAngle = angle + j * Math.PI + driftT * Math.PI; // Spiral out

                const sx = Math.cos(driftAngle) * driftRadius;
                const sy = Math.sin(driftAngle) * driftRadius;

                dummy.position.set(sx, sy, z);
                dummy.rotation.set(0, 0, 0);
                // Scale fades as it moves out
                dummy.scale.setScalar(0.01 * (1 - driftT) * scaleFactor);
                dummy.updateMatrix();
                sparklesRef.current.setMatrixAt(sIdx, dummy.matrix);
            }
        }
        particlesRef.current.instanceMatrix.needsUpdate = true;
        rungsRef.current.instanceMatrix.needsUpdate = true;
        sparklesRef.current.instanceMatrix.needsUpdate = true;
    });

    return (
        <group position={start} quaternion={quaternion}>
            {/* Particles (Strands) */}
            <instancedMesh ref={particlesRef} args={[undefined, undefined, count * 2]}>
                <sphereGeometry args={[1, 8, 8]} />
                <meshBasicMaterial
                    color={color}
                    toneMapped={false}
                    transparent
                    opacity={1.0}
                    blending={THREE.AdditiveBlending}
                />
            </instancedMesh>

            {/* Rungs (Ladder lines) */}
            <instancedMesh ref={rungsRef} args={[undefined, undefined, count]}>
                <cylinderGeometry args={[1, 1, 1, 4]} />
                <meshBasicMaterial
                    color={color}
                    toneMapped={false}
                    transparent
                    opacity={0.5}
                    blending={THREE.AdditiveBlending}
                />
            </instancedMesh>

            {/* Sparkles (Flowing Away) */}
            <instancedMesh ref={sparklesRef} args={[undefined, undefined, count * 2]}>
                <sphereGeometry args={[0.8, 8, 8]} />
                <meshBasicMaterial
                    color={color}
                    toneMapped={false}
                    transparent
                    opacity={0.6}
                    blending={THREE.AdditiveBlending}
                />
            </instancedMesh>
        </group>
    );
};



const ConnectionLine = ({
    start,
    end,
    color,
    active,
    onConnected
}: {
    start: [number, number, number],
    end: [number, number, number],
    color: string,
    active: boolean,
    onConnected?: () => void
}) => {
    // If active (clicked), show the DNA Helix logic
    if (active) {
        return <DNAHelix start={start} end={end} color={color} onConnected={onConnected} />;
    }

    // Otherwise show the new NEON STREAM
    return <NeonStream
        start={start}
        end={end}
        color={color}
    />;
};

const PlatformNode = ({ platform, onSelect, onHover, onHoverPos }: { platform: any, onSelect: (id: string) => void, onHover: (color: string | null) => void, onHoverPos: (pos: [number, number, number] | null) => void }) => {
    const meshRef = useRef<THREE.Mesh>(null!);
    const ringRef = useRef<THREE.Mesh>(null!);
    const [hovered, setHovered] = useState(false);

    // Load logo texture
    const texture = useTexture(platform.logo) as THREE.Texture;

    useFrame((state) => {
        if (!meshRef.current) return;

        // Orbit visuals
        const time = state.clock.elapsedTime;

        // Gentle rotation of the sphere itself
        meshRef.current.rotation.y = time * 0.5;

        // Bobbing motion
        meshRef.current.position.y = Math.sin(time + platform.position[0]) * 0.1;

        // Ring rotation
        if (ringRef.current) {
            ringRef.current.rotation.x = Math.PI / 2 + Math.sin(time * 0.5) * 0.2;
            ringRef.current.rotation.y = time * 0.2;
        }

        // Hover scale effect
        const targetScale = hovered ? 1.2 : 1;
        meshRef.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.1);
    });

    return (
        <group position={new THREE.Vector3(...platform.position)}>

            {/* Main Platform Sphere */}
            <mesh
                ref={meshRef}
                onClick={() => onSelect(platform.id)}
                onPointerOver={(e) => {
                    e.stopPropagation(); // Prevent bubbling
                    setHovered(true);
                    onHover(platform.color);
                    onHoverPos([e.point.x, e.point.y, e.point.z]);
                }}
                onPointerOut={(_e) => {
                    setHovered(false);
                    onHover(null);
                    onHoverPos(null);
                }}
            >
                <sphereGeometry args={[0.35, 32, 32]} />
                <meshStandardMaterial
                    color={platform.color}
                    roughness={0.2}
                    metalness={0.7}
                    emissive={platform.color}
                    emissiveIntensity={hovered ? 0.6 : 0.2}
                />

                {/* Logo Decal */}
                <Decal
                    position={[0, 0, 0.35]}
                    rotation={[0, 0, 0]}
                    scale={[0.45, 0.45, 0.45]}
                    map={texture}
                    depthTest={true}
                />
                <Decal
                    position={[0, 0, -0.35]}
                    rotation={[0, Math.PI, 0]}
                    scale={[0.45, 0.45, 0.45]}
                    map={texture}
                    depthTest={true}
                />
            </mesh>

            {/* Holographic Ring */}
            <mesh ref={ringRef}>
                <torusGeometry args={[0.55, 0.015, 16, 64]} />
                <meshBasicMaterial color={platform.color} transparent opacity={0.4} side={THREE.DoubleSide} />
            </mesh>

            {/* Label on Hover */}
            {hovered && (
                <Html position={[0, -1, 0]} center distanceFactor={10} style={{ pointerEvents: 'none' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                        <div style={{
                            background: 'rgba(0,0,0,0.8)',
                            padding: '4px 12px',
                            borderRadius: '12px',
                            border: `1px solid ${platform.color}`,
                            color: 'white',
                            fontSize: '0.8rem',
                            whiteSpace: 'nowrap',
                            fontWeight: 'bold',
                            backdropFilter: 'blur(4px)',
                            boxShadow: `0 0 10px ${platform.color}, 0 0 1px ${platform.color}`
                        }}>
                            {platform.name}
                        </div>
                        {platform.id !== 'spotify' && platform.id !== 'soundcloud' && (
                            <div style={{
                                color: 'rgba(255, 255, 255, 0.6)',
                                fontSize: '0.6rem',
                                marginTop: '4px',
                                textShadow: '0 1px 2px rgba(0,0,0,0.8)',
                                whiteSpace: 'nowrap'
                            }}>
                                Coming Soon
                            </div>
                        )}
                    </div>
                </Html>
            )}
        </group>
    );
};

interface PlatformOrbitProps {
    connecting: string | null;
    setConnecting: (platform: string | null) => void;
    setHoveredColor: (color: string | null) => void;
    setHoveredPos: (pos: [number, number, number] | null) => void;
    activeLookingId?: string | null;
}

export const PlatformOrbit = ({ connecting, setConnecting, setHoveredColor, setHoveredPos, activeLookingId }: PlatformOrbitProps) => {
    const groupRef = useRef<THREE.Group>(null!);

    // Store the pending network request
    const prefetchRef = useRef<Promise<string | void> | null>(null);

    useFrame((state, _delta) => {
        if (groupRef.current) {
            // Rotate the entire platform group around the Y axis
            // Use absolute time for deterministic sync with SAM
            const time = state.clock.elapsedTime;
            groupRef.current.rotation.y = time * 0.2;
        }
    });

    const handleSelect = (platformId: string, platformName: string) => {
        if (platformId !== 'spotify' && platformId !== 'soundcloud') return;

        // 1. Trigger Animation
        setConnecting(platformName);

        // 2. Start Network Request IMMEDIATELY (Prefetch)
        const prefetch = async () => {
            try {
                // Check status first
                const status = await getPlatformStatus(platformId);
                if (status && status.is_connected && status.account_id && status.user_id) {
                    return `http://localhost:5173/chat?platform=${platformId}&account_id=${status.account_id}&user_id=${status.user_id}&has_device=${status.has_active_device}`;
                }
            } catch (e) {
                console.warn("Status check failed, proceeding to login flow", e);
            }

            if (platformId === 'soundcloud') {
                return `${API_URL}/adapter/soundcloud/login`;
            }

            return await getAuthUrl(platformId);
        };

        prefetchRef.current = prefetch();
    };

    const handleConnectionComplete = async () => {
        // 3. Wait for BOTH animation (this function call) AND network (stored promise)
        if (prefetchRef.current) {
            try {
                const url = await prefetchRef.current;
                if (url) window.location.href = url;
            } catch (e) {
                console.error("Prefetch failed", e);
            }
        }
    };

    return (
        <group>
            <group ref={groupRef}>
                {/* Render Nodes */}
                {PLATFORMS.map((p) => (
                    <PlatformNode
                        key={p.id}
                        platform={p}
                        onSelect={(id) => handleSelect(id, p.name)}
                        onHover={setHoveredColor}
                        onHoverPos={setHoveredPos}
                    />
                ))}

                {/* Render Connections */}
                {PLATFORMS.map((p) => {

                    const isLookingAt = activeLookingId === p.id;
                    const isConnecting = connecting === p.name; // 'connecting' uses p.name in original code, not p.id

                    if (!isLookingAt && !isConnecting) return null;

                    return (
                        <ConnectionLine
                            key={`line-${p.id}`}
                            start={[0, 0, 0]}
                            end={p.position as [number, number, number]}
                            color={p.color}
                            active={isConnecting} // This triggers "DNA Helix" mode
                            onConnected={() => handleConnectionComplete()}
                        />
                    );
                })}
            </group>
        </group>
    );
};

