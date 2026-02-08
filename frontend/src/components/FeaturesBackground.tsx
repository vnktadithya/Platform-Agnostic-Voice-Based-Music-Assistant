import { Canvas } from '@react-three/fiber';
import { Suspense } from 'react';
import { HeroParticles } from './canvas/HeroParticles';
import styles from './Features.module.css';

// This component isolates the heavy 3D canvas and its dependencies (Three.js stuff)
// so it can be lazy loaded separately from the main Features page content.
const FeaturesBackground = () => {
    return (
        <div className={styles.backgroundContainer}>
            {/* Inline zIndex preserved just in case, though handled in CSS too */}
            <Canvas camera={{ position: [0, 0, 10], fov: 45 }}>
                <Suspense fallback={null}>
                    <color attach="background" args={['#050505']} />
                    <HeroParticles />
                </Suspense>
            </Canvas>
        </div>
    );
};

export default FeaturesBackground;
