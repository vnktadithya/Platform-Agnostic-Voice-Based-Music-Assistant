import { useEffect } from 'react';

import { AnimatePresence } from 'framer-motion';
import { useStore } from '../store/useStore';

import { Canvas } from '@react-three/fiber';
import { CosmicBackground } from '../components/canvas/CosmicBackground';
import { SamCore } from '../components/canvas/SamCore';
import { GhostMessage } from '../components/overlay/GhostMessage';
import { DeviceWarning } from '../components/overlay/DeviceWarning';
import { NowPlayingWidget } from '../components/overlay/NowPlayingWidget';

import { PLATFORM_THEME } from '../constants/theme';
import { InputArea } from '../components/overlay/InputArea';
import { PlatformVisuals } from '../components/overlay/PlatformVisuals';
import { useChatController } from '../hooks/useChatController';
import { usePlatformStatus } from '../hooks/usePlatformStatus';
import { PlatformButton } from '../components/overlay/PlatformButton';
import { CapabilitiesButton } from '../components/overlay/CapabilitiesButton';
import { ConnectionStatus } from '../components/overlay/ConnectionStatus';
import { SoundCloudWidget } from '../components/overlay/SoundCloudWidget';

import styles from '../components/overlay/Overlay.module.css';

export const ChatOverlay = () => {
    const { samState, activePlatform, setActivePlatform, setAccountId, setIntroSeen } = useStore();


    // Theme lookup
    const theme = PLATFORM_THEME[activePlatform];

    const {
        inputText, setInputText,
        nowPlaying, showWidget,
        scTrackUrl, setScTrackUrl,
        ghostMsg, inputMode, setInputMode,
        onTextSubmit, handleInteractionStart,
        analyzeAudioElement
    } = useChatController();

    // Custom Hooks
    const { showDeviceWarning } = usePlatformStatus(analyzeAudioElement);

    // Auth Persistence
    useEffect(() => {
        const search = window.location.search;
        const params = new URLSearchParams(search);
        const platform = params.get('platform');
        const accId = params.get('account_id');

        if (platform && accId) {
            console.log(`Initialized Session: ${platform} (Account: ${accId})`);
            setActivePlatform(platform);
            setAccountId(parseInt(accId, 10));
            window.history.replaceState({}, '', '/chat');
        }
    }, [setActivePlatform, setAccountId]);



    // Ensure intro is marked as seen when arriving at Chat (handles Auth redirects)
    useEffect(() => {
        setIntroSeen(true);
    }, []);

    return (
        <div className={styles.root}>

            {/* 1. Immersive Canvas Layer */}
            <div className={styles.canvasLayer}>
                <Canvas camera={{ position: [0, 0, 8], fov: 45 }} dpr={[1, 2]}>
                    <color attach="background" args={['#020205']} />
                    <CosmicBackground platformColor={theme?.color} />
                    <ambientLight intensity={0.5} />
                    <pointLight position={[10, 10, 10]} intensity={1} />
                    <group position={[0, 1, 0]}>
                        <SamCore />
                    </group>
                </Canvas>
            </div>

            {/* 2. UI Overlay */}
            <div className={styles.uiLayer}>

                {/* Change Platform Button (Top Left) */}
                <PlatformButton />

                {/* View Capabilities Button (Bottom Right) - SPECIAL */}
                {/* View Capabilities Button (Bottom Right) - PREMIUM 3D DESIGN */}
                <CapabilitiesButton activePlatform={activePlatform} theme={theme} />

                <PlatformVisuals activePlatform={activePlatform} />

                <DeviceWarning show={showDeviceWarning} />

                <ConnectionStatus activePlatform={activePlatform} theme={theme} />

                <AnimatePresence>
                    {ghostMsg && <GhostMessage message={ghostMsg} />}
                </AnimatePresence>

                <AnimatePresence>
                    {showWidget && nowPlaying && <NowPlayingWidget data={nowPlaying} />}
                </AnimatePresence>



                <InputArea
                    samState={samState}
                    inputMode={inputMode}
                    setInputMode={setInputMode}
                    inputText={inputText}
                    setInputText={setInputText}
                    onMicClick={handleInteractionStart}
                    onTextSubmit={onTextSubmit}
                />

                {activePlatform === 'soundcloud' && scTrackUrl && (
                    <SoundCloudWidget trackUrl={scTrackUrl} onClose={() => setScTrackUrl(null)} />
                )}
            </div>
        </div>
    );
};
