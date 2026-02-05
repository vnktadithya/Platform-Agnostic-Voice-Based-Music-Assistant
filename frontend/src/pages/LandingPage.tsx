import { ImageSequence } from '../components/ImageSequence';
import { LandingOverlay } from '../components/landing/LandingOverlay';
import { useStore } from '../store/useStore';


import { useState } from 'react';

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
        <main style={{
            backgroundColor: '#050505',
            color: 'white',
            minHeight: '100vh',
            fontFamily: '"SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif'
        }}>
            {/* SECTION 1: HERO (Cinematic Loop) */}
            <section style={{ position: 'relative', height: '100vh', width: '100%', overflow: 'hidden' }}>
                <ImageSequence onCycleComplete={handleCycleComplete} instantStart={introSeen} />
                <LandingOverlay showButton={showButton} />
            </section>
        </main>
    );
};


