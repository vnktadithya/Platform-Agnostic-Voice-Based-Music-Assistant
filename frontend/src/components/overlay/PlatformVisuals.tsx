import { AnimatePresence, motion } from 'framer-motion';
import { Canvas } from '@react-three/fiber';
import { SpotifyModel } from '../canvas/SpotifyModel';
import { SoundCloudModel } from '../canvas/SoundCloudModel';
import styles from './Overlay.module.css';

interface PlatformVisualsProps {
    activePlatform: string;
}

export const PlatformVisuals: React.FC<PlatformVisualsProps> = ({ activePlatform }) => {
    return (
        <>
            <AnimatePresence>
                {activePlatform === 'spotify' && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 20 }}
                        transition={{ duration: 0.8 }}
                        className={styles.platformVisualsContainer}
                    >
                        <Canvas camera={{ position: [0, 0, 6], fov: 45 }} gl={{ alpha: true }}>
                            <ambientLight intensity={1.5} />
                            <pointLight position={[2, 2, 5]} intensity={2} color="#1DB954" />
                            <group position={[0.2, -0.2, 0]}>
                                <SpotifyModel />
                            </group>
                        </Canvas>
                    </motion.div>
                )}
            </AnimatePresence>

            <AnimatePresence>
                {activePlatform === 'soundcloud' && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 20 }}
                        transition={{ duration: 0.8 }}
                        className={`${styles.platformVisualsContainer} ${styles.platformVisualsContainerLarge}`}
                    >
                        <Canvas camera={{ position: [0, 0, 6], fov: 45 }} gl={{ alpha: true }}>
                            <ambientLight intensity={1.5} />
                            <pointLight position={[2, 2, 5]} intensity={2} color="#FF5500" />
                            <group position={[0.2, -0.2, 0]}>
                                <SoundCloudModel />
                            </group>
                        </Canvas>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
};
