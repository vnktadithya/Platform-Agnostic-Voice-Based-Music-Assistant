import { useRef } from 'react';
import { useStore } from '../store/useStore';
import { useSoundCloud } from './useSoundCloud';
import { executeAction } from '../services/api';

export const useAudioController = (scTrackUrl: string | null) => {
    const { activePlatform, accountId } = useStore();
    const { setVolume: setScVolume, getVolume: getScVolume } = useSoundCloud(activePlatform, scTrackUrl);

    const preDuckVolume = useRef<number | null>(null);

    const duckAudio = async () => {
        console.log("Ducking Audio...");
        try {
            if (activePlatform === 'spotify' && accountId) {
                // Fetch current volume BEFORE ducking
                try {
                    const result = await executeAction({ type: 'get_volume', params: {} }, 'spotify', accountId);
                    if (result && result.result !== undefined) {
                        const currentVol = Number(result.result);
                        if (!isNaN(currentVol)) {
                            preDuckVolume.current = currentVol;
                            console.log("Saved Pre-Duck Volume:", currentVol);
                        }
                    }
                } catch (err) {
                    console.warn("Failed to fetch volume before ducking", err);
                }

                executeAction({ type: 'set_volume', params: { volume: 40 } }, 'spotify', accountId);
                await new Promise(r => setTimeout(r, 100)); // Small delay for effect
            } else if (activePlatform === 'soundcloud') {
                // Fetch current volume before ducking
                const currentVol = await getScVolume();
                preDuckVolume.current = currentVol;
                console.log("Saved SC Pre-Duck Volume:", currentVol);
                setScVolume(0); // Duck to 0% (Mute) to prevent STT interference
            }
        } catch (e) {
            console.warn("Ducking failed", e);
        }
    };

    const unduckAudio = async () => {
        console.log("Unducking Audio...");
        try {
            if (activePlatform === 'spotify' && accountId) {
                const restoreVol = preDuckVolume.current !== null ? preDuckVolume.current : 80;
                console.log("Restoring Volume To:", restoreVol);
                executeAction({ type: 'set_volume', params: { volume: restoreVol } }, 'spotify', accountId);
                preDuckVolume.current = null; // Reset
            } else if (activePlatform === 'soundcloud') {
                const restoreVol = preDuckVolume.current !== null ? preDuckVolume.current : 100;
                setScVolume(restoreVol);
            }
        } catch (e) {
            console.warn("Unducking failed", e);
        }
    };

    return { duckAudio, unduckAudio };
};
