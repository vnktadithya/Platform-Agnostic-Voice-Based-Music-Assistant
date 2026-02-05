import { useState, useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';
import { useToast } from '../components/ui/Toast';
import { voiceClient } from '../services/VoiceClient';
import { executeAction } from '../services/api';
import { useAudioAnalysis } from './useAudioAnalysis';
import { useChatHandler } from './useChatHandler';
import { useAudioController } from './useAudioController';
import type { BackendResponse, Command } from '../types';

export const useChatController = () => {
    const { samState, setSamState, setAudioLevel, activePlatform, accountId } = useStore();
    const { addToast } = useToast();

    const [inputText, setInputText] = useState('');
    const [ghostMsg, setGhostMsg] = useState<string | null>(null);
    const [inputMode, setInputMode] = useState<'voice' | 'text'>('voice');

    const [nowPlaying, setNowPlaying] = useState<{ title: string, subtitle: string, type: 'song' | 'playlist', image?: string } | null>(null);
    const [showWidget, setShowWidget] = useState(false);
    const [pendingTrackInfo, setPendingTrackInfo] = useState<{ title: string, subtitle: string, type: 'song' | 'playlist', image?: string } | null>(null);
    const [scTrackUrl, setScTrackUrl] = useState<string | null>(null);

    const { startMicAnalysis, stopMicAnalysis, analyzeAudioElement } = useAudioAnalysis();
    const { processText, processVoice, handleBackendResponse, executePendingCommand, setPendingCommand } = useChatHandler();
    const { duckAudio, unduckAudio } = useAudioController(scTrackUrl);

    const prevSamState = useRef(samState);

    // Widget Effect
    useEffect(() => {
        if (prevSamState.current === 'SPEAKING' && samState === 'IDLE') {
            if (pendingTrackInfo) {
                // Optimization: Preload image during the delay so it appears instantly
                if (pendingTrackInfo.image) {
                    const img = new Image();
                    img.src = pendingTrackInfo.image;
                }

                const timer = setTimeout(() => {
                    setNowPlaying(pendingTrackInfo);
                    setShowWidget(true);
                    setPendingTrackInfo(null);
                    setTimeout(() => setShowWidget(false), 4000);
                }, 1500);
                return () => clearTimeout(timer);
            }
        }
        prevSamState.current = samState;
    }, [samState, pendingTrackInfo]);

    useEffect(() => {
        setGhostMsg(null);
    }, [samState]);

    const playResponse = async (base64Audio: string, deferredCommand: Command | null = null) => {
        await duckAudio();
        setSamState('SPEAKING');

        const audio = new Audio(`data:audio/wav;base64,${base64Audio}`);
        const audioContext = analyzeAudioElement(audio);

        const safeExecute = () => {
            if (deferredCommand) {
                executeAction(deferredCommand, activePlatform, accountId || 1).catch(console.error);
                setPendingCommand(null);
            } else {
                executePendingCommand();
            }
        };

        audio.onended = () => {
            setSamState('IDLE');
            setAudioLevel(0);
            if (audioContext) audioContext.close();
            unduckAudio();
            safeExecute();
        };

        audio.play().catch(e => {
            console.error(e);
            setSamState('IDLE');
            unduckAudio();
        });
    };

    const handleResponseAction = (response: BackendResponse | null) => {
        if (!response) return;

        const { trackInfo, command } = handleBackendResponse(response);
        if (trackInfo) setPendingTrackInfo(trackInfo);
        if (trackInfo?.permalink_url && (activePlatform === 'soundcloud' || response.platform === 'soundcloud')) {
            setScTrackUrl(trackInfo.permalink_url);
        }

        if (response.reply) {
            if (response.audio_base64) {
                playResponse(response.audio_base64, command);
            } else {
                setTimeout(() => setSamState('IDLE'), 2000);
            }
        } else {
            setSamState('IDLE');
        }
    };

    const onTextSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const text = inputText;
        setInputText('');
        const response = await processText(text);
        handleResponseAction(response);
    };

    const handleInteractionStart = async () => {
        if (samState === 'IDLE') {
            try {
                setSamState('LISTENING');
                await voiceClient.startRecording();
                startMicAnalysis();
            } catch (e) {
                console.error(e);
                addToast("Microphone access failed.", 'error');
                setSamState('IDLE');
            }
        } else if (samState === 'LISTENING') {
            setSamState('THINKING');
            stopMicAnalysis();
            try {
                const processVoiceResult = await processVoice();
                handleResponseAction(processVoiceResult);
            } catch (e) {
                setSamState('IDLE');
            }
        }
    };

    return {
        inputText,
        setInputText,
        nowPlaying,
        showWidget,
        scTrackUrl,
        setScTrackUrl,
        ghostMsg,
        inputMode,
        setInputMode,
        onTextSubmit,
        handleInteractionStart,
        analyzeAudioElement
    };
};
