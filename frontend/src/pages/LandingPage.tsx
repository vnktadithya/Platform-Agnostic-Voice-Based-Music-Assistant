import { ImageSequence } from '../components/ImageSequence';
import { LandingOverlay } from '../components/landing/LandingOverlay';
import { useStore } from '../store/useStore';


import { useState } from 'react';
import styles from './LandingPage.module.css';

// Module-level variable to track animation state across navigations,
// but reset on full page reload.
export const LandingPage = () => {
    const { introSeen, setIntroSeen } = useStore();
    const [showButton, setShowButton] = useState(introSeen);

    const handleCycleComplete = () => {
        setShowButton(true);
        setIntroSeen(true);
    };

    return (
        <main className={styles.main}>
            {/* SECTION 1: HERO (Cinematic Loop) */}
            <section className={styles.heroSection}>
                <ImageSequence onCycleComplete={handleCycleComplete} instantStart={introSeen} />
                <LandingOverlay showButton={showButton} />
            </section>
        </main>
    );
};


