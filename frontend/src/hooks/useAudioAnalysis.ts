import { useRef, useCallback } from 'react';
import { useStore } from '../store/useStore';

export const useAudioAnalysis = () => {
    const { setAudioLevel } = useStore();
    const audioContextRef = useRef<AudioContext | null>(null);
    const audioStreamRef = useRef<MediaStream | null>(null);
    const analysisFrameRef = useRef<number | null>(null);

    const startMicAnalysis = useCallback(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            audioStreamRef.current = stream;

            const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
            const audioContext = new AudioContextClass();
            audioContextRef.current = audioContext;

            const source = audioContext.createMediaStreamSource(stream);
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 256;
            source.connect(analyser);

            const dataArray = new Uint8Array(analyser.frequencyBinCount);

            const updateAnalysis = () => {
                analyser.getByteFrequencyData(dataArray);
                let sum = 0;
                for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
                const average = sum / dataArray.length;
                const normalizedVolume = Math.min(1, average / 128);

                setAudioLevel(normalizedVolume);
                analysisFrameRef.current = requestAnimationFrame(updateAnalysis);
            };
            updateAnalysis();

        } catch (err) {
            console.error("Audio analysis failed:", err);
            const interval = window.setInterval(() => setAudioLevel(Math.random() * 0.5 + 0.2), 100);
            window.audioInterval = interval;
        }
    }, [setAudioLevel]);

    const stopMicAnalysis = useCallback(() => {
        if (analysisFrameRef.current) cancelAnimationFrame(analysisFrameRef.current);
        if (audioContextRef.current) audioContextRef.current.close();
        if (audioStreamRef.current) audioStreamRef.current.getTracks().forEach(t => t.stop());
        if (window.audioInterval) clearInterval(window.audioInterval);
        setAudioLevel(0);
    }, [setAudioLevel]);

    const analyzeAudioElement = useCallback((audio: HTMLAudioElement) => {
        try {
            const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
            const audioContext = new AudioContextClass();

            const source = audioContext.createMediaElementSource(audio);
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 256;

            source.connect(analyser);
            analyser.connect(audioContext.destination);

            const dataArray = new Uint8Array(analyser.frequencyBinCount);

            const updateVolume = () => {
                if (audio.paused || audio.ended) return;
                analyser.getByteFrequencyData(dataArray);
                let sum = 0;
                for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
                const avg = sum / dataArray.length;
                setAudioLevel(avg / 128);
                requestAnimationFrame(updateVolume);
            };

            audio.onplay = () => {
                audioContext.resume();
                updateVolume();
            };

            return audioContext;
        } catch (e) {
            console.warn("Analysis failed, playing audio normally", e);
            return null;
        }
    }, [setAudioLevel]);

    return { startMicAnalysis, stopMicAnalysis, analyzeAudioElement };
};
