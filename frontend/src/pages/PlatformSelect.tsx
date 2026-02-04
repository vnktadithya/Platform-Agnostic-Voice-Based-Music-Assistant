import { Canvas } from '@react-three/fiber';
import { motion, AnimatePresence } from 'framer-motion';
import { useRef, useEffect, useState, Suspense } from 'react';
import { useLocation } from 'wouter';
import { SamPlatformBehavior } from '../components/canvas/SamPlatformBehavior';
import { PlatformOrbit, PLATFORMS } from '../components/canvas/PlatformOrbit';
import { HeroParticles } from '../components/canvas/HeroParticles';

// Fallback for loading 3D assets
const Loader = () => (
    <div style={{ color: 'white', position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>
        LOADING...
    </div>
);

const PlatformSelect = () => {
    const [, setLocation] = useLocation();
    const [connecting, setConnecting] = useState<string | null>(null);
    const [hoveredColor, setHoveredColor] = useState<string | null>(null);
    const [hoveredPos, setHoveredPos] = useState<[number, number, number] | null>(null);
    const [sessionExpired, setSessionExpired] = useState(false);

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        if (params.get('expired')) {
            setSessionExpired(true);
            window.history.replaceState({}, '', '/platform-select');
        }
    }, []);

    // Auto-dismiss timer depends on state
    useEffect(() => {
        if (sessionExpired) {
            const timer = setTimeout(() => {
                setSessionExpired(false);
            }, 4000);
            return () => clearTimeout(timer);
        }
    }, [sessionExpired]);

    // Random Looking Logic
    const [lookingAtId, setLookingAtId] = useState<string | null>(null);
    const [lookTarget, setLookTarget] = useState<[number, number, number] | null>(null);

    // Timing config matches NeonStream defaults/overrides
    const BEAM_GROW_TIME = 1000; // 1s
    const BEAM_STAY_TIME = 2000; // 2s
    const BEAM_FADE_TIME = 500;  // 0.5s (Matches NeonStream FADE_OUT_TIME)

    // State for permutation cycle
    const platformQueue = useRef<any[]>([]);
    const lastPlayedId = useRef<string | null>(null);

    // Shuffle helper
    const getShuffledPlatforms = (excludeFirstId: string | null) => {
        // 1. Clone array
        const pool = [...PLATFORMS];

        // 2. Fisher-Yates Shuffle
        for (let i = pool.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [pool[i], pool[j]] = [pool[j], pool[i]];
        }

        // 3. Ensure no repeat across boundary
        // If the first item matches the last played, swap it with the last item
        if (excludeFirstId && pool[0].id === excludeFirstId) {
            // Swap 0 with index 1 (or last)
            [pool[0], pool[pool.length - 1]] = [pool[pool.length - 1], pool[0]];
        }

        return pool;
    };

    useEffect(() => {
        let timeout: any;

        // If user has selected a platform (Connecting...), FORCE SAM to look at it
        if (connecting) {
            const targetPlatform = PLATFORMS.find(p => p.name === connecting);
            if (targetPlatform) {
                setLookingAtId(targetPlatform.id);
                setLookTarget(targetPlatform.position as [number, number, number]);
            }
            return; // Stop the random cycle
        }

        // Otherwise: Random looking cycle
        const cycle = () => {
            // 0. Refill Queue if empty
            if (platformQueue.current.length === 0) {
                platformQueue.current = getShuffledPlatforms(lastPlayedId.current);
            }

            // 1. Pop next platform
            const nextPlatform = platformQueue.current.shift();
            lastPlayedId.current = nextPlatform.id;

            // 2. Look at it
            setLookingAtId(nextPlatform.id);
            setLookTarget(nextPlatform.position as [number, number, number]);

            // 3. Wait for the cycle (Grow + Stay + Fade)
            timeout = setTimeout(() => {
                setLookingAtId(null);
                setLookTarget(null); // Stop looking (Idle)

                // Wait a bit before next one
                timeout = setTimeout(() => {
                    cycle();
                }, 2000); // 1s break between beams (Sam is idle)
            }, BEAM_GROW_TIME + BEAM_STAY_TIME + BEAM_FADE_TIME);
        };

        // Start cycle
        cycle();

        return () => clearTimeout(timeout);
    }, [connecting]);

    return (
        <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            background: 'black',
            overflow: 'hidden'
        }}>
            {/* 3D SCENE */}
            <div style={{ position: 'absolute', width: '100%', height: '100%', zIndex: 1 }}>
                <Canvas camera={{ position: [0, 0, 8], fov: 45 }}>
                    <Suspense fallback={null}>
                        {/* Background */}
                        <color attach="background" args={['#050510']} />
                        <HeroParticles connecting={!!connecting} hoveredColor={hoveredColor} hoveredPos={hoveredPos} />

                        {/* Lighting */}
                        <ambientLight intensity={0.5} />
                        <pointLight position={[10, 10, 10]} intensity={1} />
                        <spotLight position={[-10, 10, 10]} angle={0.3} intensity={0.8} />

                        {/* Central Intelligence */}
                        <group position={[0, -0.8, 0]} scale={0.6}>
                            <SamPlatformBehavior lookAtTarget={lookTarget} />
                        </group>

                        {/* Orbiting Platforms */}
                        <group position={[0, -0.8, 0]} scale={0.85}>
                            <PlatformOrbit
                                connecting={connecting}
                                setConnecting={setConnecting}
                                setHoveredColor={setHoveredColor}
                                setHoveredPos={setHoveredPos}
                                activeLookingId={lookingAtId}
                            />
                        </group>
                    </Suspense>
                </Canvas>
            </div>

            {/* UI OVERLAY */}
            <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                zIndex: 10,
                pointerEvents: 'none', // Allow clicks to pass through to Canvas for 3D interactions
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                paddingTop: '10px'
            }}>
                {/* Back to Home Button (Top Left) */}
                <motion.button
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                    onClick={() => setLocation('/')}
                    style={{
                        position: 'fixed',
                        top: '2rem',
                        left: '2rem',
                        padding: '0.75rem 1.5rem',
                        fontSize: '0.9rem',
                        fontWeight: 500,
                        backgroundColor: 'rgba(255, 255, 255, 0.1)',
                        backdropFilter: 'blur(10px)',
                        color: 'white',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        borderRadius: '9999px',
                        cursor: 'pointer',
                        zIndex: 50,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        pointerEvents: 'auto',
                        transition: 'all 0.2s ease'
                    }}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
                        e.currentTarget.style.transform = 'translateY(-2px)';
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                        e.currentTarget.style.transform = 'translateY(0)';
                    }}
                >
                    Back to Home
                </motion.button>

                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 1 }}
                    style={{ textAlign: 'center' }}
                >
                    <h1 style={{
                        fontSize: '3.5rem',
                        fontWeight: 700,
                        background: 'linear-gradient(to right, #4facfe 0%, #00f2fe 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        marginBottom: '1rem',
                        textShadow: '0 10px 30px rgba(0, 242, 254, 0.3)'
                    }}>
                        One Intelligence. Every Music World.
                    </h1>
                    <p style={{
                        fontSize: '1.1rem',
                        color: 'rgba(255, 255, 255, 0.7)',
                        maxWidth: '800px',
                        margin: '0 auto',
                        lineHeight: '1.6'
                    }}>
                        SAM connects seamlessly to your favorite platform — your music stays unified, wherever it lives.
                    </p>
                </motion.div>

                {/* Connecting HUD - Fixed Bottom Right */}
                {connecting && (
                    <div style={{
                        position: 'absolute',
                        bottom: '40px',
                        right: '40px',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'flex-end',
                        gap: '4px',
                        color: '#00f2fe',
                        fontFamily: "'Courier New', monospace",
                        textShadow: '0 0 10px #00f2fe',
                        fontWeight: 'bold',
                        pointerEvents: 'none'
                    }}>
                        <div style={{ fontSize: '1.2rem' }}>{`Binding intelligence to`}</div>
                        <div style={{ fontSize: '1.4rem' }}>{`${connecting}...`}</div>
                    </div>
                )}

                {/* Session Expired Message - Center Left */}
                <AnimatePresence>
                    {sessionExpired && (
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            transition={{ duration: 0.4, type: "spring" }}
                            style={{
                                position: 'absolute',
                                top: '50%',
                                left: '4%',
                                transform: 'translateY(-50%)',
                                background: 'rgba(255, 59, 48, 0.08)', // Much subtler
                                border: '1px solid rgba(255, 59, 48, 0.15)',
                                backdropFilter: 'blur(8px)',
                                padding: '1rem 1.5rem', // Reduced padding
                                borderRadius: '12px',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.8rem',
                                pointerEvents: 'none' // Don't block clicks
                            }}
                        >
                            <div style={{
                                width: '3px',
                                height: '32px',
                                background: 'rgba(255, 59, 48, 0.8)',
                                borderRadius: '2px',
                                boxShadow: '0 0 10px rgba(255, 59, 48, 0.4)'
                            }} />
                            <div style={{ display: 'flex', flexDirection: 'column' }}>
                                <span style={{
                                    color: 'rgba(255, 59, 48, 0.9)',
                                    fontWeight: '600',
                                    fontSize: '0.95rem',
                                    letterSpacing: '0.5px'
                                }}>
                                    SESSION EXPIRED
                                </span>
                                <span style={{
                                    color: 'rgba(255, 255, 255, 0.6)',
                                    fontSize: '0.8rem'
                                }}>
                                    Please Re-Login.
                                </span>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Loading Overlay */}
            <Suspense fallback={<Loader />}>
                <></>
            </Suspense>
        </div>
    );
};

export default PlatformSelect;
