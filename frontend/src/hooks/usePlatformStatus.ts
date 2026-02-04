import { useState, useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';
import { getPlatformStatus, synthesizeSpeechStream } from '../services/api';

export const usePlatformStatus = (analyzeAudioElement: (audio: HTMLAudioElement) => AudioContext | null) => {
    const { activePlatform, accountId, setSamState } = useStore();
    const [showDeviceWarning, setShowDeviceWarning] = useState(false);
    const audioRef = useRef<HTMLAudioElement | null>(null);

    useEffect(() => {
        if (activePlatform !== 'spotify' || !accountId) return;

        let isCancelled = false;

        const checkStatus = async () => {
            try {
                // Check URL params for pre-fetched status (Optimization)
                console.log("Checking Platform Status...");
                const params = new URLSearchParams(window.location.search);
                const hasDeviceParam = params.get('has_device');

                let status;

                // If we have the param, trust it initially to speed up UX
                if (hasDeviceParam !== null) {
                    console.log("Using Pre-fetched Status:", hasDeviceParam);
                    status = {
                        is_connected: true,
                        has_active_device: hasDeviceParam === 'true'
                    };
                } else {
                    // Fallback to network fetch if no param
                    status = await getPlatformStatus(activePlatform, accountId);
                }

                console.log("Spotify Status:", status);

                if (isCancelled) return;

                if (status.is_connected && status.has_active_device === false) {
                    console.warn("No active device found. Triggering voice warning.");

                    // Trigger Voice Warning (Direct Stream)
                    try {
                        const audioBlob = await synthesizeSpeechStream("No active Spotify device found. Please open Spotify on any device to continue.");

                        if (isCancelled) return;

                        const audioUrl = URL.createObjectURL(audioBlob);
                        const audio = new Audio(audioUrl);
                        audioRef.current = audio;

                        // Sync: Warning appears exactly when we are ready to play
                        setShowDeviceWarning(true);

                        // Auto-hide warning after 5s if audio fails or hangs
                        const safetyTimer = setTimeout(() => {
                            if (!isCancelled) setShowDeviceWarning(false);
                        }, 5000);

                        setSamState('SPEAKING');

                        // Always attach visualizer to attempt animation
                        const audioContext = analyzeAudioElement(audio);

                        // Attempt to wake up AudioContext (non-blocking)
                        if (audioContext && audioContext.state === 'suspended') {
                            audioContext.resume().catch(e => console.warn("Audio resume failed:", e));
                        }

                        audio.onended = () => {
                            if (!isCancelled) {
                                setSamState('IDLE');
                                setShowDeviceWarning(false);
                            }
                            if (audioContext) audioContext.close();
                            URL.revokeObjectURL(audioUrl);
                            clearTimeout(safetyTimer);
                        };

                        audio.onerror = () => {
                            if (!isCancelled) {
                                setSamState('IDLE');
                                setShowDeviceWarning(false);
                            }
                            URL.revokeObjectURL(audioUrl);
                        };

                        await audio.play();
                    } catch (err) {
                        console.error("TTS Stream Error:", err);
                        if (!isCancelled) {
                            setSamState('IDLE');
                            setShowDeviceWarning(false);
                        }
                    }
                } else {
                    if (!isCancelled) setShowDeviceWarning(false);
                }
            } catch (e) {
                console.error("Failed to check platform status:", e);
            }
        };

        checkStatus();

        return () => {
            isCancelled = true;
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current = null;
            }
            setShowDeviceWarning(false);
            setSamState('IDLE'); // Ensure we don't get stuck in SPEAKING if unmounted
        };
    }, [activePlatform, accountId, setSamState, analyzeAudioElement]);

    return { showDeviceWarning };
};
