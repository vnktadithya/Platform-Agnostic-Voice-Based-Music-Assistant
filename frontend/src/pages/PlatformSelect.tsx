import { Canvas } from '@react-three/fiber';
import { motion, AnimatePresence } from 'framer-motion';
import { useRef, useEffect, useState, Suspense } from 'react';
import { useLocation } from 'wouter';
import { SamPlatformBehavior } from '../components/canvas/SamPlatformBehavior';
import { PlatformOrbit, PLATFORMS } from '../components/canvas/PlatformOrbit';
import { HeroParticles } from '../components/canvas/HeroParticles';
import { AccessDeniedWidget } from '../components/AccessDeniedWidget';
import styles from './PlatformSelect.module.css';

// Fallback for loading 3D assets
const Loader = () => (
    <div className={styles.loader}>
        LOADING...
    </div>
);

const PlatformSelect = () => {
    const [, setLocation] = useLocation();
    const [connecting, setConnecting] = useState<string | null>(null);
    const [hoveredColor, setHoveredColor] = useState<string | null>(null);
    const [hoveredPos, setHoveredPos] = useState<[number, number, number] | null>(null);
    const [sessionExpired, setSessionExpired] = useState(false);
    const [accessDenied, setAccessDenied] = useState(false);

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        if (params.get('expired')) {
            setSessionExpired(true);
            window.history.replaceState({}, '', '/platform-select');
        }
        if (params.get('error') === 'access_denied') {
            setAccessDenied(true);
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
        <div className={styles.container}>
            {/* 3D SCENE */}
            <div className={styles.sceneContainer}>
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
            <div className={styles.uiOverlay}>
                {/* Back to Home Button (Top Left) */}
                <motion.button
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                    onClick={() => setLocation('/')}
                    className={styles.backButton}
                // Hover styles moved to CSS :hover
                >
                    Back to Home
                </motion.button>

                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 1 }}
                    className={styles.headerContainer}
                >
                    <h1 className={styles.title}>
                        One Intelligence. Every Music World.
                    </h1>
                    <p className={styles.subtitle}>
                        SAM connects seamlessly to your favorite platform — your music stays unified, wherever it lives.
                    </p>
                </motion.div>

                {/* Connecting HUD - Fixed Bottom Right */}
                {connecting && (
                    <div className={styles.connectingHud}>
                        <div className={styles.hudLabel}>{`Binding intelligence to`}</div>
                        <div className={styles.hudValue}>{`${connecting}...`}</div>
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
                            className={styles.sessionExpiredToast}
                        >
                            <div className={styles.sessionExpiredBar} />
                            <div className={styles.sessionExpiredContent}>
                                <span className={styles.sessionExpiredTitle}>
                                    SESSION EXPIRED
                                </span>
                                <span className={styles.sessionExpiredMessage}>
                                    Please Re-Login.
                                </span>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Access Denied Widget */}
            <AccessDeniedWidget isOpen={accessDenied} onClose={() => setAccessDenied(false)} />

            {/* Loading Overlay */}
            <Suspense fallback={<Loader />}>
                <></>
            </Suspense>
        </div>
    );
};

export default PlatformSelect;
